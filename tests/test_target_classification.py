"""
tests/test_target_classification.py

Pure-Python unit tests for IntelligentDecisionEngine._determine_target_type()
and the lightweight heuristic helpers (_detect_technologies, _detect_cms,
_detect_cloud_provider).

No subprocess, no Flask, no server calls.
The engine is instantiated directly — it performs no I/O during __init__.
"""

import pytest

from server_core.intelligence.intelligent_decision_engine import IntelligentDecisionEngine
from shared.target_types import TargetType, TechnologyStack


@pytest.fixture(scope="module")
def engine():
    return IntelligentDecisionEngine()


# ---------------------------------------------------------------------------
# _determine_target_type
# ---------------------------------------------------------------------------

class TestDetermineTargetType:

    # --- bare IP address ---
    @pytest.mark.parametrize("target", [
        "10.10.10.10",
        "192.168.1.1",
        "172.16.0.1",
        "8.8.8.8",
    ])
    def test_bare_ip_is_network_host(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.NETWORK_HOST

    # --- binary file extensions ---
    @pytest.mark.parametrize("target", [
        "challenge.exe",
        "firmware.bin",
        "crackme.elf",
        "lib.so",
        "plugin.dll",
    ])
    def test_binary_extensions_are_binary_file(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.BINARY_FILE

    # --- cloud service domains ---
    @pytest.mark.parametrize("target", [
        "https://aws.amazon.com",
        "https://s3.amazonaws.com/bucket",
        "https://app.azurewebsites.net",
        "https://storage.googleapis.com",
    ])
    def test_cloud_domains_are_cloud_service(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.CLOUD_SERVICE

    # --- api. subdomain prefix ---
    @pytest.mark.parametrize("target", [
        "https://api.example.com",
        "https://api.example.com/v1/users",
        "api.example.com",
    ])
    def test_api_subdomain_is_api_endpoint(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.API_ENDPOINT

    # --- API path hints ---
    @pytest.mark.parametrize("target", [
        "https://example.com/api",
        "https://example.com/api/v2/items",
        "https://example.com/graphql",
        "https://example.com/v1/users",
    ])
    def test_api_path_hints_are_api_endpoint(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.API_ENDPOINT

    # --- query string tokens ---
    @pytest.mark.parametrize("target", [
        "https://example.com/query?graphql=1",
        "https://example.com/docs?openapi=true",
        "https://example.com/spec?swagger=json",
    ])
    def test_query_token_is_api_endpoint(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.API_ENDPOINT

    # --- plain web application ---
    @pytest.mark.parametrize("target", [
        "https://example.com",
        "https://shop.example.com/products",
        "https://blog.example.com/post/1",
        "http://example.com/login",
    ])
    def test_plain_web_url_is_web_application(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.WEB_APPLICATION

    # --- bare domain without scheme ---
    @pytest.mark.parametrize("target", [
        "example.com",
        "shop.example.co.uk",
    ])
    def test_bare_domain_is_web_application(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.WEB_APPLICATION

    # --- UNKNOWN fallback ---
    @pytest.mark.parametrize("target", [
        "not-a-valid-target",
        "just_some_string",
        "",
    ])
    def test_unrecognised_target_is_unknown(self, engine, target):
        assert engine._determine_target_type(target) == TargetType.UNKNOWN


# ---------------------------------------------------------------------------
# _detect_technologies
# ---------------------------------------------------------------------------

class TestDetectTechnologies:
    def test_wordpress_url_detected(self, engine):
        techs = engine._detect_technologies("https://example.com/wp-login.php")
        assert TechnologyStack.WORDPRESS in techs

    def test_php_extension_detected(self, engine):
        techs = engine._detect_technologies("https://example.com/index.php")
        assert TechnologyStack.PHP in techs

    def test_aspx_extension_detected(self, engine):
        techs = engine._detect_technologies("https://example.com/login.aspx")
        assert TechnologyStack.DOTNET in techs

    def test_unknown_target_returns_unknown(self, engine):
        techs = engine._detect_technologies("https://example.com")
        assert techs == [TechnologyStack.UNKNOWN]

    def test_multiple_technologies_detected(self, engine):
        # URL hints at both WordPress and PHP
        techs = engine._detect_technologies("https://example.com/wordpress.php")
        assert TechnologyStack.WORDPRESS in techs
        assert TechnologyStack.PHP in techs


# ---------------------------------------------------------------------------
# _detect_cms
# ---------------------------------------------------------------------------

class TestDetectCMS:
    def test_wordpress_detected(self, engine):
        assert engine._detect_cms("https://example.com/wp-admin") == "WordPress"

    def test_drupal_detected(self, engine):
        assert engine._detect_cms("https://example.com/drupal/node/1") == "Drupal"

    def test_joomla_detected(self, engine):
        assert engine._detect_cms("https://example.com/joomla/index.php") == "Joomla"

    def test_unknown_returns_none(self, engine):
        assert engine._detect_cms("https://example.com") is None


# ---------------------------------------------------------------------------
# _detect_cloud_provider
# ---------------------------------------------------------------------------

class TestDetectCloudProvider:
    def test_aws_detected(self, engine):
        assert engine._detect_cloud_provider("https://s3.amazonaws.com") == "aws"

    def test_azure_detected(self, engine):
        assert engine._detect_cloud_provider("https://app.azurewebsites.net") == "azure"

    def test_gcp_detected(self, engine):
        assert engine._detect_cloud_provider("https://storage.googleapis.com") == "gcp"

    def test_unknown_returns_none(self, engine):
        assert engine._detect_cloud_provider("https://example.com") is None
