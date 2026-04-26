"""
tests/test_tool_command_builders.py

Verify that each tool endpoint builds the correct shell command from the
supplied HTTP parameters.

Safety guarantee
────────────────
conftest.py already patches server_core.command_executor.execute_command
at the session level (no real binary fires).  The tests here additionally
patch the *module-local* reference (e.g. server_api.net_scan.nmap.execute_command)
to capture call_args and inspect the exact command string built by each handler.
"""

import pytest
from unittest.mock import patch, MagicMock

_MOCK_RESULT = {"success": True, "output": "mocked", "returncode": 0}


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

_NMAP_PATCH = "server_api.net_scan.nmap.execute_command"


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

_HYDRA_PATCH = "server_api.password_cracking.hydra.execute_command"


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

_HASHCAT_PATCH = "server_api.password_cracking.hashcat.execute_command"


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

_NUCLEI_PATCH = "server_api.vuln_scan.nuclei.execute_command"


class TestNucleiCommandBuilder:
    def test_basic_command(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {"target": "https://example.com"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "nuclei -u https://example.com" in cmd

    def test_requires_target(self, client):
        r = _post(client, "/api/tools/nuclei", {})
        assert r.status_code == 400

    def test_severity_flag(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {
                "target": "https://example.com", "severity": "critical,high"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-severity critical,high" in cmd

    def test_tags_flag(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {
                "target": "https://example.com", "tags": "cve,oast"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-tags cve,oast" in cmd

    def test_template_flag(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {
                "target": "https://example.com", "template": "cves/2021/"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-t cves/2021/" in cmd

    def test_no_severity_when_not_provided(self, client):
        with patch(_NUCLEI_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/nuclei", {"target": "https://example.com"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-severity" not in cmd


# ---------------------------------------------------------------------------
# sqlmap
# ---------------------------------------------------------------------------

_SQLMAP_PATCH = "server_api.web_scan.sqlmap.execute_command"


class TestSqlmapCommandBuilder:
    def test_basic_command(self, client):
        with patch(_SQLMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/sqlmap", {"url": "http://example.com/page?id=1"})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "sqlmap -u http://example.com/page?id=1" in cmd
            assert "--batch" in cmd

    def test_requires_url(self, client):
        r = _post(client, "/api/tools/sqlmap", {})
        assert r.status_code == 400

    def test_data_flag(self, client):
        with patch(_SQLMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/sqlmap", {
                "url": "http://example.com/login",
                "data": "user=admin&pass=test"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "--data=" in cmd
            assert "user=admin&pass=test" in cmd

    def test_additional_args(self, client):
        with patch(_SQLMAP_PATCH, return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, "/api/tools/sqlmap", {
                "url": "http://example.com/?id=1",
                "additional_args": "--level=5 --risk=3"
            })
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "--level=5 --risk=3" in cmd
