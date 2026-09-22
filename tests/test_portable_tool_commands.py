"""Offline command regressions; no tools, servers or DNS requests are started."""

import importlib.util
import itertools
import os
from pathlib import Path
import plistlib
import shlex
import socket
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PortableToolCommandsTests(unittest.TestCase):
    def setUp(self):
        self.settings = {"BINARY_PATH_OVERRIDES": {}}
        core = types.ModuleType("backend.server_core")
        config = types.ModuleType("backend.server_core.config_core")
        config.get = self.settings.get
        core.config_core = config
        # Import only the declarative specs, without starting the application.
        with patch.dict(sys.modules, {
            "backend": types.ModuleType("backend"),
            "backend.server_core": core,
            "backend.server_core.config_core": config,
        }):
            self.base = load_module("backend.server_core.tool_spec", ROOT / "backend/server_core/tool_spec.py")
            self.modules = {}
            for name in ("smb_enum", "net_scan", "recon_bot"):
                self.modules[name] = load_module(
                    f"backend.server_core.tool_specs.{name}",
                    ROOT / f"backend/server_core/tool_specs/{name}.py",
                )
        self.temp = tempfile.TemporaryDirectory(prefix="nyxstrike-command-tests-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home with spaces"
        self.home.mkdir()
        env = patch.dict(os.environ, {"HOME": str(self.home)})
        env.start()
        self.addCleanup(env.stop)
        discovery = patch.object(self.modules["smb_enum"].shutil, "which", return_value=None)
        discovery.start()
        self.addCleanup(discovery.stop)
        platform = patch.object(self.modules["net_scan"].sys, "platform", "linux")
        platform.start()
        self.addCleanup(platform.stop)

    def build(self, module, name, **values):
        spec = next(item for item in self.modules[module].SPECS if item.name == name)
        params = {item.name: item.default for item in spec.params}
        params.update(target="example.invalid")
        params.update(values)
        return shlex.split(spec.build_command(params))

    def test_enum_all_flag_combinations(self):
        options = {"shares": "-S", "users": "-U", "groups": "-G", "policy": "-P"}
        for enabled in itertools.product((False, True), repeat=4):
            with self.subTest(enabled=enabled):
                values = dict(zip(options, enabled))
                expected = ["-A"] if all(enabled) else [options[key] for key in options if values[key]]
                self.assertEqual(self.build("smb_enum", "enum4linux-ng", **values),
                                 ["enum4linux-ng", "example.invalid", *expected])

    def test_enum_auth_domain_and_extra_args_are_quoted(self):
        argv = self.build("smb_enum", "enum4linux-ng", username="domain user",
                          password="a'b $value", domain="EXAMPLE DOMAIN",
                          additional_args='-oJ "results with spaces"')
        self.assertEqual(argv, ["enum4linux-ng", "example.invalid", "-u", "domain user",
                               "-p", "a'b $value", "-w", "EXAMPLE DOMAIN", "-A",
                               "-oJ", "results with spaces"])

    def test_enum_classic_is_unchanged(self):
        self.assertEqual(self.build("smb_enum", "enum4linux", additional_args="-a"),
                         ["enum4linux", "-a", "example.invalid"])

    def test_enum_user_install_fallback_requires_an_executable_file(self):
        candidate = self.home / ".local/bin/enum4linux-ng"
        candidate.parent.mkdir(parents=True)
        candidate.mkdir()
        self.assertEqual(self.build("smb_enum", "enum4linux-ng")[0], "enum4linux-ng")
        candidate.rmdir()
        candidate.write_text("#!/bin/sh\nexit 0\n")
        candidate.chmod(0o644)
        self.assertEqual(self.build("smb_enum", "enum4linux-ng")[0], "enum4linux-ng")
        candidate.chmod(0o755)
        self.assertEqual(self.build("smb_enum", "enum4linux-ng")[0], str(candidate))
        with patch.object(self.modules["smb_enum"].shutil, "which", return_value="/usr/bin/enum4linux-ng"):
            self.assertEqual(self.build("smb_enum", "enum4linux-ng")[0], "enum4linux-ng")

    def test_explicit_binary_overrides_expand_home_and_preserve_spaces(self):
        for name, module in (("nmap", "net_scan"), ("enum4linux-ng", "smb_enum")):
            for template in ("{HOME}/custom bin/tool", "~/custom bin/tool"):
                with self.subTest(name=name, template=template):
                    self.settings["BINARY_PATH_OVERRIDES"] = {name: template}
                    self.assertEqual(self.build(module, name)[0], str(self.home / "custom bin/tool"))
                    if name == "nmap":
                        self.assertEqual(self.build(module, "nmap-advanced")[0],
                                         str(self.home / "custom bin/tool"))

    def test_nmap_empty_or_absent_override_keeps_normal_command(self):
        for overrides in ({}, {"nmap": ""}, {"nmap": None}):
            self.settings["BINARY_PATH_OVERRIDES"] = overrides
            self.assertEqual(self.build("net_scan", "nmap"),
                             ["nmap", "-sCV", "-T4", "-Pn", "example.invalid"])
            self.assertEqual(self.build("net_scan", "nmap-advanced"),
                             ["nmap", "-sS", "example.invalid", "-T4", "-sC"])

    def test_nmap_syn_and_advanced_options_are_preserved(self):
        self.settings["BINARY_PATH_OVERRIDES"] = {"nmap": "{HOME}/custom bin/nmap"}
        argv = self.build("net_scan", "nmap-advanced", scan_type="-sS", ports="80,443",
                          version_detection=True, os_detection=True, nse_scripts="safe",
                          additional_args='-oN "scan results.txt"')
        self.assertEqual(argv, [str(self.home / "custom bin/nmap"), "-sS", "example.invalid",
                               "-p", "80,443", "-T4", "-O", "-sV", "--script=safe",
                               "-oN", "scan results.txt"])

    def test_macos_syn_uses_bpf_without_sudo_for_both_endpoints(self):
        net = self.modules["net_scan"]
        with patch.object(net.sys, "platform", "darwin"), patch.object(os, "geteuid", return_value=501), \
                patch.object(net.glob, "glob", return_value=["/dev/bpf0"]), \
                patch.object(os, "stat", return_value=types.SimpleNamespace(st_mode=stat.S_IFCHR)), \
                patch.object(os, "access", return_value=True):
            for tool in ("nmap", "nmap-advanced"):
                argv = self.build("net_scan", tool, scan_type="-sS")
                self.assertEqual(argv[:4], ["nmap", "--privileged", "--send-eth", "-sS"])
                self.assertNotIn("sudo", argv)
                self.assertNotIn("-sT", argv)
            self.assertIn("--privileged", self.build("net_scan", "nmap", scan_type="-sSV"))
            self.assertIn("--privileged", self.build("net_scan", "nmap", scan_type="-sSR"))
            self.assertIn("--privileged", self.build("net_scan", "nmap", additional_args="-sS"))

    def test_macos_missing_or_unusable_bpf_is_an_actionable_error(self):
        net = self.modules["net_scan"]
        with patch.object(net.sys, "platform", "darwin"), patch.object(os, "geteuid", return_value=501):
            for mode, accessible in ((stat.S_IFREG, True), (stat.S_IFCHR, False)):
                with self.subTest(mode=mode), patch.object(net.glob, "glob", return_value=["/dev/bpf0"]), \
                        patch.object(os, "stat", return_value=types.SimpleNamespace(st_mode=mode)), \
                        patch.object(os, "access", return_value=accessible):
                    with self.assertRaisesRegex(self.base.ToolValidationError, "packet-device access"):
                        self.build("net_scan", "nmap-advanced")
            with patch.object(net.glob, "glob", return_value=["/dev/bpf0"]), \
                    patch.object(os, "stat", side_effect=FileNotFoundError):
                with self.assertRaises(self.base.ToolValidationError):
                    self.build("net_scan", "nmap-advanced")

    def test_macos_root_and_connect_scans_do_not_need_bpf(self):
        net = self.modules["net_scan"]
        with patch.object(net.sys, "platform", "darwin"), patch.object(net.glob, "glob") as devices:
            with patch.object(os, "geteuid", return_value=0):
                self.assertEqual(self.build("net_scan", "nmap-advanced")[:2], ["nmap", "-sS"])
            with patch.object(os, "geteuid", return_value=501):
                self.assertEqual(self.build("net_scan", "nmap", scan_type="-sT")[:2], ["nmap", "-sT"])
                self.assertEqual(self.build("net_scan", "nmap")[:2], ["nmap", "-sCV"])
            devices.assert_not_called()

    def test_macos_conflicting_raw_packet_options_are_rejected(self):
        net = self.modules["net_scan"]
        with patch.object(net.sys, "platform", "darwin"), patch.object(os, "geteuid", return_value=501):
            for option in ("--send-ip", "--unprivileged"):
                with self.subTest(option=option), self.assertRaises(self.base.ToolValidationError):
                    self.build("net_scan", "nmap-advanced", additional_args=option)

    def test_macos_custom_wrapper_controls_its_own_privileges(self):
        net = self.modules["net_scan"]
        self.settings["BINARY_PATH_OVERRIDES"] = {"nmap": "{HOME}/custom bin/nmap-wrapper"}
        with patch.object(net.sys, "platform", "darwin"), patch.object(os, "geteuid", return_value=501), \
                patch.object(net.glob, "glob", return_value=[]) as devices:
            argv = self.build("net_scan", "nmap-advanced")
            self.assertEqual(argv[:2], [str(self.home / "custom bin/nmap-wrapper"), "-sS"])
            self.assertNotIn("--privileged", argv)
            devices.assert_not_called()

    def test_masscan_resolves_a_single_hostname(self):
        with patch.object(socket, "gethostbyname", return_value="192.0.2.7") as resolve:
            argv = self.build("net_scan", "masscan", target="test-host.example.invalid",
                              additional_args='--output-filename "scan results.json"')
        resolve.assert_called_once_with("test-host.example.invalid")
        self.assertEqual(argv[1], "192.0.2.7")
        self.assertEqual(argv[-2:], ["--output-filename", "scan results.json"])

    def test_masscan_preserves_numeric_targets_without_dns(self):
        for target in ("192.0.2.7", "192.0.2.0/24", "192.0.2.1-192.0.2.9",
                       "192.0.2.1-9", "2001:db8::1", "2001:db8::/120",
                       "192.0.2.1,192.0.2.2"):
            with self.subTest(target=target), patch.object(socket, "gethostbyname") as resolve:
                self.assertEqual(self.build("net_scan", "masscan", target=target)[1], target)
                resolve.assert_not_called()

    def test_masscan_dns_failures_are_validation_errors(self):
        for error in (socket.gaierror("not found"), UnicodeError("invalid hostname")):
            with self.subTest(error=error), patch.object(socket, "gethostbyname", side_effect=error):
                with self.assertRaisesRegex(self.base.ToolValidationError, "Could not resolve"):
                    self.build("net_scan", "masscan")

    def test_bbot_parameters_can_be_omitted_or_empty(self):
        module = self.modules["recon_bot"]
        spec = module.SPECS[0]
        parameter = next(item for item in spec.params if item.name == "parameters")
        self.assertFalse(parameter.required)
        self.assertEqual(parameter.default, {})
        self.assertEqual(self.build("recon_bot", "bbot"), ["bbot", "-t", "example.invalid"])
        self.assertEqual(shlex.split(module._bbot_command({"target": "example.invalid"})),
                         ["bbot", "-t", "example.invalid"])
        self.assertEqual(self.build("recon_bot", "bbot", parameters={}),
                         ["bbot", "-t", "example.invalid"])

    def test_bbot_preserves_parameters_without_mutating_them(self):
        options = {"f": "subdomain-enum", "rf": "safe", "em": "two modules"}
        expected = dict(options)
        self.assertEqual(self.build("recon_bot", "bbot", parameters=options),
                         ["bbot", "-t", "example.invalid", "-f", "subdomain-enum",
                          "-rf", "safe", "-em", "two modules"])
        self.assertEqual(options, expected)

    def test_bbot_rejects_non_object_parameters(self):
        for value in (None, "safe", [], 4):
            with self.subTest(value=value), self.assertRaises(self.base.ToolValidationError):
                self.build("recon_bot", "bbot", parameters=value)


class MacOSPacketAccessInstallerTests(unittest.TestCase):
    def setUp(self):
        source = (ROOT / "ops/scripts/install_tools.sh").read_text()
        self.library = source[source.index("_macos_install_nmap_bpf() {"):source.index("install_network() {")]

    def run_setup(self, os_name="macos", dry_run="false", present=0, result=0):
        script = self.library + r'''
COUNT_MANUAL=0
COUNT_FAILED=0
COUNT_INSTALLED=1
MANUAL_TOOLS=()
LOG_FILE=fixture.log
dry() { echo dry; }
success() { echo success; }
warn() { echo warning; }
tool_exists() { return "$TEST_PRESENT"; }
# Replace the privileged entry point: never invoke sudo, dscl or launchctl.
_macos_install_nmap_bpf() { echo setup-called; return "$TEST_RESULT"; }
_macos_setup_nmap_bpf
printf 'counts:%s:%s:%s\n' "$COUNT_INSTALLED" "$COUNT_FAILED" "$COUNT_MANUAL"
printf 'manual:%s\n' "${MANUAL_TOOLS[*]}"
'''
        env = {"PATH": "/usr/bin:/bin", "OS": os_name, "DRY_RUN": dry_run,
               "TEST_PRESENT": str(present), "TEST_RESULT": str(result)}
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(["/bin/bash", "-c", script], env=env, cwd=directory,
                                    capture_output=True, text=True, timeout=10, check=True)
            log = Path(directory) / "fixture.log"
            return result.stdout + (log.read_text() if log.exists() else "")

    def test_non_macos_and_missing_nmap_do_not_change_permissions(self):
        for settings in ({"os_name": "linux"}, {"present": 1}):
            output = self.run_setup(**settings)
            self.assertNotIn("setup-called", output)
            self.assertIn("counts:1:0:0", output)

    def test_dry_run_does_not_escalate(self):
        output = self.run_setup(dry_run="true")
        self.assertIn("dry", output)
        self.assertNotIn("setup-called", output)
        self.assertIn("counts:1:0:0", output)

    def test_success_configures_access_even_for_an_existing_nmap(self):
        output = self.run_setup()
        self.assertIn("setup-called", output)
        self.assertIn("success", output)
        self.assertIn("counts:1:0:0", output)

    def test_permission_failure_does_not_report_nmap_missing(self):
        output = self.run_setup(result=1)
        self.assertIn("warning", output)
        self.assertIn("counts:1:0:1", output)
        self.assertIn("manual:Nmap packet access", output)

    def test_generated_boot_service_and_scripts_are_valid(self):
        def heredoc(marker):
            return self.library.split("<<'" + marker + "'\n", 1)[1].split("\n" + marker + "\n", 1)[0]

        for marker in ("NYXSTRIKE_BPF_SETUP", "NYXSTRIKE_BPF_HELPER"):
            result = subprocess.run(["/bin/bash", "-n"], input=heredoc(marker), text=True,
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
        service = plistlib.loads(heredoc("NYXSTRIKE_BPF_PLIST").encode())
        self.assertTrue(service["RunAtLoad"])
        self.assertEqual(service["StartInterval"], 60)
        self.assertEqual(service["ProgramArguments"],
                         ["/Library/Application Support/NyxStrike/configure-bpf"])
        self.assertNotIn("nmap", service["ProgramArguments"])


if __name__ == "__main__":
    unittest.main()
