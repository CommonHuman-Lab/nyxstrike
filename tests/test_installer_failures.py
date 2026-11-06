"""Offline installation failures and source-tool isolation regressions."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerFailureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nyx-install-failures-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = (ROOT / "ops/scripts/install_tools.sh").read_text()
        library, separator, _ = source.rpartition('\nmain "$@"')
        self.assertTrue(separator)
        self.library = self.root / "installer.sh"
        self.library.write_text(library)

    def run_shell(self, body):
        environment = dict(os.environ)
        for name in ("BASH_ENV", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
            environment.pop(name, None)
        return subprocess.run(
            ["/bin/bash", "-c", 'source "$1"\n' + body, "test", str(self.library)],
            cwd=self.root, env=environment, text=True, capture_output=True, timeout=30,
        )

    def test_hint_does_not_leak_after_skip_success_or_dry_run(self):
        for first in ("skip", "success", "dry"):
            with self.subTest(first=first):
                result = self.run_shell(r'''
tool_exists() { [[ "$1" == existing ]]; }
FAIL_HINT='wrong hint from previous tool'
''' + {
                    "skip": 'install_tool_multi first existing pkg:first\n',
                    "success": '_pkg_install() { return 0; }\n'
                               'tool_exists() { [[ "${installed:-}" == "$1" ]]; }\n'
                               '_pkg_install() { installed=first; }\n'
                               'install_tool_multi first first pkg:first\n',
                    "dry": 'DRY_RUN=true\ninstall_tool_multi first first pkg:first\nDRY_RUN=false\n',
                }[first] + r'''
_pkg_install() { return 1; }
install_tool_multi second absent pkg:second
printf 'reason=%s\n' "${FAILED_REASONS[0]}"
''')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("wrong hint", result.stdout + result.stderr)
                self.assertIn("package installation failed", result.stdout)

    def test_command_failure_keeps_full_log_and_limits_console(self):
        result = self.run_shell(r'''
noisy() { local n; for ((n=1;n<=100;n++)); do echo "build-line-$n"; done; return 7; }
_run_install_logged build noisy
status=$?
printf 'status=%s\n' "$status"
''')
        self.assertIn("status=7", result.stdout)
        output = result.stdout + result.stderr
        self.assertNotIn("build-line-1\n", output)
        self.assertIn("build-line-100", output)
        log = (self.root / "install_log.txt").read_text()
        self.assertIn("build-line-1\n", log)
        self.assertIn("build-line-100", log)

    def test_brew_uses_mac_package_name_and_retains_errors(self):
        result = self.run_shell(r'''
PKG_MGR=brew
brew() { printf 'brew arguments: %s\n' "$*" >&2; return 9; }
_pkg_install bulk-extractor
printf 'status=%s\n' "$?"
''')
        self.assertIn("status=9", result.stdout)
        self.assertIn("brew arguments: install bulk_extractor", result.stderr)
        self.assertIn("brew arguments: install bulk_extractor",
                      (self.root / "install_log.txt").read_text())

    def test_main_reports_failure_to_caller(self):
        for failures in (0, 2):
            with self.subTest(failures=failures):
                result = self.run_shell(r'''
detect_os() { :; }
check_prerequisites() { :; }
install_network() { COUNT_FAILED=''' + str(failures) + r'''; }
main --dry-run --only network
''')
                self.assertEqual(result.returncode, int(failures > 0), result.stderr)
                self.assertIn("Installation Summary", result.stdout)

    def test_source_install_isolated_and_publishes_only_working_cli(self):
        for tool, binary, help_status in (("netexec", "nxc", 0),
                                          ("enum4linux-ng", "enum4linux-ng", 0),
                                          ("netexec", "nxc", 5)):
            with self.subTest(tool=tool, status=help_status):
                result = self.run_shell(r'''
task_home="$PWD/home with 'quotes \$value"
mkdir -p "$task_home"
_run_source_test() (
  # Scope simulated home to the installer subprocess only.
  export HOME="$task_home"
  export VIRTUAL_ENV="$PWD/server-venv" PYTHONHOME=old-python PYTHONPATH=old-packages
  mkdir -p "$HOME/.local/bin"
  printf '#!/bin/bash\necho original\n' > "$HOME/.local/bin/''' + binary + r'''"
  chmod +x "$HOME/.local/bin/''' + binary + r'''"
  tool_exists() { return 0; }
  uv() {
    printf '%s\n' "$@" > "$PWD/uv-args"
    printf '%s\n' "${VIRTUAL_ENV-unset}" "${PYTHONHOME-unset}" "${PYTHONPATH-unset}" "$UV_TOOL_DIR" > "$PWD/uv-env"
    mkdir -p "$UV_TOOL_BIN_DIR"
    printf '#!/bin/bash\nexit ''' + str(help_status) + r'''\n' > "$UV_TOOL_BIN_DIR/''' + binary + r'''"
    chmod +x "$UV_TOOL_BIN_DIR/''' + binary + r'''"
  }
  _install_macos_source_tool ''' + tool + " " + binary + r''' git+https://example.invalid/repository@revision
  printf 'status=%s\n' "$?"
  printf 'server=%s\n' "$VIRTUAL_ENV"
)
_run_source_test
''')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"status={int(help_status > 0)}", result.stdout)
                args = (self.root / "uv-args").read_text().splitlines()
                self.assertEqual(args[:2], ["tool", "install"])
                self.assertIn("git+https://example.invalid/repository@revision", args)
                env = (self.root / "uv-env").read_text().splitlines()
                self.assertEqual(env[:3], ["unset", "unset", "unset"])
                self.assertIn("nyxstrike-tools", env[3])
                wrapper = self.root / "home with 'quotes $value/.local/bin" / binary
                self.assertEqual("echo original" in wrapper.read_text(), help_status > 0)

    def test_launcher_does_not_announce_success_after_installer_failure(self):
        source = (ROOT / "nyxstrike.sh").read_text()
        library, separator, _ = source.partition("# Argument parsing\n")
        self.assertTrue(separator)
        launcher = self.root / "launcher.sh"
        launcher.write_text(library + "\n" + r'''
update_self_repo() { :; }
sync_python_deps() { :; }
bash() { return 17; }
INSTALL_TOOLS=true
run_setup
''')
        environment = dict(os.environ)
        environment.pop("BASH_ENV", None)
        result = subprocess.run(
            ["/bin/bash", str(launcher)], cwd=self.root, env=environment,
            text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 17)
        self.assertNotIn("Setup complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
