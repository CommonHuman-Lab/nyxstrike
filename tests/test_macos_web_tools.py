"""Offline regressions for macOS web-tool installation using system Bash."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASH = "/bin/bash"
WHATWEB_REVISION = "d279d93042d034f3fd29d5a893d44ccc0595d3f8"


class MacOSWebToolsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nyxstrike-web-tools-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "home with 'quotes $value"
        self.root.mkdir()
        self.bin = self.root / "mocks"
        self.managed = self.root / ".local/share/nyxstrike-tools"
        self.log = self.root / "commands.log"
        self.env = dict(os.environ)
        for key in ("BASH_ENV", "VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH"):
            self.env.pop(key, None)
        self.env.update(
            HOME=str(self.root), PATH=f"{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin",
            XDG_CONFIG_HOME=str(self.root / "config"), COMMAND_LOG=str(self.log),
            ENV_LOG=str(self.root / "environment.log"),
            MOCK_REVISION=WHATWEB_REVISION, MOCK_GEM_STATUS="0",
            MOCK_VERSION_STATUS="0", MOCK_UV_STATUS="0",
            MOCK_RUBY_PREFIX=str(self.root / "Homebrew Ruby"),
            MOCK_DEFAULT_GEMS=str(self.root / "Ruby default gems"),
            NYXSTRIKE_DATA_DIR=str(self.root / "data"),
        )

    def script(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/bash\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def run_bash(self, *args):
        result = subprocess.run(
            [BASH, *args], cwd=self.root, env=self.env,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def installer(self, body):
        source = (ROOT / "ops/scripts/install_tools.sh").read_text(encoding="utf-8")
        library, separator, _ = source.rpartition('\nmain "$@"')
        self.assertTrue(separator, "Do not execute the installer entrypoint in tests")
        path = self.root / "installer.sh"
        path.write_text(library, encoding="utf-8")
        return self.run_bash("-c", 'source "$1"\n' + body, "test", str(path))

    def mock_uv(self):
        self.script(self.bin / "uv", r'''
printf '%s\n' "$@" > "$COMMAND_LOG"
printf '%s\n' "$UV_TOOL_DIR" "$UV_TOOL_BIN_DIR" "${VIRTUAL_ENV-unset}" \
  "${PYTHONHOME-unset}" "${PYTHONPATH-unset}" > "$ENV_LOG"
[[ "$MOCK_UV_STATUS" == 0 ]] || exit "$MOCK_UV_STATUS"
mkdir -p "$UV_TOOL_BIN_DIR"
cat > "$UV_TOOL_BIN_DIR/wfuzz" <<'CLI'
#!/bin/bash
printf '%s\n' "${PYTHONHOME-unset}" "${PYTHONPATH-unset}" \
  "${PYTHONNOUSERSITE-unset}" > "$HOME/runtime-environment.log"
printf '%s\n' "$@" > "$HOME/runtime-arguments.log"
exit "$MOCK_VERSION_STATUS"
CLI
chmod +x "$UV_TOOL_BIN_DIR/wfuzz"
''')

    def test_wfuzz_uses_isolated_python_and_binary_pycurl(self):
        self.mock_uv()
        output = self.installer(r'''
UV_TOOL_DIR=original UV_TOOL_BIN_DIR=original-bin
export VIRTUAL_ENV="$HOME/server environment"
export PYTHONHOME=anaconda PYTHONPATH=anaconda-packages
_install_macos_wfuzz || exit 1
printf 'preserved:%s:%s:%s:%s\n' "$UV_TOOL_DIR" "$UV_TOOL_BIN_DIR" "$PYTHONHOME" "$PYTHONPATH"
''')
        arguments = self.log.read_text().splitlines()
        for value in ("--managed-python", "pyparsing==2.4.7", "setuptools<82", "pycurl==7.47.0"):
            self.assertIn(value, arguments)
        self.assertEqual(arguments[arguments.index("--python") + 1], "3.11")
        self.assertEqual(arguments[arguments.index("--no-build-package") + 1], "pycurl")
        self.assertIn(
            "wfuzz @ https://github.com/xmendez/wfuzz/archive/"
            "2263cd0932fef333118cd197656f709141bab615.tar.gz", arguments,
        )
        self.assertEqual(Path(self.env["ENV_LOG"]).read_text().splitlines(), [
            str(self.managed / "uv"), str(self.managed / "uv-bin"),
            str(self.root / "server environment"), "unset", "unset",
        ])
        self.assertIn("preserved:original:original-bin:anaconda:anaconda-packages", output)

    def test_wfuzz_wrapper_isolates_runtime_and_preserves_arguments(self):
        self.mock_uv()
        self.installer("_install_macos_wfuzz")
        self.env.update(PYTHONHOME="/Anaconda", PYTHONPATH="/Anaconda/packages")
        arguments = ["--help", "two words", "$(touch unexpected)", "a'b", ""]
        self.run_bash(str(self.managed / "bin/wfuzz"), *arguments)
        self.assertEqual((self.root / "runtime-environment.log").read_text().splitlines(),
                         ["unset", "unset", "1"])
        self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(), arguments)
        self.assertFalse((self.root / "unexpected").exists())

    def test_wfuzz_failure_preserves_wrapper_and_removes_temporary_wrapper(self):
        for failure in ("MOCK_UV_STATUS", "MOCK_VERSION_STATUS"):
            with self.subTest(failure=failure):
                self.mock_uv()
                self.env.update(MOCK_UV_STATUS="0", MOCK_VERSION_STATUS="0")
                self.env[failure] = "1"
                wrapper = self.managed / "bin/wfuzz"
                self.script(wrapper, "echo original\n")
                original = wrapper.read_bytes()
                output = self.installer('_install_macos_wfuzz\nprintf "status=%s\\n" "$?"')
                self.assertIn("status=1", output)
                self.assertEqual(wrapper.read_bytes(), original)
                self.assertEqual(list((self.managed / "bin").glob(".wfuzz.*")), [])

    def mock_whatweb(self):
        self.script(self.bin / "brew", r'''
[[ "$1" == --prefix && "$2" == ruby ]] || exit 91
printf '%s\n' "$MOCK_RUBY_PREFIX"
''')
        self.script(self.bin / "git", r'''
printf 'git:%s\n' "$@" >> "$COMMAND_LOG"
if [[ "$1" == clone ]]; then
  for destination in "$@"; do :; done
  mkdir -p "$destination"
  touch "$destination/whatweb"
elif [[ "$1" == -C && "$3" == rev-parse ]]; then
  printf '%s\n' "$MOCK_REVISION"
else
  exit 92
fi
''')
        prefix = Path(self.env["MOCK_RUBY_PREFIX"])
        self.script(prefix / "bin/gem", "exit 93\n")
        self.script(prefix / "bin/ruby", r'''
if [[ "$1" == -e ]]; then
  printf '%s\n' "$MOCK_DEFAULT_GEMS"
elif [[ "$1" == */bin/gem ]]; then
  printf 'gem:%s\n' "$@" >> "$COMMAND_LOG"
  printf '%s\n' "$GEM_HOME" "$GEM_PATH" > "$ENV_LOG"
  exit "$MOCK_GEM_STATUS"
else
  [[ -f "$1" ]] || exit 94
  shift
  printf '%s\n' "$@" > "$HOME/runtime-arguments.log"
  printf '%s\n' "$GEM_HOME" "$GEM_PATH" "${RUBYOPT-unset}" \
    "${RUBYLIB-unset}" "${RUBYGEMS_GEMDEPS-unset}" > "$HOME/runtime-environment.log"
  exit "$MOCK_VERSION_STATUS"
fi
''')

    def test_whatweb_wrapper_quotes_paths_and_isolates_gems(self):
        self.mock_whatweb()
        self.installer("_install_macos_whatweb")
        releases = list(self.managed.glob("whatweb-v0.6.4.*"))
        self.assertEqual(len(releases), 1)
        self.env.update(RUBYOPT="hostile", RUBYLIB="hostile", RUBYGEMS_GEMDEPS="hostile")
        arguments = ["--help", "two words", "$(touch unexpected)", "a'b", ""]
        self.run_bash(str(self.managed / "bin/whatweb"), *arguments)
        self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(), arguments)
        gem_home = str(releases[0] / "gems")
        self.assertEqual((self.root / "runtime-environment.log").read_text().splitlines(), [
            gem_home, f"{gem_home}:{self.env['MOCK_DEFAULT_GEMS']}",
            "unset", "unset", "unset",
        ])
        commands = self.log.read_text()
        for gem in ("ipaddr", "addressable", "json"):
            self.assertIn(f"gem:{gem}\n", commands)
        self.assertIn("git:https://github.com/urbanadventurer/WhatWeb.git\n", commands)
        self.assertIn("git:v0.6.4\n", commands)
        self.assertFalse((self.root / "unexpected").exists())

    def test_whatweb_failures_preserve_existing_installation_and_clean_staging(self):
        for failure in ("revision", "gem", "version"):
            with self.subTest(failure=failure):
                self.mock_whatweb()
                self.env.update(MOCK_REVISION=WHATWEB_REVISION, MOCK_GEM_STATUS="0", MOCK_VERSION_STATUS="0")
                self.env[{
                    "revision": "MOCK_REVISION", "gem": "MOCK_GEM_STATUS",
                    "version": "MOCK_VERSION_STATUS",
                }[failure]] = "1"
                wrapper = self.managed / "bin/whatweb"
                self.script(wrapper, "echo original\n")
                original = wrapper.read_bytes()
                checkout = self.managed / "user-checkout/important.txt"
                checkout.parent.mkdir(exist_ok=True)
                checkout.write_text("preserve")
                output = self.installer('_install_macos_whatweb\nprintf "status=%s\\n" "$?"')
                self.assertIn("status=1", output)
                self.assertEqual(wrapper.read_bytes(), original)
                self.assertEqual(checkout.read_text(), "preserve")
                self.assertEqual(list(self.managed.glob("whatweb-v0.6.4.*")), [])
                self.assertEqual(list((self.managed / "bin").glob(".whatweb.*")), [])

    def test_verified_installer_dry_run_does_not_execute_tools(self):
        output = self.installer(r'''
DRY_RUN=true
tool_exists() { echo unexpected >> "$COMMAND_LOG"; return 0; }
fake_install() { echo unexpected >> "$COMMAND_LOG"; }
_install_verified_macos_web_tool fixture fake_install preview
printf 'counts:%s:%s:%s\n' "$COUNT_INSTALLED" "$COUNT_ALREADY" "$COUNT_FAILED"
''')
        self.assertIn("counts:0:0:0", output)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.managed.exists())

    def test_verified_installer_checks_health_and_accounts_for_failure(self):
        for scenario in ("healthy", "repair", "backend-failure", "smoke-failure"):
            with self.subTest(scenario=scenario):
                self.env["SCENARIO"] = scenario
                self.log.unlink(missing_ok=True)
                self.script(self.managed / "bin/fixture", "exit 0\n" if scenario == "healthy" else "exit 1\n")
                output = self.installer(r'''
fake_install() {
  echo installer-called >> "$COMMAND_LOG"
  [[ "$SCENARIO" != backend-failure ]] || return 1
  printf '#!/bin/bash\nexit %s\n' "$([[ "$SCENARIO" == smoke-failure ]] && echo 1 || echo 0)" > "$HOME/.local/share/nyxstrike-tools/bin/fixture"
}
_install_verified_macos_web_tool fixture fake_install test
printf 'status:%s counts:%s:%s:%s\n' "$?" "$COUNT_INSTALLED" "$COUNT_ALREADY" "$COUNT_FAILED"
[[ "$COUNT_FAILED" == 0 ]] || printf 'failed:%s reason:%s\n' "${FAILED_TOOLS[0]}" "${FAILED_REASONS[0]}"
''')
                expected = {"healthy": "0:1:0", "repair": "1:0:0"}.get(scenario, "0:0:1")
                self.assertIn(f"counts:{expected}", output)
                self.assertEqual(self.log.exists(), scenario != "healthy")
                if scenario.endswith("failure"):
                    self.assertIn("status:1", output)
                    self.assertIn("failed:fixture reason:", output)
                else:
                    self.assertIn("status:0", output)

    def test_launcher_prefers_managed_tools_but_retains_server_python(self):
        launcher = self.root / "nyxstrike.sh"
        shutil.copyfile(ROOT / "nyxstrike.sh", launcher)
        self.script(self.root / ".local/bin/uv", "exit 0\n")
        self.script(self.root / "nyxstrike-env/bin/python3", r'''
printf '%s\n' "$(command -v python3)" "$(command -v wfuzz)" > "$COMMAND_LOG"
''')
        self.script(self.root / "nyxstrike-env/bin/wfuzz", "exit 1\n")
        self.script(self.managed / "bin/wfuzz", "exit 0\n")
        self.run_bash("-c", r'''
uname() { [[ "$1" == -s ]] && echo Linux || echo x86_64; }
export -f uname
exec /bin/bash "$1" -a
''', "test", str(launcher))
        self.assertEqual(self.log.read_text().splitlines(), [
            str(self.root / "nyxstrike-env/bin/python3"), str(self.managed / "bin/wfuzz"),
        ])


if __name__ == "__main__":
    unittest.main()
