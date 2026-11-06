"""
tests/test_tool_command_builders.py

Verify that each tool endpoint builds the correct shell command from the
supplied HTTP parameters.

Safety guarantee
────────────────
conftest.py already patches server_core.command_executor.execute_command
at the session level (no real binary fires).  The tests here additionally
patch the *module-local* reference (e.g. server_api.hydra.execute_command, or
server_api._generic.blueprint_factory.execute_command for ToolSpec-migrated
tools) to capture call_args and inspect the exact command string built by
each handler.
"""

import shlex

import pytest
from unittest.mock import patch, MagicMock

_MOCK_RESULT = {"success": True, "output": "mocked", "returncode": 0}


class TestAutoReconCommandBuilder:
    def test_default_request_uses_supported_flags_and_json_file(self):
        from backend.server_core.tool_specs.recon import SPECS

        spec = next(spec for spec in SPECS if spec.name == "autorecon")
        params = {param.name: param.default for param in spec.params}
        params["target"] = "example.invalid"
        with patch("backend.server_core.tool_specs.recon.os.makedirs") as mkdir:
            command = spec.build_command(params)
        mkdir.assert_called_once_with("/tmp/autorecon", exist_ok=True)
        assert shlex.split(command) == [
            "autorecon", "example.invalid", "-f", "-j",
            "-o", "/tmp/autorecon/autorecon.json",
        ]

    def test_optional_output_and_arguments_can_be_omitted(self):
        from backend.server_core.tool_specs.recon import _autorecon_command

        for optional in ({}, {"output_dir": ""}, {"output_dir": None}):
            with patch("backend.server_core.tool_specs.recon.os.makedirs") as mkdir:
                command = _autorecon_command({"target": "example.invalid", **optional})
            mkdir.assert_not_called()
            assert shlex.split(command) == [
                "autorecon", "example.invalid", "-f", "-j",
            ]

    def test_quoted_paths_and_extra_arguments_preserve_argument_boundaries(self, tmp_path):
        from backend.server_core.tool_specs.recon import _autorecon_command

        output_dir = tmp_path / "recon results" / "nested"
        command = _autorecon_command({
            "target": "example.invalid", "output_dir": str(output_dir),
            "additional_args": '--custom-option "two words"',
            "heartbeat": 60, "timeout": 300,
            "port_scans": "top-100-ports", "service_scans": "custom",
        })
        assert shlex.split(command) == [
            "autorecon", "example.invalid", "-f", "-j",
            "-o", str(output_dir / "autorecon.json"),
            "--custom-option", "two words",
        ]
        assert output_dir.is_dir()

    def test_existing_output_directory_and_results_are_preserved(self, tmp_path):
        from backend.server_core.tool_specs.recon import _autorecon_command

        result = tmp_path / "autorecon.json"
        result.write_text('{"previous": true}')
        params = {"target": "example.invalid", "output_dir": str(tmp_path)}
        _autorecon_command(params)
        _autorecon_command(params)
        assert result.read_text() == '{"previous": true}'


@pytest.fixture(scope="module")
def app():
    import os
    os.environ.setdefault("NYXSTRIKE_API_TOKEN", "")
    from nyxstrike_server import app as _app
    _app.config["TESTING"] = True
    return _app


@pytest.fixture()
def client(app):
    return app.test_client()


def _post(client, url, json_body):
    return client.post(url, json=json_body, content_type="application/json")


# ---------------------------------------------------------------------------
# nmap
# ---------------------------------------------------------------------------

_NMAP_PATCH = "backend.server_api._generic.blueprint_factory.execute_command"


class TestNmapCommandBuilder:
    def test_basic_command(self, client):
        with patch(_NMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nmap", {"target": "10.0.0.1"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert cmd.startswith("nmap ")
            assert "10.0.0.1" in cmd

    def test_requires_target(self, client):
        r = _post(client, "/api/tools/nmap", {})
        assert r.status_code == 400
        assert "error" in r.get_json()

    def test_custom_ports(self, client):
        with patch(_NMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nmap", {"target": "10.0.0.1", "ports": "80,443"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-p 80,443" in cmd

    def test_custom_scan_type(self, client):
        with patch(_NMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nmap", {"target": "10.0.0.1", "scan_type": "-sS"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-sS" in cmd

    def test_default_scan_type_is_scv(self, client):
        with patch(_NMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nmap", {"target": "10.0.0.1"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-sCV" in cmd

    def test_additional_args(self, client):
        with patch(_NMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nmap", {"target": "10.0.0.1", "additional_args": "--open"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "--open" in cmd

    def test_target_appears_in_command(self, client):
        with patch(_NMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nmap", {"target": "192.168.0.0/24"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "192.168.0.0/24" in cmd


# ---------------------------------------------------------------------------
# hydra
# ---------------------------------------------------------------------------

_HYDRA_PATCH = "backend.server_api._generic.blueprint_factory.execute_command"


class TestHydraCommandBuilder:
    def test_basic_command_with_username_password(self, client):
        with patch(_HYDRA_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hydra", {
                "target": "10.0.0.1", "service": "ssh",
                "username": "admin", "password": "password123"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "hydra" in cmd
            assert "-l admin" in cmd
            assert "-p password123" in cmd
            assert "10.0.0.1 ssh" in cmd

    def test_requires_target_and_service(self, client):
        r = _post(client, "/api/tools/hydra", {"username": "admin", "password": "pass"})
        assert r.status_code == 400

    def test_requires_credentials(self, client):
        r = _post(client, "/api/tools/hydra", {"target": "10.0.0.1", "service": "ftp"})
        assert r.status_code == 400

    def test_uses_username_file(self, client):
        with patch(_HYDRA_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hydra", {
                "target": "10.0.0.1", "service": "ssh",
                "username_file": "/wordlists/users.txt",
                "password_file": "/wordlists/pass.txt"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-L /wordlists/users.txt" in cmd
            assert "-P /wordlists/pass.txt" in cmd

    def test_additional_args(self, client):
        with patch(_HYDRA_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hydra", {
                "target": "10.0.0.1", "service": "ftp",
                "username": "root", "password": "toor",
                "additional_args": "-V"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-V" in cmd

    def test_service_appears_at_end(self, client):
        """Service must appear after target so hydra parses correctly."""
        with patch(_HYDRA_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hydra", {
                "target": "192.168.1.1", "service": "http-form-post",
                "username": "admin", "password": "admin"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert cmd.endswith("192.168.1.1 http-form-post")


# ---------------------------------------------------------------------------
# hashcat
# ---------------------------------------------------------------------------

_HASHCAT_PATCH = "backend.server_api._generic.blueprint_factory.execute_command"


class TestHashcatCommandBuilder:
    def test_basic_command(self, client):
        with patch(_HASHCAT_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hashcat", {
                "hash_file": "/tmp/hashes.txt",
                "hash_type": "1000"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "hashcat" in cmd
            assert "-m 1000" in cmd
            assert "/tmp/hashes.txt" in cmd

    def test_requires_hash_file(self, client):
        r = _post(client, "/api/tools/hashcat", {"hash_type": "1000"})
        assert r.status_code == 400

    def test_requires_hash_type(self, client):
        r = _post(client, "/api/tools/hashcat", {"hash_file": "/tmp/h.txt"})
        assert r.status_code == 400

    def test_wordlist_mode(self, client):
        with patch(_HASHCAT_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hashcat", {
                "hash_file": "/tmp/h.txt", "hash_type": "0",
                "attack_mode": "0", "wordlist": "/wordlists/rockyou.txt"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-a 0" in cmd
            assert "/wordlists/rockyou.txt" in cmd

    def test_mask_mode(self, client):
        with patch(_HASHCAT_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/hashcat", {
                "hash_file": "/tmp/h.txt", "hash_type": "0",
                "attack_mode": "3", "mask": "?a?a?a?a"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-a 3" in cmd
            assert "?a?a?a?a" in cmd


# ---------------------------------------------------------------------------
# nuclei
# ---------------------------------------------------------------------------

_NUCLEI_PATCH = "backend.server_api._generic.blueprint_factory.execute_command"


class TestNucleiCommandBuilder:
    def test_basic_command(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {"target": "https://example.invalid"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "nuclei -u https://example.invalid" in cmd

    def test_requires_target(self, client):
        r = _post(client, "/api/tools/nuclei", {})
        assert r.status_code == 400

    def test_severity_flag(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {
                "target": "https://example.invalid", "severity": "critical,high"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-severity critical,high" in cmd

    def test_tags_flag(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {
                "target": "https://example.invalid", "tags": "cve,oast"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-tags cve,oast" in cmd

    def test_template_flag(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {
                "target": "https://example.invalid", "template": "cves/2021/"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-t cves/2021/" in cmd

    def test_no_severity_when_not_provided(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {"target": "https://example.invalid"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-severity" not in cmd


# ---------------------------------------------------------------------------
# sqlmap
# ---------------------------------------------------------------------------

_SQLMAP_PATCH = "backend.server_api._generic.blueprint_factory.execute_command"


class TestSqlmapCommandBuilder:
    def test_basic_command(self, client):
        with patch(_SQLMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/sqlmap", {"url": "http://example.invalid/page?id=1"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            tokens = shlex.split(cmd)
            assert tokens[:2] == ["sqlmap", "-u"]
            assert tokens[2] == "http://example.invalid/page?id=1"
            assert "--batch" in tokens

    def test_requires_url(self, client):
        r = _post(client, "/api/tools/sqlmap", {})
        assert r.status_code == 400

    def test_data_flag(self, client):
        with patch(_SQLMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/sqlmap", {
                "url": "http://example.invalid/login",
                "data": "user=admin&pass=test"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "--data=" in cmd
            assert "user=admin&pass=test" in cmd

    def test_additional_args(self, client):
        with patch(_SQLMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/sqlmap", {
                "url": "http://example.invalid/?id=1",
                "additional_args": "--level=5 --risk=3"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "--level=5 --risk=3" in cmd
