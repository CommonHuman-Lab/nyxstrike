"""Installer regressions, runnable without backend dependencies via unittest.

Run: python3 -m unittest discover -s tests -p test_macos_installation.py
On macOS these tests exercise the system's Bash 3.2. External installs are mocked.
"""

import os
from importlib import metadata
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
BASH = "/bin/bash"


class MacOSInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nyxstrike-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.log = self.root / "commands.log"
        self.env = dict(os.environ, COMMAND_LOG=str(self.log))
        self.env.pop("BASH_ENV", None)
        self.env.pop("VIRTUAL_ENV", None)
        # Isolate user installs and sticky extras from the developer's machine.
        self.env["HOME"] = str(self.root)
        self.env["NYXSTRIKE_DATA_DIR"] = str(self.root / "data")

    def script(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
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
        self.assertTrue(separator, "Installer entrypoint must be isolated from mocks")
        path = self.root / "ops/scripts/install_tools.sh"
        path.parent.mkdir(parents=True, exist_ok=True)
        catalog = self.root / "backend/server_core/tool_constants.py"
        catalog.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "backend/server_core/tool_constants.py", catalog)
        path.write_text(library, encoding="utf-8")
        return self.run_bash("-c", 'source "$1"\n' + body, "test", str(path))

    def test_help_and_list_work_in_system_bash(self):
        installer = str(ROOT / "ops/scripts/install_tools.sh")
        self.assertIn("USAGE", self.run_bash(installer, "--help"))
        self.assertIn("Inventory", self.run_bash(installer, "--list"))

    def test_launcher_empty_and_sticky_extras(self):
        launcher = self.root / "nyxstrike.sh"
        shutil.copyfile(ROOT / "nyxstrike.sh", launcher)
        self.script(self.root / ".local/bin/uv", 'echo "uv $*" >> "$COMMAND_LOG"\n')
        self.script(
            self.root / "nyxstrike-env/bin/python3",
            'echo "server $*" >> "$COMMAND_LOG"\n',
        )
        self.script(
            self.root / "ops/scripts/install_tools.sh",
            'echo "installer $VIRTUAL_ENV" >> "$COMMAND_LOG"\n',
        )
        # This test covers extras only. Dedicated bootstrap tests mock Intel's
        # native prerequisites; never let this copied launcher run real Homebrew.
        def launch(*args: str) -> str:
            return self.run_bash("-c", '''
uname() {
  case "$1" in
    -s) echo Linux ;;
    -m) echo x86_64 ;;
    *) return 1 ;;
  esac
}
export -f uname
exec /bin/bash "$@"
''', "test", str(launcher), *args)

        launch("-a")
        self.assertIn("uv sync --inexact\n", self.log.read_text())
        launch("-a", "-t")
        self.assertIn("uv sync --inexact --extra tools\n", self.log.read_text())
        self.assertIn(f"installer {self.root}/nyxstrike-env", self.log.read_text())
        self.log.write_text("")
        launch("-a")
        self.assertIn("uv sync --inexact --extra tools\n", self.log.read_text())
        self.assertNotIn("installer", self.log.read_text())

    def constrained_install(
        self, manager: str, *, install_status: int = 0, freeze_status: int = 0,
        freeze_content: str = "cryptography==49.0.0\n", request_spec: str = "",
    ) -> str:
        """Run the real helper against a fake uv or pip executable."""
        self.env.update(
            INSTALL_STATUS=str(install_status), FREEZE_STATUS=str(freeze_status),
            FREEZE_CONTENT=freeze_content, REQUEST_SPEC=request_spec,
            TEST_MANAGER=manager, TMPDIR=str(self.root),
        )
        self.log.write_text("")
        (self.root / "install_log.txt").write_text("")
        body = r'''
printf '<%s>\n' "$@" >> "$COMMAND_LOG"
if [ "$1" = -m ]; then shift; fi
shift
action="$1"
shift
if [ "$action" = freeze ]; then
  printf '%s' "$FREEZE_CONTENT"
  exit "$FREEZE_STATUS"
fi
while [ "$#" -gt 0 ]; do
  if [ "$1" = --constraint ]; then
    shift
    printf '%s' "$1" > "$HOME/constraint-path"
    cat "$1"
  fi
  shift
done
exit "$INSTALL_STATUS"
'''
        self.script(self.root / "fake-manager", body)
        self.script(self.root / "project environment/bin/python", body)
        return self.installer('''
VIRTUAL_ENV="$PWD/project environment"
uv() { "$PWD/fake-manager" "$@"; }
command() {
  if [[ "$TEST_MANAGER" == pip && "$*" == '-v uv' ]]; then return 1; fi
  builtin command "$@"
}
if [[ -n "$REQUEST_SPEC" ]]; then
  _pip_install "$REQUEST_SPEC"
else
  _pip_install -r "$PWD/tool requirements.txt"
fi
printf 'status=%s\\n' "$?"
''')

    def test_pip_installs_preserve_project_constraints(self) -> None:
        for manager in ("uv", "pip"):
            with self.subTest(manager=manager):
                output = self.constrained_install(manager)
                commands = self.log.read_text()
                self.assertIn("status=0", output)
                diagnostics = (self.root / "install_log.txt").read_text()
                self.assertIn("cryptography==49.0.0", diagnostics)
                self.assertIn("<--constraint>", commands)
                self.assertIn(f"<{self.root}/tool requirements.txt>", commands)
                self.assertNotIn("--user", commands)
                if manager == "uv":
                    self.assertIn(
                        f"<{self.root}/project environment/bin/python>", commands
                    )
                else:
                    self.assertIn("<--all>", commands)
                constraints = Path((self.root / "constraint-path").read_text())
                self.assertFalse(constraints.exists())

    def test_dependency_conflict_has_no_unconstrained_retry(self) -> None:
        for manager in ("uv", "pip"):
            with self.subTest(manager=manager):
                output = self.constrained_install(manager, install_status=9)
                self.assertIn("status=9", output)
                self.assertEqual(self.log.read_text().count("<install>"), 1)
                self.assertEqual(self.log.read_text().count("<--constraint>"), 1)
                constraints = Path((self.root / "constraint-path").read_text())
                self.assertFalse(constraints.exists())

    def test_repair_excludes_requested_package_from_frozen_constraints(self) -> None:
        output = self.constrained_install(
            "uv",
            freeze_content="cryptography==49.0.0\nbreachsql==0.0.9\n",
            request_spec="breachsql>=0.1.0,<1.0.0",
        )
        self.assertIn("status=0", output)
        diagnostics = (self.root / "install_log.txt").read_text()
        self.assertIn("cryptography==49.0.0", diagnostics)
        self.assertNotIn("breachsql==0.0.9", diagnostics)

    def test_freeze_failure_prevents_install_and_cleans_temporary_file(self) -> None:
        for manager in ("uv", "pip"):
            with self.subTest(manager=manager):
                output = self.constrained_install(manager, freeze_status=1)
                self.assertIn("status=1", output)
                self.assertNotIn("<install>", self.log.read_text())
                self.assertEqual(list(self.root.glob("nyxstrike-pip-constraints.*")), [])

    def test_constraint_file_creation_failure_prevents_install(self) -> None:
        output = self.installer('''
VIRTUAL_ENV="$PWD/project environment"
mktemp() { return 1; }
uv() { echo unexpected >> "$COMMAND_LOG"; }
_pip_install example-tool
printf 'status=%s\\n' "$?"
''')
        self.assertIn("status=1", output)
        self.assertFalse(self.log.exists())

    def test_failure_reasons_survive_non_identifier_tool_names(self):
        output = self.installer('''
tool_exists() { return 1; }
_pkg_install() { return 1; }
_pip_install() { return 1; }
install_tool_multi "tool-one" "tool-one" "pkg:missing"
install_tool_multi "tool.two" "tool.two" "pip:missing"
print_summary
''')
        self.assertIn("tool-one", output)
        self.assertIn("package installation failed", output)
        self.assertIn("tool.two", output)
        self.assertIn("pip failed", output)

    def test_macos_dry_run_never_installs_or_downloads(self):
        for architecture in ("arm64", "x86_64"):
            with self.subTest(architecture=architecture):
                self.env["TEST_ARCH"] = architecture
                output = self.installer('''
OSTYPE=darwin
uname() { echo "$TEST_ARCH"; }
tool_exists() { return 1; }
brew() {
  case "$1" in
    --version) echo "Homebrew test" ;;
    --prefix)
      if [[ "$TEST_ARCH" == arm64 ]]; then echo /opt/homebrew; else echo /usr/local; fi ;;
    *) echo "brew $*" >> "$COMMAND_LOG"; return 1 ;;
  esac
}
curl() { echo "curl $*" >> "$COMMAND_LOG"; return 1; }
_pkg_install() { echo pkg >> "$COMMAND_LOG"; return 1; }
_pip_install() { echo pip >> "$COMMAND_LOG"; return 1; }
_go_install() { echo go >> "$COMMAND_LOG"; return 1; }
_cargo_install() { echo cargo >> "$COMMAND_LOG"; return 1; }
_gem_install() { echo gem >> "$COMMAND_LOG"; return 1; }
main --dry-run
''')
                self.assertIn("DRY-RUN", output)
                self.assertIn("bbot", output)
                self.assertFalse(
                    self.log.exists(),
                    self.log.read_text() if self.log.exists() else "",
                )

    def test_macos_cloud_does_not_download_linux_binaries(self):
        output = self.installer('''
OS=macos
PKG_MGR=brew
DRY_RUN=true
tool_exists() { return 1; }
ONLY_CATEGORY=cloud
_install_macos_catalog
install_cloud
''')
        self.assertIn("kube-bench", output)
        self.assertIn("brew: kube-bench", output)
        self.assertIn("Linux", output)
        self.assertNotIn("GitHub release binary", output)

    def steghide_fixture(self, failed_build=""):
        """Exercise source-build sequencing with local compiler fixtures."""
        self.env["FAILED_BUILD"] = failed_build
        self.log.write_text("")
        for name in ("config.guess", "config.sub"):
            path = self.root / "brew/automake/share/automake-test" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("current configuration\n")
        self.script(self.root / "configure-fixture", r'''
printf 'configure:%s:%s\n' "${PWD##*/}" "$*" >> "$COMMAND_LOG"
printf 'cpp:%s\nld:%s\npath:%s\n' "$CPPFLAGS" "$LDFLAGS" "$PATH" >> "$COMMAND_LOG"
''')
        return self.installer(r'''
_macos_native_packages() { printf 'packages:%s\n' "$*" >> "$COMMAND_LOG"; }
_macos_native_download() {
  printf 'download:%s:%s\n' "$1" "${3:-}" >> "$COMMAND_LOG"
  : > "$2"
}
brew() { [[ "$1" == --prefix ]] || return 99; printf '%s/brew/%s\n' "$HOME" "$2"; }
xcrun() { printf '/usr/bin/%s\n' "$2"; }
tar() {
  local destination="${@: -1}"
  cp "$HOME/configure-fixture" "$destination/configure"
}
patch() { printf 'patch:%s\n' "${PWD##*/}" >> "$COMMAND_LOG"; }
shasum() { echo 'a6d204744fabfe5751ab5e2d889ac373c0b0a30c  fixture'; }
make() {
  printf 'make:%s:%s\n' "${PWD##*/}" "$*" >> "$COMMAND_LOG"
  [[ "${PWD##*/}" != "$FAILED_BUILD" ]] || return 17
  if [[ "$1" == install && "${PWD##*/}" == libmcrypt ]]; then
    mkdir -p ../deps/lib ../deps/bin
    : > ../deps/lib/libmcrypt.a
    printf '#!/bin/sh\nexit 0\n' > ../deps/bin/libmcrypt-config
    chmod +x ../deps/bin/libmcrypt-config
  elif [[ "$1" == install && "${PWD##*/}" == source ]]; then
    mkdir -p ../install/bin
    printf '#!/bin/sh\necho steghide-fixture\n' > ../install/bin/steghide
    chmod +x ../install/bin/steghide
  fi
}
_macos_publish() { printf 'publish:%s:%s\n' "$1" "$2" >> "$COMMAND_LOG"; }
stage="$HOME/stage with spaces"
mkdir -p "$stage"
_macos_native_steghide "$stage"
printf 'status=%s\n' "$?"
''')

    def test_steghide_builds_private_checked_libmcrypt_before_publishing(self):
        self.assertIn("status=0", self.steghide_fixture())
        commands = self.log.read_text()
        package_line = next(line for line in commands.splitlines()
                            if line.startswith("packages:"))
        self.assertNotIn("libmcrypt", package_line)
        self.assertIn(
            "libmcrypt-2.5.8.tar.bz2:"
            "bf2f1671f44af88e66477db0982d5ecb5116a5c767b0a0d68acb34499d41b793",
            commands,
        )
        self.assertEqual(commands.count("patch:libmcrypt\n"), 4)
        self.assertIn("--disable-posix-threads --enable-static --disable-shared", commands)
        stage = self.root / "stage with spaces"
        self.assertIn(f"-I{stage}/deps/include", commands)
        self.assertIn(f"-L{stage}/deps/lib", commands)
        self.assertIn(f"path:{stage}/deps/bin:", commands)
        self.assertLess(commands.index("make:libmcrypt:install"),
                        commands.index("configure:source:"))
        self.assertIn(f"publish:steghide:{stage}/install/bin/steghide", commands)
        for name in ("config.guess", "config.sub"):
            self.assertEqual((stage / "libmcrypt" / name).read_text(),
                             "current configuration\n")

    def test_steghide_build_failures_never_publish_partial_installations(self):
        for component in ("libmcrypt", "source"):
            with self.subTest(component=component):
                self.assertIn("status=1", self.steghide_fixture(component))
                commands = self.log.read_text()
                self.assertNotIn("publish:", commands)
                self.assertNotIn(f"make:{component}:install", commands)
                if component == "libmcrypt":
                    self.assertNotIn("configure:source:", commands)

    def gstreamer_fixture(self, missing_plugin="", missing_scanner=False):
        prefix = self.root / "framework with spaces"
        (prefix / "lib").mkdir(parents=True, exist_ok=True)
        (prefix / "lib/libgstreamer-1.0.dylib").touch()
        scanner = prefix / "libexec/gstreamer-1.0/gst-plugin-scanner"
        self.script(scanner, "exit 0\n")
        if missing_scanner:
            scanner.unlink()
        self.script(prefix / "bin/gst-inspect-1.0", r'''
printf 'inspect:%s\n' "$1" >> "$COMMAND_LOG"
[ "$GST_PLUGIN_SYSTEM_PATH" = "$GST_TEST_ROOT/lib/gstreamer-1.0" ] || exit 21
[ "$GST_PLUGIN_SYSTEM_PATH_1_0" = "$GST_PLUGIN_SYSTEM_PATH" ] || exit 22
[ "$GST_PLUGIN_SCANNER" = "$GST_TEST_ROOT/libexec/gstreamer-1.0/gst-plugin-scanner" ] || exit 23
[ "$GST_PLUGIN_SCANNER_1_0" = "$GST_PLUGIN_SCANNER" ] || exit 24
[ "${GST_PLUGIN_PATH+x}" != x ] || exit 25
[ "${GST_PLUGIN_PATH_1_0+x}" != x ] || exit 26
[ "$1" != "$MISSING_PLUGIN" ] || exit 1
''')
        self.env.update(GST_TEST_ROOT=str(prefix), MISSING_PLUGIN=missing_plugin,
                        GST_PLUGIN_PATH="foreign-plugins", GST_PLUGIN_PATH_1_0="foreign-plugins")
        self.log.write_text("")
        return self.installer(r'''
_macos_gstreamer_check "$GST_TEST_ROOT"
printf 'status=%s\n' "$?"
[[ "$GST_PLUGIN_PATH" == foreign-plugins && "$GST_PLUGIN_PATH_1_0" == foreign-plugins ]] || exit 90
''')

    def test_gstreamer_checks_required_plugins_in_isolated_framework_environment(self):
        self.assertIn("status=0", self.gstreamer_fixture())
        self.assertEqual(self.log.read_text().splitlines(), [
            "inspect:--version", "inspect:playbin", "inspect:jpegdec", "inspect:avdec_h264",
        ])

    def test_gstreamer_missing_plugin_or_scanner_fails_validation(self):
        for plugin in ("playbin", "jpegdec", "avdec_h264"):
            with self.subTest(plugin=plugin):
                self.assertIn("status=1", self.gstreamer_fixture(missing_plugin=plugin))
                self.assertEqual(self.log.read_text().splitlines()[-1], f"inspect:{plugin}")
        self.assertIn("status=1", self.gstreamer_fixture(missing_scanner=True))
        self.assertEqual(self.log.read_text(), "")

    def test_managed_autopsy_rechecks_gstreamer_before_accepting_installation(self):
        stage = self.root / ".local/share/nyxstrike-tools/autopsy.fixture"
        app = stage / "app/autopsy"
        self.script(app / "bin/autopsy", 'echo unexpected-gui >> "$COMMAND_LOG"\n')
        for path in (app / "autopsy/modules/ext/sleuthkit-4.15.0.jar",
                     app / "etc/autopsy.conf", stage / "tsk/lib/libtsk_jni.dylib"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        for gst_status in (0, 1):
            with self.subTest(gstreamer_status=gst_status):
                self.env["GST_CHECK_STATUS"] = str(gst_status)
                self.log.write_text("")
                output = self.installer(r'''
brew() { [[ "$*" == '--prefix openjdk@17' ]] || return 99; echo "$HOME/java"; }
_macos_probe() { printf 'probe:%s\n' "$*" >> "$COMMAND_LOG"; }
_macos_gstreamer_check() {
  printf 'gstreamer:%s\n' "$1" >> "$COMMAND_LOG"
  return "$GST_CHECK_STATUS"
}
_macos_publish autopsy /usr/bin/env JAVA_HOME="$HOME/java" \
  "$HOME/.local/share/nyxstrike-tools/autopsy.fixture/app/autopsy/bin/autopsy" || exit 90
_macos_native_check autopsy
printf 'status=%s\n' "$?"
''')
                self.assertIn(f"status={gst_status}", output)
                commands = self.log.read_text()
                self.assertIn("gstreamer:/Library/Frameworks/GStreamer.framework/Versions/1.0\n",
                              commands)
                self.assertEqual("probe:" in commands, gst_status == 0)
                self.assertNotIn("unexpected-gui", commands)


class MacOSToolDetectionTests(unittest.TestCase):
    """Exercise real probe code without importing the API's runtime services."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nyxstrike-detection-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        environment = patch.dict(os.environ, {"PATH": str(self.bin), "HOME": str(self.root)})
        environment.start()
        self.addCleanup(environment.stop)
        self.settings = {}
        self.metadata = Mock()
        self.metadata.version.side_effect = metadata.PackageNotFoundError
        self.platform = SimpleNamespace(platform="darwin")
        source = (ROOT / "backend/server_api/ops/system_monitoring.py").read_text()
        start = source.index("def _probe_binary(")
        end = source.index("\ndef _refresh_tool_availability(", start)
        namespace = {
            "os": os, "shutil": shutil, "subprocess": subprocess,
            "sys": self.platform, "metadata": self.metadata,
            "config_core": SimpleNamespace(get=self.settings.get),
        }
        exec(compile(source[start:end], "system_monitoring_probe", "exec"), namespace)
        self.probe = namespace["_probe_binary"]

    def executable(self, name, body="exit 0\n"):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)
        return path

    def test_real_cli_aliases_and_cargo_binaries_work_without_package_managers(self):
        for check_type, tool, executable in (
            ("pip", "one-gadget", "one_gadget"),
            ("which", "testssl", "testssl.sh"),
            ("which", "ghidra", "analyzeHeadless"),
            ("cargo", "x8", "x8"),
            ("cargo", "pwninit", "pwninit"),
        ):
            with self.subTest(tool=tool):
                self.assertFalse(self.probe(check_type, tool))
                self.executable(executable)
                self.assertTrue(self.probe(check_type, tool))

    def test_python_metadata_works_without_pip_and_requires_exact_package(self):
        for name in ("phaseaccess", "stingxss", "breachsql", "vaultrip", "pwntools"):
            with self.subTest(name=name):
                self.metadata.version.reset_mock()
                self.metadata.version.side_effect = None
                self.metadata.version.return_value = "1.0"
                with patch.object(subprocess, "run", side_effect=AssertionError("pip must not run")):
                    self.assertTrue(self.probe("pip", name))
                self.metadata.version.assert_called_once_with(name)
                self.metadata.version.side_effect = metadata.PackageNotFoundError
                self.assertFalse(self.probe("pip", name))

    def test_isolated_pwn_cli_does_not_replace_server_pwntools_library(self):
        self.executable("pwn")
        self.executable("pwntools")
        self.assertFalse(self.probe("pip", "pwntools"))
        self.metadata.version.side_effect = None
        self.metadata.version.return_value = "4.15.0"
        self.assertTrue(self.probe("pip", "pwntools"))

    def test_macos_suites_require_each_representative_executable(self):
        for package, binaries in (
            ("sleuthkit", ("fls", "icat")),
            ("impacket-scripts", ("smbclient.py", "secretsdump.py")),
            ("hashcat-utils", ("cap2hccapx.bin", "combinator.bin")),
        ):
            with self.subTest(package=package):
                self.executable(binaries[0])
                self.assertFalse(self.probe("dpkg", package))
                last = self.executable(binaries[1])
                self.assertTrue(self.probe("dpkg", package))
                last.chmod(0o644)
                self.assertFalse(self.probe("dpkg", package))

    def test_macos_impacket_accepts_packaged_prefixes(self):
        self.executable("impacket-smbclient")
        self.executable("impacket-secretsdump")
        self.assertTrue(self.probe("dpkg", "impacket-scripts"))

    def test_linux_retains_dpkg_detection(self):
        self.platform.platform = "linux"
        with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            self.assertTrue(self.probe("dpkg", "sleuthkit"))
        self.assertEqual(run.call_args.args[0], ["dpkg", "-s", "sleuthkit"])

    def test_httpx_checks_identity_without_go_or_scanning(self):
        self.executable("httpx", "printf 'Python httpx 0.28.1\\n'\n")
        self.assertFalse(self.probe("go", "httpx"))
        self.executable("httpx", '[ "$#" = 1 ] && [ "$1" = -version ] || exit 9\n'
                        "printf 'projectdiscovery.io\\n[INF] Current Version: v1.7.2\\n' >&2\n")
        self.assertTrue(self.probe("go", "httpx"))

    def test_httpx_override_is_authoritative_and_must_be_a_real_executable(self):
        self.executable("httpx", "printf 'projectdiscovery.io\\n'\n")
        self.settings["BINARY_PATH_OVERRIDES"] = {"httpx": "{HOME}/custom-httpx"}
        self.assertFalse(self.probe("go", "httpx"))
        custom = self.root / "custom-httpx"
        custom.mkdir()
        self.assertFalse(self.probe("go", "httpx"))
        custom.rmdir()
        custom.write_text("#!/bin/sh\nprintf 'Python httpx\\n'\n")
        custom.chmod(0o755)
        self.assertFalse(self.probe("go", "httpx"))
        custom.write_text("#!/bin/sh\nprintf 'projectdiscovery.io\\n'\n")
        self.assertTrue(self.probe("go", "httpx"))

    def test_httpx_timeout_and_failed_execution_report_unavailable(self):
        self.executable("httpx")
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("httpx", 5)) as run:
            self.assertFalse(self.probe("go", "httpx"))
        self.assertEqual(run.call_args.kwargs["timeout"], 5)
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        with patch.object(subprocess, "run", return_value=SimpleNamespace(
            returncode=1, stdout="projectdiscovery.io"
        )):
            self.assertFalse(self.probe("go", "httpx"))

    def test_gui_directory_and_hidden_executables_are_not_available(self):
        (self.root / "Ghidra.app").mkdir()
        managed = self.root / ".local/share/nyxstrike-tools/bin"
        managed.mkdir(parents=True)
        for tool in ("ghidra", "wafw00f", "wpscan", "sublist3r"):
            self.assertFalse(self.probe("which", tool))
        executable = managed / "wafw00f"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        self.assertFalse(self.probe("which", "wafw00f"))
        with patch.dict(os.environ, {"PATH": str(managed)}):
            self.assertTrue(self.probe("which", "wafw00f"))

    def test_unsupported_notice_preserves_boolean_api_and_linux_status(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        import time

        source = (ROOT / "backend/server_api/ops/system_monitoring.py").read_text()
        start = source.index("def _refresh_tool_availability(")
        end = source.index("\ndef _get_tool_availability(", start)
        for platform in ("darwin", "linux"):
            with self.subTest(platform=platform):
                namespace = {
                    "sys": SimpleNamespace(platform=platform), "time": time,
                    "ThreadPoolExecutor": ThreadPoolExecutor,
                    "_tool_availability_lock": threading.Lock(),
                    "_tool_availability_refresh_in_progress": False,
                    "_tool_availability_cache": {}, "_probe_binary": Mock(return_value=False),
                    "ALL_TOOLS_FLAT": ["airmon-ng", "kube-bench"],
                    "BINARY_NAME_OVERRIDES": {}, "BUILT_IN_TOOLS": [],
                    "REQUIRE_DPKG_CHECK": [], "REQUIRE_PIP_CHECK": [],
                    "REQUIRE_GEM_CHECK": [], "REQUIRE_CARGO_CHECK": [], "REQUIRE_GO_CHECK": [],
                    "MACOS_UNSUPPORTED_TOOLS": {"airmon-ng": "requires Linux"},
                    "ModernVisualEngine": SimpleNamespace(COLORS={"HACKER_RED": "", "RESET": ""}),
                    "logger": Mock(),
                }
                exec(compile(source[start:end], "system_monitoring_refresh", "exec"), namespace)
                namespace["_refresh_tool_availability"]()
                self.assertEqual(namespace["_tool_availability_cache"], {
                    "airmon-ng": False, "kube-bench": False,
                })
                message = namespace["logger"].info.call_args.args[0]
                self.assertEqual("NOT SUPPORTED ON MACOS (requires Linux)" in message,
                                 platform == "darwin")
                self.assertRegex(message, r"kube-bench\s+NOT INSTALLED")


if __name__ == "__main__":
    unittest.main()
