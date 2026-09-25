"""Offline macOS CLI recipe regressions; no package managers reach the network."""

import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MacOSCLIRecipesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nyxstrike-cli-recipes-")
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
            NYXSTRIKE_DATA_DIR=str(self.root / "data"), MOCK_UV_STATUS="0",
            MOCK_CLI_STATUS="0", MOCK_FORMULA_PREFIX=str(self.root / "brew formula"),
        )

    def script(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/bash\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def run_bash(self, *args):
        result = subprocess.run(
            ["/bin/bash", *args], cwd=self.root, env=self.env,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def installer(self, body, catalog=None):
        source = (ROOT / "ops/scripts/install_tools.sh").read_text(encoding="utf-8")
        library, separator, _ = source.rpartition('\nmain "$@"')
        self.assertTrue(separator, "Do not run the real installer entrypoint")
        path = self.root / "ops/scripts/install_tools.sh"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(library, encoding="utf-8")
        constants = self.root / "backend/server_core/tool_constants.py"
        constants.parent.mkdir(parents=True, exist_ok=True)
        if catalog is None:
            shutil.copyfile(ROOT / "backend/server_core/tool_constants.py", constants)
        else:
            constants.write_text("MACOS_TOOL_INSTALLATION = " + repr(catalog), encoding="utf-8")
        return self.run_bash("-c", 'source "$1"\n' + body, "test", str(path))

    def mock_uv(self):
        self.script(self.bin / "uv", r'''
printf '%s\n' "$@" > "$COMMAND_LOG"
printf '%s\n' "${VIRTUAL_ENV-unset}" "${PYTHONHOME-unset}" \
  "${PYTHONPATH-unset}" "${UV_PROJECT_ENVIRONMENT-unset}" "${UV_PYTHON-unset}" \
  > "$HOME/install-environment.log"
[[ "$MOCK_UV_STATUS" == 0 ]] || exit "$MOCK_UV_STATUS"
for package in "$@"; do :; done
mkdir -p "$UV_TOOL_BIN_DIR"
cat > "$UV_TOOL_BIN_DIR/$package" <<'CLI'
#!/bin/bash
printf '%s\n' "$@" > "$HOME/runtime-arguments.log"
printf '%s\n' "${PYTHONHOME-unset}" "${PYTHONPATH-unset}" \
  "${PYTHONNOUSERSITE-unset}" > "$HOME/runtime-environment.log"
exit "$MOCK_CLI_STATUS"
CLI
chmod +x "$UV_TOOL_BIN_DIR/$package"
''')

    def test_wafw00f_uses_official_source_and_isolated_runtime(self):
        self.mock_uv()
        for name, repository in (("wafw00f", "enablesecurity/wafw00f"),):
            with self.subTest(name=name):
                output = self.installer(r'''
export VIRTUAL_ENV=server PYTHONHOME=anaconda PYTHONPATH=server-packages
export UV_PROJECT_ENVIRONMENT=server-env UV_PYTHON=server-python
''' + f"_install_macos_{name} || exit 1\n" + r'''
printf 'preserved:%s:%s:%s\n' "$VIRTUAL_ENV" "$PYTHONHOME" "$UV_PYTHON"
''')
                args = self.log.read_text().splitlines()
                self.assertEqual(args[args.index("--python") + 1], "3.12")
                self.assertIn("--managed-python", args)
                self.assertIn(repository.lower(), args[args.index("--from") + 1].lower())
                self.assertEqual(args[-1], name)
                self.assertEqual((self.root / "install-environment.log").read_text().splitlines(),
                                 ["unset"] * 5)
                self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(),
                                 ["--help"])
                self.assertIn("preserved:server:anaconda:server-python", output)
                arguments = ["--help", "two words", "$(touch unexpected)", "a'b", ""]
                self.env.update(PYTHONHOME="anaconda", PYTHONPATH="server-packages")
                self.run_bash(str(self.managed / "bin" / name), *arguments)
                self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(),
                                 arguments)
                self.assertEqual((self.root / "runtime-environment.log").read_text().splitlines(),
                                 ["unset", "unset", "1"])
                self.assertFalse((self.root / "unexpected").exists())

    def test_python_failed_install_or_probe_preserves_previous_wrapper(self):
        for name in ("wafw00f", "sublist3r"):
            if name == "sublist3r":
                self.mock_sublist3r()
            else:
                self.mock_uv()
            for failure in ("MOCK_UV_STATUS", "MOCK_CLI_STATUS"):
                with self.subTest(name=name, failure=failure):
                    self.env.update(MOCK_UV_STATUS="0", MOCK_CLI_STATUS="0")
                    self.env[failure] = "1"
                    wrapper = self.managed / "bin" / name
                    self.script(wrapper, "echo previous\n")
                    original = wrapper.read_bytes()
                    output = self.installer(f'_install_macos_{name}\nprintf "status:%s\\n" "$?"')
                    self.assertIn("status:1", output)
                    self.assertEqual(wrapper.read_bytes(), original)
                    self.assertEqual(list((self.managed / "bin").glob(f".{name}.*")), [])
                    self.assertEqual(list(self.managed.glob(f"{name}.*")), [])

    def mock_sublist3r(self):
        self.script(self.bin / "git", r'''
printf 'git:%s\n' "$@" >> "$COMMAND_LOG"
for last in "$@"; do :; done
if [[ "$1" == init ]]; then
  mkdir -p "$last"
elif [[ "$1" == -C ]]; then
  case "$3" in
    remote) : ;;
    fetch) printf '%s\n' "$last" > "$HOME/fetched-revision" ;;
    checkout) touch "$2/sublist3r.py" "$2/requirements.txt" ;;
    rev-parse)
      [[ "${MOCK_BAD_REVISION:-0}" == 0 ]] || { echo wrong-revision; exit 0; }
      cat "$HOME/fetched-revision"
      ;;
    *) exit 91 ;;
  esac
else
  exit 92
fi
''')
        self.script(self.bin / "uv", r'''
printf 'uv:%s\n' "$@" >> "$COMMAND_LOG"
printf '%s\n' "${VIRTUAL_ENV-unset}" "${PYTHONHOME-unset}" \
  "${PYTHONPATH-unset}" "${UV_PROJECT_ENVIRONMENT-unset}" "${UV_PYTHON-unset}" \
  >> "$HOME/install-environment.log"
[[ "$MOCK_UV_STATUS" == 0 ]] || exit "$MOCK_UV_STATUS"
if [[ "$1" == venv ]]; then
  for destination in "$@"; do :; done
  mkdir -p "$destination/bin"
  cat > "$destination/bin/python" <<'CLI'
#!/bin/bash
[[ "$1" == /*/source/sublist3r.py && -f "$1" ]] || exit 93
shift
printf '%s\n' "$@" > "$HOME/runtime-arguments.log"
printf '%s\n' "${PYTHONHOME-unset}" "${PYTHONPATH-unset}" \
  "${PYTHONNOUSERSITE-unset}" > "$HOME/runtime-environment.log"
exit "$MOCK_CLI_STATUS"
CLI
  chmod +x "$destination/bin/python"
elif [[ "$1" == pip && "$2" == install ]]; then
  for requirements in "$@"; do :; done
  [[ "$requirements" == /*/source/requirements.txt && -f "$requirements" ]] || exit 94
  exit "${MOCK_PIP_STATUS:-0}"
else
  exit 95
fi
''')

    def test_sublist3r_uses_checkout_and_venv_without_installing_legacy_package(self):
        self.mock_sublist3r()
        self.installer(r'''
export VIRTUAL_ENV=server PYTHONHOME=anaconda PYTHONPATH=server-packages
export UV_PROJECT_ENVIRONMENT=server-env UV_PYTHON=server-python
_install_macos_sublist3r
''')
        commands = self.log.read_text().splitlines()
        self.assertIn("git:https://github.com/aboul3la/Sublist3r.git", commands)
        self.assertIn("git:--detach", commands)
        self.assertIn("git:FETCH_HEAD", commands)
        self.assertIn("git:rev-parse", commands)
        self.assertIn("uv:venv", commands)
        self.assertIn("uv:3.12", commands)
        self.assertIn("uv:--managed-python", commands)
        self.assertIn("uv:-r", commands)
        self.assertNotIn("uv:tool", commands)
        self.assertEqual((self.root / "install-environment.log").read_text().splitlines(),
                         ["unset"] * 10)
        self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(), ["--help"])
        arguments = ["--help", "two words", "$(touch unexpected)", "a'b", ""]
        self.env.update(PYTHONHOME="anaconda", PYTHONPATH="server-packages")
        self.run_bash(str(self.managed / "bin/sublist3r"), *arguments)
        self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(), arguments)
        self.assertEqual((self.root / "runtime-environment.log").read_text().splitlines(),
                         ["unset", "unset", "1"])
        self.assertFalse((self.root / "unexpected").exists())

    def test_sublist3r_rejects_wrong_revision_or_failed_dependency_install(self):
        self.mock_sublist3r()
        for failure in ("MOCK_BAD_REVISION", "MOCK_PIP_STATUS"):
            with self.subTest(failure=failure):
                self.env.update(MOCK_BAD_REVISION="0", MOCK_PIP_STATUS="0")
                self.env[failure] = "1"
                wrapper = self.managed / "bin/sublist3r"
                self.script(wrapper, "echo previous\n")
                original = wrapper.read_bytes()
                output = self.installer('_install_macos_sublist3r\nprintf "status:%s\\n" "$?"')
                self.assertIn("status:1", output)
                self.assertEqual(wrapper.read_bytes(), original)
                self.assertEqual(list(self.managed.glob("sublist3r.*")), [])

    def mock_brew(self):
        self.script(self.bin / "brew", r'''
[[ "$1" == --prefix && "$2" == wpscanteam/tap/wpscan ]] || exit 91
printf '%s\n' "$MOCK_FORMULA_PREFIX"
''')

    def test_wpscan_installs_official_tap_and_quotes_wrapper_arguments(self):
        self.mock_brew()
        self.env.update(GEM_HOME="other-gems", GEM_PATH="other-gems", RUBYOPT="other-options",
                        RUBYLIB="other-ruby", RUBYGEMS_GEMDEPS="other-dependencies")
        self.installer(r'''
_pkg_install() {
  printf '%s\n' "$@" >> "$COMMAND_LOG"
  printf '%s\n' "${GEM_HOME-unset}" "${GEM_PATH-unset}" "${RUBYOPT-unset}" \
    "${RUBYLIB-unset}" "${RUBYGEMS_GEMDEPS-unset}" > "$HOME/install-ruby-environment.log"
  mkdir -p "$MOCK_FORMULA_PREFIX/bin"
  cat > "$MOCK_FORMULA_PREFIX/bin/wpscan" <<'CLI'
#!/bin/bash
printf '%s\n' "$@" > "$HOME/runtime-arguments.log"
printf '%s\n' "${GEM_HOME-unset}" "${GEM_PATH-unset}" "${RUBYOPT-unset}" \
  "${RUBYLIB-unset}" "${RUBYGEMS_GEMDEPS-unset}" > "$HOME/runtime-ruby-environment.log"
exit 0
CLI
  chmod +x "$MOCK_FORMULA_PREFIX/bin/wpscan"
}
_install_macos_wpscan
''')
        self.assertEqual(self.log.read_text().splitlines(), ["wpscanteam/tap/wpscan"])
        self.assertEqual((self.root / "install-ruby-environment.log").read_text().splitlines(),
                         ["unset"] * 5)
        self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(),
                         ["--version"])
        arguments = ["--help", "two words", "$(touch unexpected)", "a'b", ""]
        self.run_bash(str(self.managed / "bin/wpscan"), *arguments)
        self.assertEqual((self.root / "runtime-arguments.log").read_text().splitlines(), arguments)
        self.assertEqual((self.root / "runtime-ruby-environment.log").read_text().splitlines(),
                         ["unset"] * 5)
        self.assertFalse((self.root / "unexpected").exists())

    def test_wpscan_reuses_healthy_official_formula_without_installing(self):
        self.mock_brew()
        self.script(Path(self.env["MOCK_FORMULA_PREFIX"]) / "bin/wpscan", "exit 0\n")
        self.installer(r'''
_pkg_install() { echo unexpected >> "$COMMAND_LOG"; return 1; }
_install_macos_wpscan
''')
        self.assertFalse(self.log.exists())
        self.assertTrue((self.managed / "bin/wpscan").is_file())

    def test_wpscan_bad_probe_preserves_previous_wrapper(self):
        self.mock_brew()
        self.script(Path(self.env["MOCK_FORMULA_PREFIX"]) / "bin/wpscan", "exit 1\n")
        wrapper = self.managed / "bin/wpscan"
        self.script(wrapper, "echo previous\n")
        original = wrapper.read_bytes()
        output = self.installer(r'''
_pkg_install() { return 0; }
_install_macos_wpscan
printf 'status:%s\n' "$?"
''')
        self.assertIn("status:1", output)
        self.assertEqual(wrapper.read_bytes(), original)
        self.assertEqual(list((self.managed / "bin").glob(".wpscan.*")), [])

    def test_wpscan_repairs_existing_broken_formula(self):
        prefix = Path(self.env["MOCK_FORMULA_PREFIX"])
        self.script(prefix / "bin/wpscan", "exit 7\n")
        self.script(self.bin / "brew", r'''
if [[ "$1" == --prefix && "$2" == wpscanteam/tap/wpscan ]]; then
  printf '%s\n' "$MOCK_FORMULA_PREFIX"
elif [[ "$1" == reinstall && "$2" == wpscanteam/tap/wpscan ]]; then
  printf 'reinstall:%s\n' "$2" >> "$COMMAND_LOG"
  cat > "$MOCK_FORMULA_PREFIX/bin/wpscan" <<'CLI'
#!/bin/bash
[[ "$1" == --version ]]
CLI
  chmod +x "$MOCK_FORMULA_PREFIX/bin/wpscan"
else
  exit 91
fi
''')
        self.installer('_install_macos_wpscan || exit 1')
        self.assertEqual(self.log.read_text().splitlines(), [
            "reinstall:wpscanteam/tap/wpscan"
        ])
        self.assertTrue((self.managed / "bin/wpscan").is_file())

    def test_wpscan_uses_private_ruby_fallback_when_formula_build_fails(self):
        ruby_prefix = self.root / "ruby-3.4"
        self.script(self.bin / "brew", r'''
if [[ "$1" == install && "$2" == ruby@3.4 ]]; then
  printf 'brew:%s\n' "$2" >> "$COMMAND_LOG"
elif [[ "$1" == --prefix && "$2" == ruby@3.4 ]]; then
  printf '%s\n' "$HOME/ruby-3.4"
else
  exit 90
fi
''')
        self.script(ruby_prefix / "bin/ruby", r'''
if [[ "$1" == -e ]]; then
  printf '%s\n' "$HOME/default-gems"
else
  printf '%s\n' "$@" > "$HOME/wpscan-ruby-arguments"
fi
''')
        self.script(ruby_prefix / "bin/gem", r'''
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == --bindir ]]; then
    shift
    mkdir -p "$1"
    printf '#!/bin/bash\nexit 0\n' > "$1/wpscan"
    chmod +x "$1/wpscan"
  fi
  shift
done
''')
        self.installer('_install_macos_wpscan_gem || exit 1')
        self.assertTrue((self.managed / "bin/wpscan").is_file())
        self.run_bash(str(self.managed / "bin/wpscan"), "--version")
        self.assertIn("brew:ruby@3.4", self.log.read_text())
        self.assertEqual(
            (self.root / "wpscan-ruby-arguments").read_text().splitlines()[-1],
            "--version",
        )

    def test_wpscan_falls_back_when_formula_installs_but_cannot_start(self):
        self.mock_brew()
        self.installer(r'''
_pkg_install() {
  mkdir -p "$MOCK_FORMULA_PREFIX/bin"
  printf '#!/bin/bash\nexit 7\n' > "$MOCK_FORMULA_PREFIX/bin/wpscan"
  chmod +x "$MOCK_FORMULA_PREFIX/bin/wpscan"
}
_install_macos_wpscan_gem() {
  printf 'gem-fallback\n' >> "$COMMAND_LOG"
  mkdir -p "$HOME/.local/share/nyxstrike-tools/bin"
  printf '#!/bin/bash\nexit 0\n' > "$HOME/.local/share/nyxstrike-tools/bin/wpscan"
  chmod +x "$HOME/.local/share/nyxstrike-tools/bin/wpscan"
}
_install_macos_wpscan || exit 1
''')
        self.assertEqual(self.log.read_text().splitlines(), ["gem-fallback"])
        self.run_bash(str(self.managed / "bin/wpscan"), "--version")

    def test_managed_only_requires_managed_executable_and_uses_help_probe(self):
        self.script(self.bin / "fixture", "exit 0\n")
        output = self.installer(r'''
fake_install() {
  echo installed >> "$COMMAND_LOG"
  mkdir -p "$HOME/.local/share/nyxstrike-tools/bin"
  cat > "$HOME/.local/share/nyxstrike-tools/bin/fixture" <<'CLI'
#!/bin/bash
[[ "$1" == --help ]]
CLI
  chmod +x "$HOME/.local/share/nyxstrike-tools/bin/fixture"
}
_install_verified_macos_web_tool fixture fake_install test --help true || exit 1
_install_verified_macos_web_tool fixture fake_install test --help true || exit 1
printf 'counts:%s:%s:%s\n' "$COUNT_INSTALLED" "$COUNT_ALREADY" "$COUNT_FAILED"
''')
        self.assertEqual(self.log.read_text().splitlines(), ["installed"])
        self.assertIn("counts:1:1:0", output)

    def test_categories_register_managed_macos_recipes(self):
        output = self.installer(r'''
OS=macos
tool_exists() { return 0; }
install_tool_multi() { :; }
_install_verified_macos_web_tool() { printf 'recipe:%s:%s:%s:%s\n' "$1" "$2" "${4:---version}" "${5:-false}"; }
install_network
install_web
''')
        for name, probe in (("wafw00f", "--help"), ("sublist3r", "--help"), ("wpscan", "--version")):
            self.assertEqual(output.count(f"recipe:{name}:_install_macos_{name}:{probe}:true"), 1)

    def test_full_launcher_all_and_tools_installs_all_categories_then_starts_server(self):
        launcher_source = (ROOT / "nyxstrike.sh").read_text(encoding="utf-8")
        marker = "# Argument parsing\n"
        self.assertEqual(launcher_source.count(marker), 1)
        overrides = r'''
update_self_repo() {
  [[ "$UPDATE_SELF" == true ]] || return 91
  echo update >> "$COMMAND_LOG"
}
sync_python_deps() {
  [[ "$INSTALL_TOOLS" == true && "$RUN_SERVER" == true ]] || return 92
  echo sync >> "$COMMAND_LOG"
}
uname() {
  case "$1" in -s) echo Darwin ;; -m) echo x86_64 ;; *) return 93 ;; esac
}
brew() {
  case "$1" in
    --prefix) printf '%s\n' "$HOME/mock-homebrew" ;;
    --version) echo 'Homebrew fixture' ;;
    update) echo brew-update >> "$COMMAND_LOG" ;;
    *) return 94 ;;
  esac
}
export -f uname brew
export OSTYPE=darwin
'''
        launcher = self.root / "nyxstrike.sh"
        launcher.write_text(launcher_source.replace(marker, overrides + marker), encoding="utf-8")
        installer_source = (ROOT / "ops/scripts/install_tools.sh").read_text(encoding="utf-8")
        library, separator, _ = installer_source.rpartition('\nmain "$@"')
        self.assertTrue(separator)
        category_stubs = r'''
bootstrap_essentials() { :; }
check_prerequisites() { :; }
setup_paths() { :; }
check_paths() { :; }
record_category() {
  echo "category:$1" >> "$COMMAND_LOG"
  (( COUNT_INSTALLED++ )) || true
}
publish_fixture() {
  mkdir -p "$HOME/.local/share/nyxstrike-tools/bin"
  printf '#!/bin/bash\nexit 0\n' > "$HOME/.local/share/nyxstrike-tools/bin/$1"
  chmod +x "$HOME/.local/share/nyxstrike-tools/bin/$1"
}
install_network() { record_category network; publish_fixture sublist3r; }
install_web() { record_category web; publish_fixture wafw00f; publish_fixture wpscan; }
install_auth() { record_category auth; }
install_binary() { record_category binary; }
install_cloud() { record_category cloud; }
install_ctf() { record_category ctf; }
install_osint() { record_category osint; }
install_browser() { record_category browser; }
_macos_check() { return 0; }
_macos_cask_check() { return 0; }
_macos_server_python_check() { return 0; }
_run_install_logged() { return 0; }
_pip_install() { return 0; }
main "$@"
'''
        self.script(self.root / "ops/scripts/install_tools.sh", library + category_stubs)
        constants = self.root / "backend/server_core/tool_constants.py"
        constants.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "backend/server_core/tool_constants.py", constants)
        self.script(self.root / "nyxstrike-env/bin/python3", r'''
if [[ "$1" == - ]]; then exec /usr/bin/python3 "$@"; fi
[[ "$#" == 1 && "$1" == "$HOME/nyxstrike_server.py" ]] || exit 95
[[ "$(tail -n 1 "$COMMAND_LOG")" == category:browser ]] || exit 96
for name in wafw00f wpscan sublist3r; do
  [[ "$(command -v "$name")" == "$HOME/.local/share/nyxstrike-tools/bin/$name" ]] || exit 97
  "$name" --help || exit 98
done
echo server-started >> "$COMMAND_LOG"
''')
        # Existing server-environment entrypoints must not hide the new wrappers.
        for name in ("wafw00f", "wpscan", "sublist3r"):
            self.script(self.root / "nyxstrike-env/bin" / name, "exit 99\n")
        output = self.run_bash(str(launcher), "-a", "-t")
        self.assertEqual(self.log.read_text().splitlines(), [
            "update", "sync", "brew-update", "category:network", "category:web",
            "category:auth", "category:binary", "category:cloud", "category:ctf",
            "category:osint", "category:browser", "server-started",
        ])
        self.assertIn("Installation Summary", output)
        self.assertIn("Setup complete.", output)
        self.assertIn("macOS tool installation and validation", output)
        self.assertIn("NOT SUPPORTED ON MACOS", output)

    def test_catalog_covers_every_requested_tool_and_has_complete_routes(self):
        catalog = runpy.run_path(str(ROOT / "backend/server_core/tool_constants.py"))["MACOS_TOOL_INSTALLATION"]
        original = """airbase-ng aircrack-ng airdecap-ng aireplay-ng airmon-ng airodump-ng
anew assetfinder autopsy bettercap breachsql bulk_extractor burpsuite clair cloudmapper
dirb dnsenum docker-bench-security dotdotpwn eaphammer enum4linux-ng evil-winrm falco
gdb ghidra gospider hashcat-utils hashpump hcxdumptool hcxpcapngtool httpx hurl
impacket-scripts jaeles joomscan kismet kube-bench kube-hunter libc-database maltego
massdns mdk4 msfconsole msfvenom nbtscan nxc one-gadget ophcrack outguess pacu parsero
patator phaseaccess prowler pwninit pwntools qsreplace rpcclient scalpel scout-suite
shuffledns sleuthkit spiderfoot steghide stingxss sublist3r terrascan testssl tshark
vaultrip vulnx wfuzz whatweb wifite wpscan x8 xsser zaproxy""".split()
        self.assertEqual(len(original), 78)
        self.assertEqual(set(catalog), set(original) | {"sslscan", "wafw00f"})
        for name, spec in catalog.items():
            with self.subTest(name=name):
                self.assertTrue({"category", "binary", "method", "target", "probe", "source_url"} <= spec.keys())
                self.assertIn(spec["category"], {"network", "web", "auth", "binary", "cloud", "ctf", "osint", "browser"})
                self.assertTrue(spec["source_url"].startswith("https://"))
                self.assertTrue(spec.get("reason") if spec["method"] == "unsupported" else spec["target"])
                if spec["method"] == "go":
                    self.assertIn("@", spec["target"])
                    self.assertNotIn("@latest", spec["target"])

    def test_catalog_dispatches_every_method_and_preserves_python_interpreter(self):
        output = self.installer(r'''
OS=macos
ready=false
_macos_check() { if [[ "$ready" == true ]]; then ready=false; return 0; fi; return 1; }
_macos_cask_check() { if [[ "$ready" == true ]]; then ready=false; return 0; fi; return 1; }
_macos_server_python_check() { if [[ "$ready" == true ]]; then ready=false; return 0; fi; return 1; }
record_backend() { printf '%s|' "$@" >> "$COMMAND_LOG"; printf '\n' >> "$COMMAND_LOG"; ready=true; }
_macos_brew() { record_backend brew "$@"; }
_macos_cask() { record_backend cask "$@"; }
_macos_go() { record_backend go "$@"; }
_macos_python_package() { record_backend python "$@"; }
_macos_python_source() { record_backend python-source "$@"; }
_pip_install() { record_backend server-python "$@"; }
_macos_gem() { record_backend gem "$@"; }
_macos_cargo() { record_backend cargo "$@"; }
_macos_native() { record_backend native "$@"; }
_install_macos_catalog
printf 'counts:%s:%s:%s\n' "$COUNT_INSTALLED" "$COUNT_FAILED" "$COUNT_SKIPPED"
''')
        records = self.log.read_text().splitlines()
        catalog = runpy.run_path(str(ROOT / "backend/server_core/tool_constants.py"))["MACOS_TOOL_INSTALLATION"]
        expected = [spec for spec in catalog.values() if spec["method"] not in {"existing", "unsupported"}]
        self.assertEqual(len(records), len(expected))
        self.assertEqual({row.split("|")[0] for row in records}, {spec["method"] for spec in expected})
        self.assertIn(
            "python|patator|patator|git+https://github.com/lanjelot/patator.git@"
            "964e87c4932fc20f3d0c3226a8e409eae527e831|3.13|",
            records,
        )
        self.assertIn("server-python|pwntools==4.15.0|", records)
        self.assertIn("brew|rpcclient|rpcclient|samba|--help|", records)
        self.assertIn("counts:65:0:8", output)

    def test_catalog_input_cannot_be_consumed_by_an_installer_backend(self):
        output = self.installer(r'''
OS=macos
ready=false
_macos_check() { [[ "$ready" == true ]] && { ready=false; return 0; }; return 1; }
_macos_native() {
  printf '%s\n' "$1" >> "$COMMAND_LOG"
  cat >/dev/null
  ready=true
}
_install_macos_catalog
printf 'counts:%s:%s\n' "$COUNT_INSTALLED" "$COUNT_FAILED"
''', catalog={name: {
            "category": "web", "binary": name, "method": "native",
            "target": name, "probe": "--help",
            "source_url": f"https://example.invalid/{name}",
        } for name in ("first", "second")})
        self.assertEqual(self.log.read_text().splitlines(), ["first", "second"])
        self.assertIn("counts:2:0", output)

    def test_patator_uses_pinned_source_without_unportable_database_adapters(self):
        revision = "964e87c4932fc20f3d0c3226a8e409eae527e831"
        self.script(self.bin / "uv", r'''
printf '%s\n' "$*" >> "$COMMAND_LOG"
if [[ "$*" == *" venv "* ]]; then
  for target in "$@"; do :; done
  mkdir -p "$target/bin"
  printf '#!/bin/bash\nexit 0\n' > "$target/bin/python"
  chmod +x "$target/bin/python"
elif [[ "$*" == *"git+https://github.com/lanjelot/patator.git@"* ]]; then
  while [[ "$1" != --python ]]; do shift; done
  mkdir -p "$(dirname "$2")"
  printf '#!/bin/bash\n[[ "$1" == http_fuzz && "$2" == --help ]]\n' > "$(dirname "$2")/patator"
  chmod +x "$(dirname "$2")/patator"
fi
''')
        output = self.installer(f'''
_macos_native_packages() {{ :; }}
brew() {{ [[ "$1" == --prefix ]] && printf '%s\\n' "$HOME/$2"; }}
_macos_python_package patator patator \
  'git+https://github.com/lanjelot/patator.git@{revision}' 3.13 || exit 1
''')
        commands = self.log.read_text()
        self.assertIn(f"patator.git@{revision}", commands)
        self.assertIn("--no-deps", commands)
        self.assertNotIn("cx_Oracle", commands)
        self.assertEqual(output, "")

    def test_impacket_precheck_requires_primary_and_secretsdump(self):
        self.script(self.bin / "smbclient.py", "exit 0\n")
        output = self.installer(
            '_macos_check impacket-scripts smbclient.py -h\nprintf "status:%s\\n" "$?"')
        self.assertIn("status:1", output)
        self.script(self.bin / "secretsdump.py", "exit 0\n")
        self.installer('_macos_check impacket-scripts smbclient.py -h || exit 1')

    def test_server_python_catalog_reuses_healthy_distribution_and_cli(self):
        server = self.root / "server"
        self.script(server / "bin/python", "exit 0\n")
        self.script(self.bin / "breachsql", "exit 0\n")
        output = self.installer(r'''
OS=macos
VIRTUAL_ENV="$HOME/server"
_pip_install() { echo unexpected >> "$COMMAND_LOG"; return 1; }
_install_macos_catalog
printf 'counts:%s:%s\n' "$COUNT_ALREADY" "$COUNT_INSTALLED"
''', catalog={"breachsql": {
            "category": "web", "binary": "breachsql", "method": "server-python",
            "target": "breachsql>=0.1.0,<1.0.0", "probe": "--help",
            "source_url": "https://pypi.org/project/breachsql/",
        }})
        self.assertFalse(self.log.exists())
        self.assertIn("counts:1:0", output)

        output = self.installer(r'''
_macos_server_python_check fixture fixture --help 'flask<0'
printf 'status:%s\n' "$?"
''')
        self.assertIn("status:1", output)

    def test_cask_repairs_broken_app_and_maltego_installs_java11(self):
        self.script(self.root / "burpsuite", "exit 0\n")
        self.installer(r'''
_macos_cask_check() {
  [[ -f "$HOME/burp-ready" ]] || return 1
  printf '%s\n' "$HOME/burpsuite"
}
brew() {
  if [[ "$1" == list ]]; then return 1; fi
  [[ "$1" == install && "$2" == --cask && "$3" == --force && "$4" == burp-suite ]] || return 90
  echo repair-burp >> "$COMMAND_LOG"
  touch "$HOME/burp-ready"
}
mkdir -p "$HOME/Applications/Burp Suite.app"
_macos_cask burpsuite burp-suite || exit 1
''')
        self.assertEqual(self.log.read_text().splitlines(), ["repair-burp"])
        self.assertTrue((self.managed / "bin/burpsuite").is_file())

        self.log.unlink()
        self.script(self.root / "maltego", "exit 0\n")
        self.script(self.root / "java11/bin/java", "exit 0\n")
        self.installer(r'''
_macos_java11_home() {
  [[ -f "$HOME/java-ready" ]] || return 1
  printf '%s\n' "$HOME/java11"
}
brew() {
  if [[ "$1" == list ]]; then return 1; fi
  [[ "$1" == install && "$2" == --cask && "$3" == temurin@11 ]] || return 91
  echo install-java11 >> "$COMMAND_LOG"
  touch "$HOME/java-ready"
}
_macos_cask_check() {
  _macos_java11_check >/dev/null || return 1
  printf '%s\n' "$HOME/maltego"
}
_macos_cask maltego maltego || exit 1
''')
        self.assertEqual(self.log.read_text().splitlines(), ["install-java11"])
        self.assertTrue((self.managed / "bin/maltego").is_file())

    def test_catalog_category_filter_and_dry_run_never_attempt_installation(self):
        output = self.installer(r'''
OS=macos
ONLY_CATEGORY=auth
DRY_RUN=true
_macos_check() { echo unexpected >> "$COMMAND_LOG"; return 1; }
_run_install_logged() { echo unexpected >> "$COMMAND_LOG"; return 1; }
_pip_install() { echo unexpected >> "$COMMAND_LOG"; return 1; }
_install_macos_catalog
printf 'handled:%s\n' "$MACOS_HANDLED"
''')
        self.assertFalse(self.log.exists())
        self.assertIn("evil-winrm", output)
        self.assertNotIn("airmon-ng", output)
        self.assertNotIn("assetfinder", output)
        self.assertNotIn("wafw00f", output)

    def test_failed_catalog_recipe_is_counted_once_without_legacy_retry(self):
        catalog = runpy.run_path(str(ROOT / "backend/server_core/tool_constants.py"))["MACOS_TOOL_INSTALLATION"]
        output = self.installer(r'''
OS=macos
_macos_native() { echo native-attempt >> "$COMMAND_LOG"; return 1; }
_macos_check() { return 1; }
_pkg_install() { echo unexpected-legacy-retry >> "$COMMAND_LOG"; return 1; }
_install_macos_catalog
install_tool_multi dirb dirb pkg:dirb
printf 'counts:%s:%s:%s\n' "$COUNT_INSTALLED" "$COUNT_FAILED" "$COUNT_SKIPPED"
printf 'failed:%s\n' "${FAILED_TOOLS[@]}"
''', catalog={key: catalog[key] for key in ("dirb", "airmon-ng")})
        self.assertEqual(self.log.read_text().splitlines(), ["native-attempt"])
        self.assertIn("counts:0:1:1", output)
        self.assertIn("failed:dirb", output)
        self.assertIn("NOT SUPPORTED ON MACOS", output)

    def test_publish_quotes_fixed_arguments_and_isolates_runtime_environment(self):
        executable = self.root / "runtime with 'quotes $value"
        self.script(executable, r'''
printf '%s\n' "$@" > "$HOME/published-arguments"
printf '%s\n' "${PYTHONHOME-unset}" "${PYTHONPATH-unset}" "${RUBYOPT-unset}" \
  "${RUBYLIB-unset}" "$PYTHONNOUSERSITE" > "$HOME/published-environment"
''')
        self.installer(r'''
_macos_publish fixture "$HOME/runtime with 'quotes \$value" 'fixed argument' '$(touch unexpected)' || exit 1
''')
        arguments = ["two words", "a'b", "", "$(touch unexpected)"]
        self.env.update(PYTHONHOME="host", PYTHONPATH="host", RUBYOPT="host", RUBYLIB="host")
        self.run_bash(str(self.managed / "bin/fixture"), *arguments)
        self.assertEqual((self.root / "published-arguments").read_text().splitlines(),
                         ["fixed argument", "$(touch unexpected)", *arguments])
        self.assertEqual((self.root / "published-environment").read_text().splitlines(), ["unset"] * 4 + ["1"])
        self.assertFalse((self.root / "unexpected").exists())

    def test_httpx_requires_projectdiscovery_at_the_api_override_path(self):
        self.script(self.bin / "httpx", "printf 'projectdiscovery.io\\n'\n")
        output = self.installer('_macos_check httpx httpx -version\nprintf "status:%s\\n" "$?"')
        self.assertIn("status:1", output)
        self.script(self.root / "go/bin/httpx", "printf 'Python httpx 0.28.1\\n'\n")
        output = self.installer('_macos_check httpx httpx -version\nprintf "status:%s\\n" "$?"')
        self.assertIn("status:1", output)
        self.script(self.root / "go/bin/httpx", '[[ "$#" == 1 && "$1" == -version ]] || exit 9\n'
                    "printf 'projectdiscovery.io\\n'\n")
        self.installer('_macos_check httpx httpx -version || exit 1')

    def test_go_install_publishes_managed_binary_and_preserves_api_override(self):
        self.script(self.bin / "go", r'''
if [[ "$1" == version ]]; then echo go1.25.0; exit 0; fi
[[ "$1" == install && "$2" == fixture/module@v1.0.0 ]] || exit 90
printf '%s\n' "${GOOS-unset}" "${GOARCH-unset}" "${GOROOT-unset}" > "$HOME/go-environment"
mkdir -p "$GOBIN"
printf '#!/bin/bash\nprintf "projectdiscovery.io\\n"\n' > "$GOBIN/httpx"
chmod +x "$GOBIN/httpx"
''')
        self.installer(r'''
export GOOS=linux GOARCH=arm64 GOROOT=wrong
_macos_go httpx httpx fixture/module@v1.0.0 -version || exit 1
''')
        self.assertEqual((self.root / "go-environment").read_text().splitlines(), ["unset"] * 3)
        for executable in (self.root / "go/bin/httpx", self.managed / "bin/httpx"):
            self.assertIn("projectdiscovery.io", self.run_bash(str(executable), "-version"))

    def test_brew_resolves_sbin_and_publishes_samba_dependencies(self):
        prefix = Path(self.env["MOCK_FORMULA_PREFIX"])
        self.script(self.bin / "brew", '[[ "$1" == --prefix && "$2" == samba ]] || exit 90\n'
                    'printf "%s\\n" "$MOCK_FORMULA_PREFIX"\n')
        for binary in ("rpcclient", "net", "nmblookup", "smbclient"):
            directory = "sbin" if binary == "rpcclient" else "bin"
            self.script(prefix / directory / binary, "exit 0\n")
        self.installer('_macos_brew rpcclient rpcclient samba || exit 1')
        for binary in ("rpcclient", "net", "nmblookup", "smbclient"):
            self.assertTrue((self.managed / "bin" / binary).is_file())

    def test_brew_repairs_present_formula_when_cli_is_missing_or_broken(self):
        prefix = Path(self.env["MOCK_FORMULA_PREFIX"])
        prefix.mkdir(parents=True)
        self.script(self.bin / "brew", r'''
if [[ "$1" == --prefix && "$2" == fixture ]]; then
  printf '%s\n' "$MOCK_FORMULA_PREFIX"
elif [[ "$1" == reinstall && "$2" == fixture ]]; then
  printf 'reinstall:%s\n' "$2" >> "$COMMAND_LOG"
  mkdir -p "$MOCK_FORMULA_PREFIX/bin"
  cat > "$MOCK_FORMULA_PREFIX/bin/fixture" <<'CLI'
#!/bin/bash
[[ "$1" == --version ]] || exit 92
printf 'fixture 1.0\n'
CLI
  chmod +x "$MOCK_FORMULA_PREFIX/bin/fixture"
else
  exit 90
fi
''')
        for state in ("missing", "broken"):
            with self.subTest(state=state):
                shutil.rmtree(prefix / "bin", ignore_errors=True)
                if state == "broken":
                    self.script(prefix / "bin/fixture", "exit 7\n")
                self.log.unlink(missing_ok=True)
                self.installer('_macos_brew fixture fixture fixture --version || exit 1')
                self.assertEqual(self.log.read_text().splitlines(), ["reinstall:fixture"])
                self.assertIn("fixture 1.0", self.run_bash(
                    str(self.managed / "bin/fixture"), "--version"))

    def test_testssl_native_recipe_is_pinned_and_published(self):
        output = self.installer(r'''
_macos_native_checkout() {
  [[ "$1" == testssl/testssl.sh ]] || exit 90
  [[ "$2" == 97763a411c525720a5f9bd9d2cded416b10f210a ]] || exit 91
  mkdir -p "$3"
  cat > "$3/testssl.sh" <<'CLI'
#!/bin/bash
[[ "$1" == --version ]] || exit 92
printf 'testssl 3.2.4\n'
CLI
  chmod +x "$3/testssl.sh"
}
_macos_native testssl || exit 1
_macos_native_check testssl || exit 2
"$HOME/.local/share/nyxstrike-tools/bin/testssl.sh" --version
''')
        self.assertIn("testssl 3.2.4", output)

    def test_sslscan_native_recipe_uses_pinned_official_source(self):
        output = self.installer(r'''
_macos_native_packages() { :; }
brew() { [[ "$1" == --prefix && "$2" == openssl@3 ]] && printf '%s\n' "$HOME/openssl"; }
_macos_native_checkout() {
  [[ "$1" == rbsec/sslscan ]] || exit 90
  [[ "$2" == 9c3fefa0a4b6b743c820e4f813ae2f8b695ab67e ]] || exit 91
  mkdir -p "$3"
}
make() {
  [[ "$1" == -C ]] || exit 92
  [[ " $* " == *" CC=clang "* ]] || exit 93
  [[ " $* " == *" CPPFLAGS=-I$HOME/openssl/include "* ]] || exit 94
  [[ " $* " == *" LDFLAGS=-L$HOME/openssl/lib -Wl,-rpath,$HOME/openssl/lib "* ]] || exit 95
  cat > "$2/sslscan" <<'CLI'
#!/bin/bash
[[ "$1" == --version ]] && printf 'sslscan 2.2.2\n'
CLI
  chmod +x "$2/sslscan"
}
_macos_native sslscan || exit 1
_macos_native_check sslscan || exit 2
"$HOME/.local/share/nyxstrike-tools/bin/sslscan" --version
''')
        self.assertIn("sslscan 2.2.2", output)

    def test_macos_catalog_owns_testssl_without_legacy_second_attempt(self):
        source = (ROOT / "ops/scripts/install_tools.sh").read_text(encoding="utf-8")
        start = source.index("  # testssl.sh — git clone")
        end = source.index("\n  # sslscan", start)
        block = source[start:end]
        self.assertIn("if ! _macos_catalog_contains testssl &&", block)
        self.assertIn("elif ! _macos_catalog_contains testssl; then", block)

    def test_macos_browser_uses_selenium_manager_without_chromedriver_cask(self):
        self.script(self.root / "venv/bin/python", 'cat > "$HOME/manager-probe.py"\n')
        output = self.installer(r'''
OS=macos
VIRTUAL_ENV="$HOME/venv"
tool_exists() { return 0; }
brew() { echo unexpected >> "$COMMAND_LOG"; return 1; }
install_browser
''')
        self.assertFalse(self.log.exists())
        self.assertIn("Selenium Manager runtime verified", output)
        probe = (self.root / "manager-probe.py").read_text()
        self.assertIn("SeleniumManager._get_binary()", probe)
        self.assertIn('str(binary), "--version"', probe)

    def test_macos_browser_counts_missing_chrome_as_failure(self):
        output = self.installer(r'''
OS=macos
_macos_browser_installed() { return 1; }
brew() { return 1; }
_macos_selenium_manager_check() { return 0; }
install_browser
printf 'counts:%s:%s\n' "$COUNT_FAILED" "$COUNT_ALREADY"
printf 'failed:%s\n' "${FAILED_TOOLS[*]}"
''')
        self.assertIn("counts:1:1", output)
        self.assertIn("failed:google-chrome", output)

    def test_ghidra_publication_validates_java_without_launching_gui(self):
        prefix = Path(self.env["MOCK_FORMULA_PREFIX"])
        self.script(self.bin / "brew", r'''
[[ "$1" == --prefix ]] || exit 90
case "$2" in
  ghidra) printf '%s\n' "$MOCK_FORMULA_PREFIX" ;;
  openjdk@21) printf '%s\n' "$HOME/java prefix" ;;
  *) exit 91 ;;
esac
''')
        self.script(self.root / "java prefix/bin/java", '[[ "$1" == -version ]] || exit 92\n')
        self.script(prefix / "libexec/support/analyzeHeadless", "echo unexpected >> \"$COMMAND_LOG\"\nexit 93\n")
        self.script(prefix / "bin/ghidraRun", "echo unexpected >> \"$COMMAND_LOG\"\nexit 94\n")
        self.installer('_macos_brew ghidra analyzeHeadless ghidra || exit 1')
        self.assertTrue((self.managed / "bin/analyzeHeadless").is_file())
        self.assertTrue((self.managed / "bin/ghidra").is_file())
        self.assertFalse(self.log.exists())

    def test_msfvenom_accepts_upstream_help_exit_one_but_rejects_failures(self):
        executable = self.bin / "msfvenom"
        for status, banner, expected in (
            (0, "MsfVenom\nUsage: msfvenom [options]", 0),
            (1, "MsfVenom\nUsage: msfvenom [options]", 0),
            (1, "LoadError: cannot load metasploit", 1),
            (2, "MsfVenom\nUsage: msfvenom [options]", 1),
            (0, "unrelated command", 1),
        ):
            with self.subTest(status=status, banner=banner):
                self.script(executable, f"cat <<'BANNER'\n{banner}\nBANNER\nexit {status}\n")
                output = self.installer(r'''
_macos_check msfvenom msfvenom --help
printf 'check:%s\n' "$?"
_macos_publish msfvenom "$(command -v msfvenom)" || exit 1
_macos_native_check msfvenom
printf 'native:%s\n' "$?"
''')
                self.assertIn(f"check:{expected}", output)
                self.assertIn(f"native:{expected}", output)

    def test_vulnx_uses_version_subcommand_without_update_checks(self):
        catalog = runpy.run_path(str(ROOT / "backend/server_core/tool_constants.py"))["MACOS_TOOL_INSTALLATION"]
        self.script(self.bin / "vulnx", r'''
printf '%s\n' "$*" >> "$COMMAND_LOG"
[[ " $* " == *" --disable-update-check "* ]] || exit 91
case "$1" in
  version) [[ "$#" == 2 ]] || exit 92 ;;
  id|search|auth) [[ " $* " == *" --help "* ]] || exit 93 ;;
  *) exit 94 ;;
esac
''')
        probe = catalog["vulnx"]["probe"]
        self.installer(f"_macos_check vulnx vulnx '{probe}' || exit 1")
        commands = self.log.read_text().splitlines()
        self.assertEqual(len(commands), 4)
        self.assertTrue(commands[0].startswith("version "))

    def test_kismet_trusts_only_official_formulas_when_brew_supports_trust(self):
        prefix = Path(self.env["MOCK_FORMULA_PREFIX"])
        self.script(prefix / "bin/kismet", '[[ "$1" == --version ]] || exit 90\n')
        self.script(self.bin / "brew", r'''
printf '%s\n' "$*" >> "$COMMAND_LOG"
case "$1" in
  command) [[ "$2" == trust && "$MOCK_SUPPORTS_TRUST" == 1 ]] ;;
  tap) [[ "$2" == kismetwireless/kismet ]] ;;
  trust)
    [[ "$2" == --formula ]] || exit 91
    [[ "$3" == kismetwireless/kismet/kismet || "$3" == kismetwireless/kismet/kismet-git ]] ;;
  --prefix)
    [[ "$2" == kismetwireless/kismet/kismet ]] || exit 92
    printf '%s\n' "$MOCK_FORMULA_PREFIX" ;;
  *) exit 93 ;;
esac
''')
        for supported in ("1", "0"):
            with self.subTest(supports_trust=supported):
                self.env["MOCK_SUPPORTS_TRUST"] = supported
                self.log.unlink(missing_ok=True)
                self.installer('_macos_brew kismet kismet kismetwireless/kismet/kismet --version || exit 1')
                commands = self.log.read_text().splitlines()
                trusts = [command for command in commands if command.startswith("trust ")]
                if supported == "1":
                    self.assertEqual(trusts, [
                        "trust --formula kismetwireless/kismet/kismet",
                        "trust --formula kismetwireless/kismet/kismet-git",
                    ])
                    self.assertLess(commands.index(trusts[-1]),
                                    commands.index("--prefix kismetwireless/kismet/kismet"))
                else:
                    self.assertEqual(trusts, [])

    def test_cloudmapper_uses_legacy_python_and_isolated_setuptools_constraint(self):
        self.mock_sublist3r()
        git = self.bin / "git"
        git.write_text(git.read_text().replace("sublist3r.py", "cloudmapper.py"))
        self.script(self.bin / "uv", r'''
[[ "$1" == --no-config ]] || exit 90
shift
if [[ "$1" == venv ]]; then
  [[ " $* " == *" --python 3.9 "* ]] || exit 91
  for destination in "$@"; do :; done
  mkdir -p "$destination/bin"
  cat > "$destination/bin/python" <<'CLI'
#!/bin/bash
[[ "$1" == */source/cloudmapper.py && "$2" == collect && "$3" == --help ]] || exit 92
CLI
  chmod +x "$destination/bin/python"
elif [[ "$1" == pip && "$2" == install ]]; then
  constraint=""
  while [[ "$#" -gt 0 ]]; do
    [[ "$1" != --build-constraint ]] || constraint="$2"
    shift
  done
  [[ -f "$constraint" ]] || exit 93
  [[ "$(cat "$constraint")" == 'setuptools<82' ]] || exit 94
  printf 'constrained-build\n' >> "$COMMAND_LOG"
else
  exit 95
fi
''')
        self.installer('_macos_python_source cloudmapper || exit 1')
        self.assertIn("constrained-build", self.log.read_text())
        self.assertTrue((self.managed / "bin/cloudmapper").is_file())

    def test_dotdotpwn_installs_http_and_https_perl_dependencies(self):
        prefix = Path(self.env["MOCK_FORMULA_PREFIX"])
        self.script(prefix / "bin/cpanm", "exit 90\n")
        self.script(prefix / "bin/perl", r'''
if [[ "$1" == */bin/cpanm ]]; then
  [[ " $* " == *" LWP::UserAgent "* ]] || exit 91
  [[ " $* " == *" LWP::Protocol::https "* ]] || exit 92
  [[ " $* " == *" --local-lib-contained "* ]] || exit 93
  printf 'http-modules-installed\n' >> "$COMMAND_LOG"
elif [[ "$1" == -c ]]; then
  [[ -f "$2" ]] || exit 94
else
  exit 95
fi
''')
        self.installer(r'''
_macos_native_packages() { :; }
brew() { [[ "$1" == --prefix ]] && printf '%s\n' "$MOCK_FORMULA_PREFIX"; }
_macos_native_checkout() {
  mkdir -p "$3"
  touch "$3/dotdotpwn.pl"
}
_macos_native dotdotpwn || exit 1
''')
        self.assertEqual(self.log.read_text().splitlines(), ["http-modules-installed"])
        self.assertTrue((self.managed / "bin/dotdotpwn").is_file())

    def test_dirb_repairs_archive_directory_permissions_before_configure(self):
        self.installer(r'''
_macos_native_packages() { :; }
_macos_native_download() { :; }
brew() { [[ "$1" == --prefix ]] && printf '%s\n' "$MOCK_FORMULA_PREFIX"; }
tar() {
  for destination in "$@"; do :; done
  mkdir -p "$destination/src"
  touch "$destination/src/dirb.c"
  cat > "$destination/configure" <<'CONFIGURE'
[[ -r src/dirb.c ]] || exit 90
printf '%s\n' "${1#--prefix=}" > "$HOME/dirb-prefix"
CONFIGURE
  chmod 664 "$destination/src"
}
make() {
  [[ "$1" == install ]] || return 0
  local prefix
  prefix=$(cat "$HOME/dirb-prefix")
  mkdir -p "$prefix/bin"
  printf '#!/bin/bash\necho "Usage: dirb URL"\nexit 1\n' > "$prefix/bin/dirb"
  chmod +x "$prefix/bin/dirb"
}
_macos_native dirb || exit 1
''')
        self.assertTrue((self.managed / "bin/dirb").is_file())

    def test_outguess_uses_apple_archive_tools_for_bundled_jpeg(self):
        self.installer(r'''
_macos_native_packages() { :; }
brew() { [[ "$1" == --prefix ]] && printf '%s\n' "$MOCK_FORMULA_PREFIX"; }
xcrun() {
  [[ "$1" == --find ]] || return 90
  printf '/apple/toolchain with spaces/%s\n' "$2"
}
_macos_native_checkout() {
  mkdir -p "$3"
  cat > "$3/configure" <<'CONFIGURE'
printf '%s\n' "${1#--prefix=}" > "$HOME/outguess-prefix"
CONFIGURE
}
make() {
  [[ " $* " == *" AR=/apple/toolchain\ with\ spaces/ar rc "* ]] || return 91
  [[ " $* " == *" AR2=/apple/toolchain\ with\ spaces/ranlib "* ]] || return 92
  [[ " $* " == *" RANLIB=/apple/toolchain\ with\ spaces/ranlib "* ]] || return 93
  printf 'apple-archive-tools\n' >> "$COMMAND_LOG"
  [[ " $* " == *" install "* ]] || return 0
  local prefix
  prefix=$(cat "$HOME/outguess-prefix")
  mkdir -p "$prefix/bin"
  printf '#!/bin/bash\necho "Usage: outguess [options]"\nexit 1\n' > "$prefix/bin/outguess"
  chmod +x "$prefix/bin/outguess"
}
_macos_native outguess || exit 1
''')
        self.assertEqual(self.log.read_text().splitlines(), ["apple-archive-tools"] * 2)
        self.assertTrue((self.managed / "bin/outguess").is_file())

    def test_gdb_patches_old_sdk_includes_and_preserves_targets_and_python(self):
        python = self.root / "deps/python@3.14/bin/python3.14"
        self.script(python, "exit 0\n")
        for architecture, failure in (("x86_64", "none"), ("arm64", "none"),
                                      ("x86_64", "probe")):
            with self.subTest(architecture=architecture, failure=failure):
                self.env.update(MOCK_ARCHITECTURE=architecture, MOCK_FAILURE=failure)
                wrapper = self.managed / "bin/gdb"
                self.script(wrapper, "echo previous-installation\n")
                original = wrapper.read_bytes()
                existing_stages = set(self.managed.glob("gdb.*"))
                output = self.installer(r'''
_macos_native_packages() { :; }
brew() { [[ "$1" == --prefix ]] && printf '%s\n' "$HOME/deps/$2"; }
uname() { [[ "$1" == -m ]] && printf '%s\n' "$MOCK_ARCHITECTURE"; }
xcrun() { [[ "$1" == --find ]] && printf '/apple/toolchain/%s\n' "$2"; }
_macos_native_download() {
  [[ "$1" == https://ftp.gnu.org/gnu/gdb/gdb-17.2.tar.xz ]] || return 90
  [[ "$3" == 1c036c0d72e4b3d1fb5c94c88632add6f9d76f4d7c4d2ea793c12a9f19a3228c ]] || return 91
}
tar() {
  local destination filename
  for destination in "$@"; do :; done
  mkdir -p "$destination/gdb/arch"
  for filename in amd64-linux-tdesc.c i386-linux-tdesc.c; do
    printf '#include "defs.h"\nstatic std::unordered_map<int, int> tdesc_cache;\n' \
      > "$destination/gdb/arch/$filename"
  done
  printf '#include "inferior.h"\n' > "$destination/gdb/darwin-nat.c"
  cat > "$destination/configure" <<'CONFIGURE'
[[ "$CC" == /apple/toolchain/clang && "$CXX" == /apple/toolchain/clang++ ]] || exit 92
[[ "$AR" == /apple/toolchain/ar && "$RANLIB" == /apple/toolchain/ranlib ]] || exit 93
printf '%s\n' "$@" > "$HOME/gdb-configure-arguments"
printf '%s\n' "${1#--prefix=}" > "$HOME/gdb-prefix"
CONFIGURE
}
make() {
  [[ "$1" == install-gdb ]] || return 0
  [[ "$2" == maybe-install-gdbserver ]] || return 94
  local prefix
  prefix=$(cat "$HOME/gdb-prefix")
  mkdir -p "$prefix/bin"
  cat > "$prefix/bin/gdb" <<'CLI'
#!/bin/bash
[[ "$1" == --batch && "$2" == -nx && "$3" == -ex ]] || exit 95
[[ "$4" == 'python import sys; print(sys.version)' && "$MOCK_FAILURE" != probe ]] || exit 96
echo '3.14.0 (embedded Python)'
CLI
  chmod +x "$prefix/bin/gdb"
}
_macos_native gdb
printf 'status:%s\n' "$?"
''')
                arguments = (self.root / "gdb-configure-arguments").read_text().splitlines()
                self.assertIn("--enable-targets=all", arguments)
                self.assertIn(f"--with-python={python}", arguments)
                self.assertEqual("--target=x86_64-apple-darwin20" in arguments,
                                 architecture == "arm64")
                stages = set(self.managed.glob("gdb.*"))
                if failure == "none":
                    self.assertIn("status:0", output)
                    stage, = stages - existing_stages
                    for filename in ("amd64-linux-tdesc.c", "i386-linux-tdesc.c"):
                        source = (stage / "source/gdb/arch" / filename).read_text()
                        self.assertIn("#include <unordered_map>\n", source)
                        self.assertIn("std::unordered_map<int, int> tdesc_cache;", source)
                    darwin = (stage / "source/gdb/darwin-nat.c").read_text()
                    self.assertIn('#include "gdbsupport/common-inferior.h"', darwin)
                    self.assertNotEqual(wrapper.read_bytes(), original)
                else:
                    self.assertIn("status:1", output)
                    self.assertEqual(wrapper.read_bytes(), original)
                    self.assertEqual(stages, existing_stages)

    def test_tshark_bundle_is_detached_and_verified_before_publication(self):
        for failure in ("none", "copy", "signature", "probe", "detach", "detach-always"):
            with self.subTest(failure=failure):
                self.env["MOCK_FAILURE"] = failure
                self.log.unlink(missing_ok=True)
                wrapper = self.managed / "bin/tshark"
                self.script(wrapper, "echo previous-installation\n")
                original = wrapper.read_bytes()
                existing_stages = set(self.managed.glob("tshark.*"))
                output = self.installer(r'''
_macos_native_download() {
  [[ "$1" == https://www.wireshark.org/download/osx/all-versions/Wireshark%204.6.8.dmg ]] || return 90
  [[ "$3" == 7de945ed1ba324259ba7e3b2ca2fe11a854cf48a33dc6d4423dd531e466a1f3a ]] || return 91
}
hdiutil() {
  printf '%s\n' "$1" >> "$COMMAND_LOG"
  if [[ "$1" == attach ]]; then
    [[ "$2" == -readonly && "$3" == -nobrowse && "$4" == -mountpoint ]] || return 92
    mkdir -p "$5/Wireshark.app/Contents/MacOS"
    cat > "$5/Wireshark.app/Contents/MacOS/tshark" <<'CLI'
#!/bin/bash
printf 'probe\n' >> "$COMMAND_LOG"
[[ "$1" == --version && "$MOCK_FAILURE" != probe ]] || exit 93
echo 'TShark (Wireshark) 4.6.8'
CLI
    chmod +x "$5/Wireshark.app/Contents/MacOS/tshark"
  elif [[ "$1" == detach ]]; then
    if [[ "$2" == -force ]]; then
      printf 'force\n' >> "$COMMAND_LOG"
      [[ "$MOCK_FAILURE" != detach-always ]] || return 97
    else
      [[ "$MOCK_FAILURE" != detach && "$MOCK_FAILURE" != detach-always ]] || return 96
    fi
  fi
}
ditto() {
  printf 'copy\n' >> "$COMMAND_LOG"
  [[ "$MOCK_FAILURE" != copy ]] || return 94
  cp -R "$1" "$2"
}
codesign() {
  printf 'signature\n' >> "$COMMAND_LOG"
  [[ "$1" == --verify && "$2" == --deep && "$3" == --strict ]] || return 95
  [[ "$MOCK_FAILURE" != signature ]]
}
_macos_native tshark
printf 'status:%s\n' "$?"
''')
                commands = self.log.read_text().splitlines()
                self.assertEqual(commands.count("attach"), 1)
                expected_detaches = 4 if failure == "detach-always" else 2 if failure == "detach" else 1
                self.assertEqual(commands.count("detach"), expected_detaches)
                self.assertEqual(commands.count("force"), expected_detaches // 2)
                if failure in ("none", "detach"):
                    self.assertIn("status:0", output)
                    self.assertLess(commands.index("detach"), commands.index("signature"))
                    self.assertLess(commands.index("signature"), commands.index("probe"))
                    self.assertIn("TShark", self.run_bash(str(wrapper), "--version"))
                else:
                    self.assertIn("status:1", output)
                    self.assertEqual(wrapper.read_bytes(), original)
                    stages = set(self.managed.glob("tshark.*"))
                    if failure == "detach-always":
                        stage, = stages - existing_stages
                        self.assertTrue((stage / ".mounted-image").is_file())
                        self.assertTrue((stage / "mount/Wireshark.app").is_dir())
                        self.assertNotIn("signature", commands)
                    else:
                        self.assertEqual(stages, existing_stages)

    def test_uv_bootstrap_retains_managed_tool_path_priority(self):
        launcher_source = (ROOT / "nyxstrike.sh").read_text(encoding="utf-8")
        library, separator, _ = launcher_source.partition("# Argument parsing\n")
        self.assertTrue(separator)
        self.script(self.root / ".local/bin/uv", "exit 0\n")
        self.script(self.root / ".local/bin/wafw00f", "exit 99\n")
        self.script(self.managed / "bin/wafw00f", "exit 0\n")
        fixture = self.root / "uv-bootstrap.sh"
        fixture.write_text(library + r'''
export PATH="$HOME/.local/share/nyxstrike-tools/bin:$HOME/.local/bin:/usr/bin:/bin"
uv_checks=0
command() {
  if [[ "$1" == -v && "$2" == uv ]]; then
    uv_checks=$((uv_checks + 1))
    [[ "$uv_checks" -gt 1 ]] || return 1
  fi
  builtin command "$@"
}
curl() { echo 'exit 0'; }
ensure_uv_ready
[[ "$uv_checks" == 2 ]] || exit 91
[[ "${PATH%%:*}" == "$HOME/.local/share/nyxstrike-tools/bin" ]] || exit 92
[[ "$(command -v wafw00f)" == "$HOME/.local/share/nyxstrike-tools/bin/wafw00f" ]] || exit 93
wafw00f --help
''', encoding="utf-8")
        output = self.run_bash(str(fixture))
        self.assertIn("uv not found. Installing via official install script", output)


if __name__ == "__main__":
    unittest.main()
