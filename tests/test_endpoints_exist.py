"""
tests/test_endpoints_exist.py

Verify that every registered API route exists (returns non-404).
No real tools are executed — execute_command is mocked throughout.
"""

import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Stub out execute_command before the app is imported so that no blueprint
# module ever tries to spawn a real process.
# ---------------------------------------------------------------------------
_MOCK_RESULT = {"success": True, "output": "mocked", "returncode": 0}

_EXECUTE_PATCH = patch(
    "server_core.command_executor.execute_command",
    return_value=_MOCK_RESULT,
)
_EXECUTE_PATCH.start()

# Also patch the singletons used by system_monitoring so they don't call real
# processes during module initialisation.
_CACHE_MOCK = MagicMock()
_CACHE_MOCK.get_stats.return_value = {}
_CACHE_MOCK.clear.return_value = None

_TELEMETRY_MOCK = MagicMock()
_TELEMETRY_MOCK.get_stats.return_value = {}
_TELEMETRY_MOCK.stats = {"start_time": 0.0}

_SINGLETONS_PATCH = patch(
    "server_core.singletons.cache", _CACHE_MOCK
)
_SINGLETONS_PATCH.start()

_TELEMETRY_PATCH = patch(
    "server_core.singletons.telemetry", _TELEMETRY_MOCK
)
_TELEMETRY_PATCH.start()

# Now it is safe to import the Flask app.
from nyxstrike_server import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    # Disable bearer-auth so we never need a token in tests.
    app.config["NYXSTRIKE_API_TOKEN"] = None
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helper — make a minimal valid JSON body for POST endpoints so that handlers
# that call request.json don't blow up with a 400 before we even check 404.
# ---------------------------------------------------------------------------
_MINIMAL_BODY: dict = {}


def _post(client, path: str):
    return client.post(path, json=_MINIMAL_BODY)


def _get(client, path: str):
    return client.get(path)


# ---------------------------------------------------------------------------
# We intentionally accept any status code that is NOT 404 (or 405 for a
# wrong-method probe) as proof that the route is registered.  Handlers may
# legitimately return 400 (missing required param), 500, etc. — that is fine.
#
# assert_route_exists   — strict: 404 means the route is missing.
# assert_route_exists_or_empty — lenient: 404 is allowed when a handler may
#   legitimately return 404 for an unknown resource (e.g. unknown PID / task
#   ID).  We distinguish "route registered but resource not found" from "route
#   not registered" by checking that a 404 carries a JSON body (Flask's own
#   default 404 page is HTML).
# ---------------------------------------------------------------------------
def assert_route_exists(response, path: str):
    assert response.status_code != 404, (
        f"Route {path!r} returned 404 — it appears to be unregistered."
    )


def assert_route_exists_or_empty(response, path: str):
    """For parametric routes that return 404 when the resource doesn't exist.

    A Flask-generated 404 (route not found) returns an HTML page.
    A handler-generated 404 returns JSON.  We accept the latter.
    """
    if response.status_code == 404:
        content_type = response.content_type or ""
        assert "application/json" in content_type, (
            f"Route {path!r} returned a non-JSON 404 — it appears to be unregistered. "
            f"Content-Type: {content_type!r}"
        )


# ===========================================================================
# System / OPS
# ===========================================================================

class TestSystemOps:
    def test_ping(self, client):
        r = _get(client, "/ping")
        assert_route_exists(r, "/ping")

    def test_health(self, client):
        r = _get(client, "/health")
        assert_route_exists(r, "/health")

    def test_api_command(self, client):
        r = _post(client, "/api/command")
        assert_route_exists(r, "/api/command")

    def test_cache_stats(self, client):
        r = _get(client, "/api/cache/stats")
        assert_route_exists(r, "/api/cache/stats")

    def test_cache_clear(self, client):
        r = _post(client, "/api/cache/clear")
        assert_route_exists(r, "/api/cache/clear")

    def test_telemetry(self, client):
        r = _get(client, "/api/telemetry")
        assert_route_exists(r, "/api/telemetry")


# ===========================================================================
# Files & Payloads
# ===========================================================================

class TestFilesAndPayloads:
    def test_files_create(self, client):
        r = _post(client, "/api/files/create")
        assert_route_exists(r, "/api/files/create")

    def test_files_modify(self, client):
        r = _post(client, "/api/files/modify")
        assert_route_exists(r, "/api/files/modify")

    def test_files_delete(self, client):
        r = client.delete("/api/files/delete", json=_MINIMAL_BODY)
        assert_route_exists(r, "/api/files/delete")

    def test_files_list(self, client):
        r = _get(client, "/api/files/list")
        assert_route_exists(r, "/api/files/list")

    def test_payloads_generate(self, client):
        r = _post(client, "/api/payloads/generate")
        assert_route_exists(r, "/api/payloads/generate")


# ===========================================================================
# Process management
# ===========================================================================

class TestProcessManagement:
    def test_processes_list(self, client):
        r = _get(client, "/api/processes/list")
        assert_route_exists(r, "/api/processes/list")

    def test_processes_status(self, client):
        # Handler returns 404 JSON when PID not found — route is still registered.
        r = _get(client, "/api/processes/status/1")
        assert_route_exists_or_empty(r, "/api/processes/status/<pid>")

    def test_processes_terminate(self, client):
        r = _post(client, "/api/processes/terminate/1")
        assert_route_exists_or_empty(r, "/api/processes/terminate/<pid>")

    def test_processes_pause(self, client):
        r = _post(client, "/api/processes/pause/1")
        assert_route_exists_or_empty(r, "/api/processes/pause/<pid>")

    def test_processes_resume(self, client):
        r = _post(client, "/api/processes/resume/1")
        assert_route_exists_or_empty(r, "/api/processes/resume/<pid>")

    def test_processes_dashboard(self, client):
        r = _get(client, "/api/processes/dashboard")
        assert_route_exists(r, "/api/processes/dashboard")

    def test_process_execute_async(self, client):
        r = _post(client, "/api/process/execute-async")
        assert_route_exists(r, "/api/process/execute-async")

    def test_process_get_task_result(self, client):
        # Handler returns 404 JSON when task ID not found — route is still registered.
        r = _get(client, "/api/process/get-task-result/abc123")
        assert_route_exists_or_empty(r, "/api/process/get-task-result/<task_id>")

    def test_process_pool_stats(self, client):
        r = _get(client, "/api/process/pool-stats")
        assert_route_exists(r, "/api/process/pool-stats")

    def test_process_cache_stats(self, client):
        r = _get(client, "/api/process/cache-stats")
        assert_route_exists(r, "/api/process/cache-stats")

    def test_process_clear_cache(self, client):
        r = _post(client, "/api/process/clear-cache")
        assert_route_exists(r, "/api/process/clear-cache")

    def test_process_resource_usage(self, client):
        r = _get(client, "/api/process/resource-usage")
        assert_route_exists(r, "/api/process/resource-usage")

    def test_process_performance_dashboard(self, client):
        r = _get(client, "/api/process/performance-dashboard")
        assert_route_exists(r, "/api/process/performance-dashboard")

    def test_process_terminate_gracefully(self, client):
        r = _post(client, "/api/process/terminate-gracefully/1")
        assert_route_exists(r, "/api/process/terminate-gracefully/<pid>")

    def test_process_auto_scaling(self, client):
        r = _post(client, "/api/process/auto-scaling")
        assert_route_exists(r, "/api/process/auto-scaling")

    def test_process_scale_pool(self, client):
        r = _post(client, "/api/process/scale-pool")
        assert_route_exists(r, "/api/process/scale-pool")

    def test_process_health_check(self, client):
        r = _get(client, "/api/process/health-check")
        assert_route_exists(r, "/api/process/health-check")


# ===========================================================================
# Wordlists
# ===========================================================================

class TestWordlists:
    def test_wordlists_list(self, client):
        r = _get(client, "/api/wordlists")
        assert_route_exists(r, "/api/wordlists")

    def test_wordlists_get(self, client):
        # Handler returns 404 JSON when wordlist ID not found — route is still registered.
        r = _get(client, "/api/wordlists/rockyou")
        assert_route_exists_or_empty(r, "/api/wordlists/<wordlist_id>")

    def test_wordlists_path(self, client):
        r = _get(client, "/api/wordlists/rockyou/path")
        assert_route_exists_or_empty(r, "/api/wordlists/<wordlist_id>/path")

    def test_wordlists_bestmatch(self, client):
        r = _post(client, "/api/wordlists/bestmatch")
        assert_route_exists(r, "/api/wordlists/bestmatch")

    def test_wordlists_post(self, client):
        r = _post(client, "/api/wordlists/rockyou")
        assert_route_exists(r, "/api/wordlists/<wordlist_id> POST")

    def test_wordlists_delete(self, client):
        r = client.delete("/api/wordlists/rockyou")
        assert_route_exists(r, "/api/wordlists/<wordlist_id> DELETE")


# ===========================================================================
# Settings
# ===========================================================================

class TestSettings:
    def test_settings_get(self, client):
        r = _get(client, "/api/settings")
        assert_route_exists(r, "/api/settings")

    def test_settings_patch(self, client):
        r = client.patch("/api/settings", json={"runtime": {"cache_ttl": 60}})
        assert_route_exists(r, "/api/settings PATCH")

    def test_settings_wordlists_patch(self, client):
        r = client.patch("/api/settings/wordlists", json={"wordlists": []})
        assert_route_exists(r, "/api/settings/wordlists PATCH")


# ===========================================================================
# Python Environment
# ===========================================================================

class TestPythonEnv:
    def test_python_install(self, client):
        r = _post(client, "/api/python/install")
        assert_route_exists(r, "/api/python/install")

    def test_python_execute(self, client):
        r = _post(client, "/api/python/execute")
        assert_route_exists(r, "/api/python/execute")


# ===========================================================================
# Visual
# ===========================================================================

class TestVisual:
    def test_vulnerability_card(self, client):
        r = _post(client, "/api/visual/vulnerability-card")
        assert_route_exists(r, "/api/visual/vulnerability-card")

    def test_summary_report(self, client):
        r = _post(client, "/api/visual/summary-report")
        assert_route_exists(r, "/api/visual/summary-report")

    def test_tool_output(self, client):
        r = _post(client, "/api/visual/tool-output")
        assert_route_exists(r, "/api/visual/tool-output")


# ===========================================================================
# Auto Install
# ===========================================================================

class TestAutoInstall:
    def test_auto_install_missing_apt(self, client):
        r = _post(client, "/api/tools/auto-install-missing-apt")
        assert_route_exists(r, "/api/tools/auto-install-missing-apt")


# ===========================================================================
# Database
# ===========================================================================

class TestDatabase:
    def test_mysql(self, client):
        r = _post(client, "/api/tools/mysql")
        assert_route_exists(r, "/api/tools/mysql")

    def test_sqlite(self, client):
        r = _post(client, "/api/tools/sqlite")
        assert_route_exists(r, "/api/tools/sqlite")

    def test_postgresql(self, client):
        r = _post(client, "/api/tools/postgresql")
        assert_route_exists(r, "/api/tools/postgresql")


# ===========================================================================
# Network Scanning
# ===========================================================================

class TestNetworkScanning:
    def test_nmap(self, client):
        r = _post(client, "/api/tools/nmap")
        assert_route_exists(r, "/api/tools/nmap")

    def test_nmap_advanced(self, client):
        r = _post(client, "/api/tools/nmap-advanced")
        assert_route_exists(r, "/api/tools/nmap-advanced")

    def test_masscan(self, client):
        r = _post(client, "/api/tools/masscan")
        assert_route_exists(r, "/api/tools/masscan")

    def test_rustscan(self, client):
        r = _post(client, "/api/tools/rustscan")
        assert_route_exists(r, "/api/tools/rustscan")

    def test_arp_scan(self, client):
        r = _post(client, "/api/tools/arp-scan")
        assert_route_exists(r, "/api/tools/arp-scan")


# ===========================================================================
# SMB / Network Enumeration
# ===========================================================================

class TestSMBEnum:
    def test_enum4linux(self, client):
        r = _post(client, "/api/tools/enum4linux")
        assert_route_exists(r, "/api/tools/enum4linux")

    def test_enum4linux_ng(self, client):
        r = _post(client, "/api/tools/enum4linux-ng")
        assert_route_exists(r, "/api/tools/enum4linux-ng")

    def test_smbmap(self, client):
        r = _post(client, "/api/tools/smbmap")
        assert_route_exists(r, "/api/tools/smbmap")

    def test_nbtscan(self, client):
        r = _post(client, "/api/tools/nbtscan")
        assert_route_exists(r, "/api/tools/nbtscan")

    def test_netexec(self, client):
        r = _post(client, "/api/tools/netexec")
        assert_route_exists(r, "/api/tools/netexec")

    def test_rpcclient(self, client):
        r = _post(client, "/api/tools/rpcclient")
        assert_route_exists(r, "/api/tools/rpcclient")


# ===========================================================================
# Network Lookup
# ===========================================================================

class TestNetworkLookup:
    def test_whois(self, client):
        r = _post(client, "/api/tools/whois")
        assert_route_exists(r, "/api/tools/whois")


# ===========================================================================
# Reconnaissance
# ===========================================================================

class TestRecon:
    def test_amass(self, client):
        r = _post(client, "/api/tools/amass")
        assert_route_exists(r, "/api/tools/amass")

    def test_subfinder(self, client):
        r = _post(client, "/api/tools/subfinder")
        assert_route_exists(r, "/api/tools/subfinder")

    def test_assetfinder(self, client):
        r = _post(client, "/api/tools/assetfinder")
        assert_route_exists(r, "/api/tools/assetfinder")

    def test_shuffledns(self, client):
        r = _post(client, "/api/tools/shuffledns")
        assert_route_exists(r, "/api/tools/shuffledns")

    def test_massdns(self, client):
        r = _post(client, "/api/tools/massdns")
        assert_route_exists(r, "/api/tools/massdns")

    def test_autorecon(self, client):
        r = _post(client, "/api/tools/autorecon")
        assert_route_exists(r, "/api/tools/autorecon")

    def test_theharvester(self, client):
        r = _post(client, "/api/tools/recon/theharvester")
        assert_route_exists(r, "/api/tools/recon/theharvester")


# ===========================================================================
# Recon Bot
# ===========================================================================

class TestReconBot:
    def test_bbot(self, client):
        r = _post(client, "/api/bot/bbot")
        assert_route_exists(r, "/api/bot/bbot")


# ===========================================================================
# DNS Enumeration
# ===========================================================================

class TestDNSEnum:
    def test_fierce(self, client):
        r = _post(client, "/api/tools/fierce")
        assert_route_exists(r, "/api/tools/fierce")

    def test_dnsenum(self, client):
        r = _post(client, "/api/tools/dnsenum")
        assert_route_exists(r, "/api/tools/dnsenum")


# ===========================================================================
# Web Fuzzing / Directory Scanning
# ===========================================================================

class TestWebFuzzing:
    def test_gobuster(self, client):
        r = _post(client, "/api/tools/gobuster")
        assert_route_exists(r, "/api/tools/gobuster")

    def test_ffuf(self, client):
        r = _post(client, "/api/tools/ffuf")
        assert_route_exists(r, "/api/tools/ffuf")

    def test_feroxbuster(self, client):
        r = _post(client, "/api/tools/feroxbuster")
        assert_route_exists(r, "/api/tools/feroxbuster")

    def test_dirb(self, client):
        r = _post(client, "/api/tools/dirb")
        assert_route_exists(r, "/api/tools/dirb")

    def test_dirsearch(self, client):
        r = _post(client, "/api/tools/dirsearch")
        assert_route_exists(r, "/api/tools/dirsearch")

    def test_wfuzz(self, client):
        r = _post(client, "/api/tools/wfuzz")
        assert_route_exists(r, "/api/tools/wfuzz")

    def test_dotdotpwn(self, client):
        r = _post(client, "/api/tools/dotdotpwn")
        assert_route_exists(r, "/api/tools/dotdotpwn")


# ===========================================================================
# Web Scanning / Vulnerability
# ===========================================================================

class TestWebScanning:
    def test_nuclei(self, client):
        r = _post(client, "/api/tools/nuclei")
        assert_route_exists(r, "/api/tools/nuclei")

    def test_nikto(self, client):
        r = _post(client, "/api/tools/nikto")
        assert_route_exists(r, "/api/tools/nikto")

    def test_sqlmap(self, client):
        r = _post(client, "/api/tools/sqlmap")
        assert_route_exists(r, "/api/tools/sqlmap")

    def test_dalfox(self, client):
        r = _post(client, "/api/tools/dalfox")
        assert_route_exists(r, "/api/tools/dalfox")

    def test_xsser(self, client):
        r = _post(client, "/api/tools/xsser")
        assert_route_exists(r, "/api/tools/xsser")

    def test_jaeles(self, client):
        r = _post(client, "/api/tools/jaeles")
        assert_route_exists(r, "/api/tools/jaeles")

    def test_wpscan(self, client):
        r = _post(client, "/api/tools/wpscan")
        assert_route_exists(r, "/api/tools/wpscan")

    def test_burpsuite_alternative(self, client):
        r = _post(client, "/api/tools/burpsuite-alternative")
        assert_route_exists(r, "/api/tools/burpsuite-alternative")

    def test_zap(self, client):
        r = _post(client, "/api/tools/zap")
        assert_route_exists(r, "/api/tools/zap")


# ===========================================================================
# Web Crawling
# ===========================================================================

class TestWebCrawling:
    def test_katana(self, client):
        r = _post(client, "/api/tools/katana")
        assert_route_exists(r, "/api/tools/katana")

    def test_hakrawler(self, client):
        r = _post(client, "/api/tools/hakrawler")
        assert_route_exists(r, "/api/tools/hakrawler")

    def test_gospider(self, client):
        r = _post(client, "/api/tools/gospider")
        assert_route_exists(r, "/api/tools/gospider")


# ===========================================================================
# Web Probing
# ===========================================================================

class TestWebProbing:
    def test_httpx(self, client):
        r = _post(client, "/api/tools/httpx")
        assert_route_exists(r, "/api/tools/httpx")

    def test_testssl(self, client):
        r = _post(client, "/api/tools/testssl")
        assert_route_exists(r, "/api/tools/testssl")


# ===========================================================================
# Web Framework Helpers
# ===========================================================================

class TestWebFramework:
    def test_http_framework(self, client):
        r = _post(client, "/api/tools/http-framework")
        assert_route_exists(r, "/api/tools/http-framework")

    def test_browser_agent(self, client):
        r = _post(client, "/api/tools/browser-agent")
        assert_route_exists(r, "/api/tools/browser-agent")


# ===========================================================================
# URL Recon & Filtering
# ===========================================================================

class TestURLRecon:
    def test_gau(self, client):
        r = _post(client, "/api/tools/gau")
        assert_route_exists(r, "/api/tools/gau")

    def test_waybackurls(self, client):
        r = _post(client, "/api/tools/waybackurls")
        assert_route_exists(r, "/api/tools/waybackurls")

    def test_uro(self, client):
        r = _post(client, "/api/tools/uro")
        assert_route_exists(r, "/api/tools/uro")


# ===========================================================================
# Parameter Discovery & Fuzzing
# ===========================================================================

class TestParamDiscovery:
    def test_arjun(self, client):
        r = _post(client, "/api/tools/arjun")
        assert_route_exists(r, "/api/tools/arjun")

    def test_paramspider(self, client):
        r = _post(client, "/api/tools/paramspider")
        assert_route_exists(r, "/api/tools/paramspider")

    def test_x8(self, client):
        r = _post(client, "/api/tools/x8")
        assert_route_exists(r, "/api/tools/x8")

    def test_qsreplace(self, client):
        r = _post(client, "/api/tools/qsreplace")
        assert_route_exists(r, "/api/tools/qsreplace")


# ===========================================================================
# WAF Detection
# ===========================================================================

class TestWAFDetection:
    def test_wafw00f(self, client):
        r = _post(client, "/api/tools/wafw00f")
        assert_route_exists(r, "/api/tools/wafw00f")


# ===========================================================================
# API Fuzzing & Scanning
# ===========================================================================

class TestAPIFuzzingAndScanning:
    def test_api_fuzzer(self, client):
        r = _post(client, "/api/tools/api_fuzzer")
        assert_route_exists(r, "/api/tools/api_fuzzer")

    def test_graphql_scanner(self, client):
        r = _post(client, "/api/tools/graphql_scanner")
        assert_route_exists(r, "/api/tools/graphql_scanner")

    def test_jwt_analyzer(self, client):
        r = _post(client, "/api/tools/jwt_analyzer")
        assert_route_exists(r, "/api/tools/jwt_analyzer")

    def test_api_schema_analyzer(self, client):
        r = _post(client, "/api/tools/api_schema_analyzer")
        assert_route_exists(r, "/api/tools/api_schema_analyzer")


# ===========================================================================
# Password Cracking
# ===========================================================================

class TestPasswordCracking:
    def test_hydra(self, client):
        r = _post(client, "/api/tools/hydra")
        assert_route_exists(r, "/api/tools/hydra")

    def test_hashcat(self, client):
        r = _post(client, "/api/tools/hashcat")
        assert_route_exists(r, "/api/tools/hashcat")

    def test_john(self, client):
        r = _post(client, "/api/tools/john")
        assert_route_exists(r, "/api/tools/john")

    def test_medusa(self, client):
        r = _post(client, "/api/tools/medusa")
        assert_route_exists(r, "/api/tools/medusa")

    def test_patator(self, client):
        r = _post(client, "/api/tools/patator")
        assert_route_exists(r, "/api/tools/patator")

    def test_ophcrack(self, client):
        r = _post(client, "/api/tools/password-cracking/ophcrack")
        assert_route_exists(r, "/api/tools/password-cracking/ophcrack")

    def test_hashid(self, client):
        r = _post(client, "/api/tools/password_cracking/hashid")
        assert_route_exists(r, "/api/tools/password_cracking/hashid")

    def test_aircrack_ng_password(self, client):
        r = _post(client, "/api/tools/password_cracking/aircrack_ng")
        assert_route_exists(r, "/api/tools/password_cracking/aircrack_ng")


# ===========================================================================
# Exploitation
# ===========================================================================

class TestExploitation:
    def test_metasploit(self, client):
        r = _post(client, "/api/tools/metasploit")
        assert_route_exists(r, "/api/tools/metasploit")

    def test_msfvenom(self, client):
        r = _post(client, "/api/tools/msfvenom")
        assert_route_exists(r, "/api/tools/msfvenom")

    def test_exploit_db(self, client):
        r = _post(client, "/api/tools/exploit_framework/exploit_db")
        assert_route_exists(r, "/api/tools/exploit_framework/exploit_db")

    def test_pwninit(self, client):
        r = _post(client, "/api/tools/pwninit")
        assert_route_exists(r, "/api/tools/pwninit")

    def test_pwntools(self, client):
        r = _post(client, "/api/tools/pwntools")
        assert_route_exists(r, "/api/tools/pwntools")


# ===========================================================================
# Binary Analysis
# ===========================================================================

class TestBinaryAnalysis:
    def test_checksec(self, client):
        r = _post(client, "/api/tools/checksec")
        assert_route_exists(r, "/api/tools/checksec")

    def test_binwalk(self, client):
        r = _post(client, "/api/tools/binwalk")
        assert_route_exists(r, "/api/tools/binwalk")

    def test_strings(self, client):
        r = _post(client, "/api/tools/strings")
        assert_route_exists(r, "/api/tools/strings")

    def test_ropgadget(self, client):
        r = _post(client, "/api/tools/ropgadget")
        assert_route_exists(r, "/api/tools/ropgadget")

    def test_radare2(self, client):
        r = _post(client, "/api/tools/radare2")
        assert_route_exists(r, "/api/tools/radare2")

    def test_autopsy(self, client):
        r = _post(client, "/api/tools/binary_analysis/autopsy")
        assert_route_exists(r, "/api/tools/binary_analysis/autopsy")

    def test_xxd(self, client):
        r = _post(client, "/api/tools/xxd")
        assert_route_exists(r, "/api/tools/xxd")

    def test_objdump(self, client):
        r = _post(client, "/api/tools/objdump")
        assert_route_exists(r, "/api/tools/objdump")

    def test_ghidra(self, client):
        r = _post(client, "/api/tools/ghidra")
        assert_route_exists(r, "/api/tools/ghidra")

    def test_one_gadget(self, client):
        r = _post(client, "/api/tools/one-gadget")
        assert_route_exists(r, "/api/tools/one-gadget")

    def test_libc_database(self, client):
        r = _post(client, "/api/tools/libc-database")
        assert_route_exists(r, "/api/tools/libc-database")

    def test_angr(self, client):
        r = _post(client, "/api/tools/angr")
        assert_route_exists(r, "/api/tools/angr")

    def test_ropper(self, client):
        r = _post(client, "/api/tools/ropper")
        assert_route_exists(r, "/api/tools/ropper")

    def test_gdb(self, client):
        r = _post(client, "/api/tools/gdb")
        assert_route_exists(r, "/api/tools/gdb")

    def test_gdb_peda(self, client):
        r = _post(client, "/api/tools/gdb-peda")
        assert_route_exists(r, "/api/tools/gdb-peda")


# ===========================================================================
# Cloud, Container, K8s
# ===========================================================================

class TestCloudContainerK8s:
    def test_prowler(self, client):
        r = _post(client, "/api/tools/prowler")
        assert_route_exists(r, "/api/tools/prowler")

    def test_scout_suite(self, client):
        r = _post(client, "/api/tools/scout-suite")
        assert_route_exists(r, "/api/tools/scout-suite")

    def test_trivy(self, client):
        r = _post(client, "/api/tools/trivy")
        assert_route_exists(r, "/api/tools/trivy")

    def test_docker_bench_security(self, client):
        r = _post(client, "/api/tools/docker-bench-security")
        assert_route_exists(r, "/api/tools/docker-bench-security")

    def test_clair(self, client):
        r = _post(client, "/api/tools/clair")
        assert_route_exists(r, "/api/tools/clair")

    def test_cloudmapper(self, client):
        r = _post(client, "/api/tools/cloudmapper")
        assert_route_exists(r, "/api/tools/cloudmapper")

    def test_pacu(self, client):
        r = _post(client, "/api/tools/pacu")
        assert_route_exists(r, "/api/tools/pacu")

    def test_kube_hunter(self, client):
        r = _post(client, "/api/tools/kube-hunter")
        assert_route_exists(r, "/api/tools/kube-hunter")

    def test_kube_bench(self, client):
        r = _post(client, "/api/tools/kube-bench")
        assert_route_exists(r, "/api/tools/kube-bench")

    def test_falco(self, client):
        r = _post(client, "/api/tools/falco")
        assert_route_exists(r, "/api/tools/falco")

    def test_checkov(self, client):
        r = _post(client, "/api/tools/checkov")
        assert_route_exists(r, "/api/tools/checkov")

    def test_terrascan(self, client):
        r = _post(client, "/api/tools/terrascan")
        assert_route_exists(r, "/api/tools/terrascan")


# ===========================================================================
# Credential Harvesting
# ===========================================================================

class TestCredentialHarvesting:
    def test_responder(self, client):
        r = _post(client, "/api/tools/responder")
        assert_route_exists(r, "/api/tools/responder")


# ===========================================================================
# Forensics / Steganography / Metadata
# ===========================================================================

class TestForensics:
    def test_volatility(self, client):
        r = _post(client, "/api/tools/volatility")
        assert_route_exists(r, "/api/tools/volatility")

    def test_volatility3(self, client):
        r = _post(client, "/api/tools/volatility3")
        assert_route_exists(r, "/api/tools/volatility3")

    def test_foremost(self, client):
        r = _post(client, "/api/tools/foremost")
        assert_route_exists(r, "/api/tools/foremost")

    def test_steghide(self, client):
        r = _post(client, "/api/tools/steghide")
        assert_route_exists(r, "/api/tools/steghide")

    def test_exiftool(self, client):
        r = _post(client, "/api/tools/exiftool")
        assert_route_exists(r, "/api/tools/exiftool")


# ===========================================================================
# Crypto / Data
# ===========================================================================

class TestCryptoData:
    def test_hashpump(self, client):
        r = _post(client, "/api/tools/hashpump")
        assert_route_exists(r, "/api/tools/hashpump")

    def test_anew(self, client):
        r = _post(client, "/api/tools/anew")
        assert_route_exists(r, "/api/tools/anew")

    def test_hurl(self, client):
        r = _post(client, "/api/tools/data_processing/hurl")
        assert_route_exists(r, "/api/tools/data_processing/hurl")


# ===========================================================================
# Wi-Fi Pentesting
# ===========================================================================

class TestWiFiPentest:
    def test_aircrack_ng(self, client):
        r = _post(client, "/api/tools/wifi_pentest/aircrack_ng")
        assert_route_exists(r, "/api/tools/wifi_pentest/aircrack_ng")

    def test_airmon_ng(self, client):
        r = _post(client, "/api/tools/wifi_pentest/airmon_ng")
        assert_route_exists(r, "/api/tools/wifi_pentest/airmon_ng")

    def test_airodump_ng(self, client):
        r = _post(client, "/api/tools/wifi_pentest/airodump_ng")
        assert_route_exists(r, "/api/tools/wifi_pentest/airodump_ng")

    def test_aireplay_ng(self, client):
        r = _post(client, "/api/tools/wifi_pentest/aireplay_ng")
        assert_route_exists(r, "/api/tools/wifi_pentest/aireplay_ng")

    def test_airbase_ng(self, client):
        r = _post(client, "/api/tools/wifi_pentest/airbase_ng")
        assert_route_exists(r, "/api/tools/wifi_pentest/airbase_ng")

    def test_airdecap_ng(self, client):
        r = _post(client, "/api/tools/wifi_pentest/airdecap_ng")
        assert_route_exists(r, "/api/tools/wifi_pentest/airdecap_ng")

    def test_hcxpcapngtool(self, client):
        r = _post(client, "/api/tools/wifi_pentest/hcxpcapngtool")
        assert_route_exists(r, "/api/tools/wifi_pentest/hcxpcapngtool")

    def test_hcxdumptool(self, client):
        r = _post(client, "/api/tools/wifi_pentest/hcxdumptool")
        assert_route_exists(r, "/api/tools/wifi_pentest/hcxdumptool")

    def test_eaphammer(self, client):
        r = _post(client, "/api/tools/wifi_pentest/eaphammer")
        assert_route_exists(r, "/api/tools/wifi_pentest/eaphammer")

    def test_wifite2(self, client):
        r = _post(client, "/api/tools/wifi_pentest/wifite2")
        assert_route_exists(r, "/api/tools/wifi_pentest/wifite2")

    def test_bettercap_wifi(self, client):
        r = _post(client, "/api/tools/wifi_pentest/bettercap_wifi")
        assert_route_exists(r, "/api/tools/wifi_pentest/bettercap_wifi")

    def test_mdk4(self, client):
        r = _post(client, "/api/tools/wifi_pentest/mdk4")
        assert_route_exists(r, "/api/tools/wifi_pentest/mdk4")


# ===========================================================================
# Intelligence & Vulnerability
# ===========================================================================

class TestIntelligence:
    def test_find_best_wordlist(self, client):
        r = _post(client, "/api/intelligence/find-best-wordlist")
        assert_route_exists(r, "/api/intelligence/find-best-wordlist")

    def test_analyze_target(self, client):
        r = _post(client, "/api/intelligence/analyze-target")
        assert_route_exists(r, "/api/intelligence/analyze-target")

    def test_select_tools(self, client):
        r = _post(client, "/api/intelligence/select-tools")
        assert_route_exists(r, "/api/intelligence/select-tools")

    def test_compare_planners(self, client):
        r = _post(client, "/api/intelligence/compare-planners")
        assert_route_exists(r, "/api/intelligence/compare-planners")

    def test_classify_task(self, client):
        r = _post(client, "/api/intelligence/classify-task")
        assert_route_exists(r, "/api/intelligence/classify-task")

    def test_optimize_parameters(self, client):
        r = _post(client, "/api/intelligence/optimize-parameters")
        assert_route_exists(r, "/api/intelligence/optimize-parameters")

    def test_create_attack_chain(self, client):
        r = _post(client, "/api/intelligence/create-attack-chain")
        assert_route_exists(r, "/api/intelligence/create-attack-chain")

    def test_preview_attack_chain(self, client):
        r = _post(client, "/api/intelligence/preview-attack-chain")
        assert_route_exists(r, "/api/intelligence/preview-attack-chain")

    def test_smart_scan(self, client):
        r = _post(client, "/api/intelligence/smart-scan")
        assert_route_exists(r, "/api/intelligence/smart-scan")

    def test_technology_detection(self, client):
        r = _post(client, "/api/intelligence/technology-detection")
        assert_route_exists(r, "/api/intelligence/technology-detection")

    def test_cve_monitor(self, client):
        r = _post(client, "/api/vuln-intel/cve-monitor")
        assert_route_exists(r, "/api/vuln-intel/cve-monitor")

    def test_exploit_generate(self, client):
        r = _post(client, "/api/vuln-intel/exploit-generate")
        assert_route_exists(r, "/api/vuln-intel/exploit-generate")

    def test_attack_chains(self, client):
        r = _post(client, "/api/vuln-intel/attack-chains")
        assert_route_exists(r, "/api/vuln-intel/attack-chains")

    def test_threat_feeds(self, client):
        r = _post(client, "/api/vuln-intel/threat-feeds")
        assert_route_exists(r, "/api/vuln-intel/threat-feeds")

    def test_zero_day_research(self, client):
        r = _post(client, "/api/vuln-intel/zero-day-research")
        assert_route_exists(r, "/api/vuln-intel/zero-day-research")


# ===========================================================================
# Error Handling
# ===========================================================================

class TestErrorHandling:
    def test_statistics(self, client):
        r = _get(client, "/api/error-handling/statistics")
        assert_route_exists(r, "/api/error-handling/statistics")

    def test_fallback_chains(self, client):
        r = _get(client, "/api/error-handling/fallback-chains")
        assert_route_exists(r, "/api/error-handling/fallback-chains")

    def test_alternative_tools(self, client):
        r = _get(client, "/api/error-handling/alternative-tools")
        assert_route_exists(r, "/api/error-handling/alternative-tools")

    def test_test_recovery(self, client):
        r = _post(client, "/api/error-handling/test-recovery")
        assert_route_exists(r, "/api/error-handling/test-recovery")

    def test_classify_error(self, client):
        r = _post(client, "/api/error-handling/classify-error")
        assert_route_exists(r, "/api/error-handling/classify-error")

    def test_execute_with_recovery(self, client):
        r = _post(client, "/api/error-handling/execute-with-recovery")
        assert_route_exists(r, "/api/error-handling/execute-with-recovery")

    def test_parameter_adjustments(self, client):
        r = _post(client, "/api/error-handling/parameter-adjustments")
        assert_route_exists(r, "/api/error-handling/parameter-adjustments")


# ===========================================================================
# AI Payload
# ===========================================================================

class TestAIPayload:
    def test_generate_payload(self, client):
        r = _post(client, "/api/ai/generate_payload")
        assert_route_exists(r, "/api/ai/generate_payload")

    def test_test_payload(self, client):
        r = _post(client, "/api/ai/test_payload")
        assert_route_exists(r, "/api/ai/test_payload")

    def test_advanced_payload_generation(self, client):
        r = _post(client, "/api/ai/advanced-payload-generation")
        assert_route_exists(r, "/api/ai/advanced-payload-generation")


# ===========================================================================
# Bug Bounty Workflows
# ===========================================================================

class TestBugBountyWorkflows:
    def test_reconnaissance_workflow(self, client):
        r = _post(client, "/api/bugbounty/reconnaissance-workflow")
        assert_route_exists(r, "/api/bugbounty/reconnaissance-workflow")

    def test_vulnerability_hunting_workflow(self, client):
        r = _post(client, "/api/bugbounty/vulnerability-hunting-workflow")
        assert_route_exists(r, "/api/bugbounty/vulnerability-hunting-workflow")

    def test_business_logic_workflow(self, client):
        r = _post(client, "/api/bugbounty/business-logic-workflow")
        assert_route_exists(r, "/api/bugbounty/business-logic-workflow")

    def test_osint_workflow(self, client):
        r = _post(client, "/api/bugbounty/osint-workflow")
        assert_route_exists(r, "/api/bugbounty/osint-workflow")

    def test_file_upload_testing(self, client):
        r = _post(client, "/api/bugbounty/file-upload-testing")
        assert_route_exists(r, "/api/bugbounty/file-upload-testing")

    def test_comprehensive_assessment(self, client):
        r = _post(client, "/api/bugbounty/comprehensive-assessment")
        assert_route_exists(r, "/api/bugbounty/comprehensive-assessment")


# ===========================================================================
# CTF
# ===========================================================================

class TestCTF:
    def test_create_challenge_workflow(self, client):
        r = _post(client, "/api/ctf/create-challenge-workflow")
        assert_route_exists(r, "/api/ctf/create-challenge-workflow")

    def test_auto_solve_challenge(self, client):
        r = _post(client, "/api/ctf/auto-solve-challenge")
        assert_route_exists(r, "/api/ctf/auto-solve-challenge")

    def test_team_strategy(self, client):
        r = _post(client, "/api/ctf/team-strategy")
        assert_route_exists(r, "/api/ctf/team-strategy")

    def test_suggest_tools(self, client):
        r = _post(client, "/api/ctf/suggest-tools")
        assert_route_exists(r, "/api/ctf/suggest-tools")

    def test_cryptography_solver(self, client):
        r = _post(client, "/api/ctf/cryptography-solver")
        assert_route_exists(r, "/api/ctf/cryptography-solver")

    def test_forensics_analyzer(self, client):
        r = _post(client, "/api/ctf/forensics-analyzer")
        assert_route_exists(r, "/api/ctf/forensics-analyzer")

    def test_binary_analyzer(self, client):
        r = _post(client, "/api/ctf/binary-analyzer")
        assert_route_exists(r, "/api/ctf/binary-analyzer")
