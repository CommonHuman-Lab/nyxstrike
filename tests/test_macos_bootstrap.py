"""Check Intel build prerequisites before uv, using only mocked shell commands."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MacOSBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nyxstrike-bootstrap-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prefix = self.root / "brew prefix"
        self.log = self.root / "commands.log"
        source = (ROOT / "nyxstrike.sh").read_text(encoding="utf-8")
        library, separator, _ = source.partition("# Argument parsing\n")
        self.assertTrue(separator)
        self.library = self.root / "launcher-library.sh"
        self.library.write_text(library, encoding="utf-8")
        self.env = dict(
            os.environ,
            TEST_BREW_PREFIX=str(self.prefix),
            TEST_COMMAND_LOG=str(self.log),
            NYXSTRIKE_DATA_DIR=str(self.root / "data"),
        )
        self.env.pop("BASH_ENV", None)
        self.env.pop("OPENSSL_DIR", None)

    def run_shell(self, body="sync_python_deps", **environment):
        setup = r'''
source "$1"
uname() {
  if [[ "$1" == -s ]]; then echo "${TEST_OS:-Darwin}";
  else echo "${TEST_ARCH:-x86_64}"; fi
}
xcode-select() { return "${TEST_CLT_STATUS:-0}"; }
rustc() {
  [[ "${TEST_RUST_VERSION:-missing}" != missing ]] || return 127
  echo "rustc $TEST_RUST_VERSION (test)"
}
cargo() { return 0; }
brew() {
  case "$1" in
    --prefix) echo "$TEST_BREW_PREFIX" ;;
    install)
      echo "brew $*" >> "$TEST_COMMAND_LOG"
      [[ "${TEST_BREW_FAIL:-0}" == 0 ]] || return 1
      mkdir -p "$TEST_BREW_PREFIX/opt/openssl@3/include/openssl"
      touch "$TEST_BREW_PREFIX/opt/openssl@3/include/openssl/ssl.h"
      TEST_RUST_VERSION="${TEST_INSTALLED_RUST_VERSION:-1.91.0}"
      ;;
    *) return 1 ;;
  esac
}
ensure_uv_ready() { echo uv-ready >> "$TEST_COMMAND_LOG"; }
uv() { echo "uv $* openssl=${OPENSSL_DIR:-unset}" >> "$TEST_COMMAND_LOG"; }
'''
        return subprocess.run(
            ["/bin/bash", "-c", setup + "\n" + body, "test", str(self.library)],
            cwd=self.root, env={**self.env, **environment},
            capture_output=True, text=True, timeout=10,
        )

    def commands(self):
        return self.log.read_text() if self.log.exists() else ""

    def headers(self, prefix=None):
        directory = (prefix or self.prefix / "opt/openssl@3") / "include/openssl"
        directory.mkdir(parents=True)
        (directory / "ssl.h").touch()

    def test_intel_prepares_compilers_before_dependency_sync(self):
        result = self.run_shell()
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        self.assertIn("brew install openssl@3 rust\n", commands)
        self.assertLess(commands.index("brew install"), commands.index("uv-ready"))
        self.assertIn(f"uv sync --inexact openssl={self.prefix}/opt/openssl@3", commands)

    def test_arm_and_linux_do_not_install_intel_prerequisites(self):
        for system, architecture in (("Darwin", "arm64"), ("Linux", "x86_64")):
            with self.subTest(system=system, architecture=architecture):
                self.log.write_text("")
                result = self.run_shell(TEST_OS=system, TEST_ARCH=architecture)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("brew install", self.commands())
                self.assertIn("uv sync", self.commands())

    def test_ready_intel_does_not_reinstall(self):
        self.headers()
        result = self.run_shell(TEST_RUST_VERSION="1.91.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("brew install", self.commands())

    def test_old_rust_is_upgraded_before_sync(self):
        self.headers()
        for version in ("1.83.0", "1.85.0", "1.87.0", "1.90.0"):
            with self.subTest(version=version):
                self.log.write_text("")
                result = self.run_shell(TEST_RUST_VERSION=version)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("brew install rust\n", self.commands())

    def test_inadequate_rust_after_install_stops_before_uv(self):
        result = self.run_shell(TEST_INSTALLED_RUST_VERSION="1.90.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Rust 1.91+", result.stderr)
        self.assertNotIn("uv", self.commands())

    def test_supported_custom_openssl_is_preserved(self):
        custom = self.root / "custom openssl"
        self.headers(custom)
        result = self.run_shell(TEST_RUST_VERSION="1.91.0", OPENSSL_DIR=str(custom))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"openssl={custom}", self.commands())
        self.assertNotIn("brew install", self.commands())

    def test_invalid_custom_openssl_stops_before_uv(self):
        result = self.run_shell(OPENSSL_DIR=str(self.root / "absent"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPENSSL_DIR", result.stderr)
        self.assertEqual(self.commands(), "")

    def test_missing_xcode_stops_before_uv(self):
        result = self.run_shell(TEST_CLT_STATUS="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("xcode-select --install", result.stderr)
        self.assertEqual(self.commands(), "")

    def test_missing_homebrew_stops_before_uv(self):
        result = self.run_shell(r'''
command() {
  if [[ "$*" == '-v brew' ]]; then return 1; fi
  builtin command "$@"
}
sync_python_deps
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Homebrew", result.stderr)
        self.assertEqual(self.commands(), "")

    def test_failed_prerequisite_install_stops_before_uv(self):
        result = self.run_shell(TEST_BREW_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("uv", self.commands())


if __name__ == "__main__":
    unittest.main()
