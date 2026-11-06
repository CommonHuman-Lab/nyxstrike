"""Exercise angr's missing C++ string header with the project's build flags."""

from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tempfile
import unittest

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None


ROOT = Path(__file__).resolve().parents[1]
COMPILER = shutil.which("clang++")


@unittest.skipIf(tomllib is None or COMPILER is None, "Requires TOML reader and clang++")
class AngrBuildTests(unittest.TestCase):
    def test_forward_declared_string_compiles_with_angr_build_environment(self):
        # iosfwd declares std::string without defining it, matching the failure
        # in angr's source with the older libc++ headers used on Intel Macs.
        source = '#include <iosfwd>\nint main() { std::string name("angr"); return name.empty(); }\n'
        config = tomllib.loads((ROOT / "pyproject.toml").read_text())
        build_env = config["tool"]["uv"].get("extra-build-variables", {}).get("angr", {})
        flags = shlex.split(build_env.get("CXXFLAGS", ""))
        architectures = ("arm64", "x86_64") if platform.system() == "Darwin" else (None,)
        with tempfile.TemporaryDirectory(prefix="nyxstrike-angr-compile-") as directory:
            filename = Path(directory) / "string.cpp"
            filename.write_text(source)
            for architecture in architectures:
                with self.subTest(architecture=architecture):
                    command = [COMPILER, "-std=c++11", "-fsyntax-only", str(filename)]
                    if architecture:
                        command.extend(["-arch", architecture])
                    result = subprocess.run(
                        command + flags, capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
