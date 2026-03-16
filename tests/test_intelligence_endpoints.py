"""
Tests for intelligence endpoints:
  POST /api/intelligence/analyze-target
  POST /api/intelligence/select-tools
  POST /api/intelligence/classify-task
  POST /api/intelligence/optimize-parameters
  POST /api/intelligence/create-attack-chain
"""

import json
import pytest


def _post(client, url, payload):
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# /api/intelligence/classify-task
# (pure Python — no external tools needed, no mock required)
# ---------------------------------------------------------------------------

class TestClassifyTask:
    def test_classify_returns_200(self, client):
        response = _post(client, "/api/intelligence/classify-task",
                         {"description": "scan open ports on the target"})
        assert response.status_code == 200

    def test_classify_success_true(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "scan open ports on the target"}).get_json()
        assert data["success"] is True

    def test_classify_returns_category(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "scan open ports on the target"}).get_json()
        assert "category" in data
        assert isinstance(data["category"], str)

    def test_classify_returns_confidence(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "scan open ports on the target"}).get_json()
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_classify_returns_tools_list(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "brute force SSH login"}).get_json()
        assert "tools" in data
        assert isinstance(data["tools"], (list, dict))

    def test_classify_network_task(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "nmap port scan network recon"}).get_json()
        assert data["success"] is True
        assert data["category"] == "network_recon"

    def test_classify_web_vuln_task(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "test for sql injection vulnerabilities"}).get_json()
        assert data["success"] is True
        assert data["category"] == "web_vuln"

    def test_classify_brute_force_task(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "crack password hashes with hashcat"}).get_json()
        assert data["success"] is True
        assert data["category"] == "brute_force"

    def test_classify_missing_description_returns_400(self, client):
        response = _post(client, "/api/intelligence/classify-task", {})
        assert response.status_code == 400

    def test_classify_error_body_has_error_key(self, client):
        data = _post(client, "/api/intelligence/classify-task", {}).get_json()
        assert "error" in data

    def test_classify_timestamp_present(self, client):
        data = _post(client, "/api/intelligence/classify-task",
                     {"description": "subdomain enumeration"}).get_json()
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# /api/intelligence/analyze-target
# ---------------------------------------------------------------------------

class TestAnalyzeTarget:
    def test_analyze_returns_200(self, client):
        response = _post(client, "/api/intelligence/analyze-target",
                         {"target": "192.168.1.1"})
        assert response.status_code == 200

    def test_analyze_success_true(self, client):
        data = _post(client, "/api/intelligence/analyze-target",
                     {"target": "192.168.1.1"}).get_json()
        assert data["success"] is True

    def test_analyze_returns_target_profile(self, client):
        data = _post(client, "/api/intelligence/analyze-target",
                     {"target": "192.168.1.1"}).get_json()
        assert "target_profile" in data
        assert isinstance(data["target_profile"], dict)

    def test_analyze_profile_has_target_type(self, client):
        data = _post(client, "/api/intelligence/analyze-target",
                     {"target": "192.168.1.1"}).get_json()
        profile = data["target_profile"]
        assert "target_type" in profile

    def test_analyze_missing_target_returns_400(self, client):
        response = _post(client, "/api/intelligence/analyze-target", {})
        assert response.status_code == 400

    def test_analyze_timestamp_present(self, client):
        data = _post(client, "/api/intelligence/analyze-target",
                     {"target": "example.com"}).get_json()
        assert "timestamp" in data

    def test_analyze_web_target(self, client):
        data = _post(client, "/api/intelligence/analyze-target",
                     {"target": "https://example.com"}).get_json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# /api/intelligence/select-tools
# ---------------------------------------------------------------------------

class TestSelectTools:
    def test_select_returns_200(self, client):
        response = _post(client, "/api/intelligence/select-tools",
                         {"target": "192.168.1.1"})
        assert response.status_code == 200

    def test_select_success_true(self, client):
        data = _post(client, "/api/intelligence/select-tools",
                     {"target": "192.168.1.1"}).get_json()
        assert data["success"] is True

    def test_select_returns_tools(self, client):
        data = _post(client, "/api/intelligence/select-tools",
                     {"target": "192.168.1.1"}).get_json()
        assert "selected_tools" in data
        assert isinstance(data["selected_tools"], list)

    def test_select_returns_tool_count(self, client):
        data = _post(client, "/api/intelligence/select-tools",
                     {"target": "192.168.1.1"}).get_json()
        assert "tool_count" in data
        assert data["tool_count"] == len(data["selected_tools"])

    def test_select_missing_target_returns_400(self, client):
        response = _post(client, "/api/intelligence/select-tools", {})
        assert response.status_code == 400

    def test_select_with_objective(self, client):
        data = _post(client, "/api/intelligence/select-tools",
                     {"target": "192.168.1.1", "objective": "quick"}).get_json()
        assert data["success"] is True
        assert data["objective"] == "quick"


# ---------------------------------------------------------------------------
# /api/intelligence/optimize-parameters
# ---------------------------------------------------------------------------

class TestOptimizeParameters:
    def test_optimize_returns_200(self, client):
        response = _post(client, "/api/intelligence/optimize-parameters",
                         {"target": "192.168.1.1", "tool": "nmap"})
        assert response.status_code == 200

    def test_optimize_success_true(self, client):
        data = _post(client, "/api/intelligence/optimize-parameters",
                     {"target": "192.168.1.1", "tool": "nmap"}).get_json()
        assert data["success"] is True

    def test_optimize_returns_optimized_parameters(self, client):
        data = _post(client, "/api/intelligence/optimize-parameters",
                     {"target": "192.168.1.1", "tool": "nmap"}).get_json()
        assert "optimized_parameters" in data

    def test_optimize_missing_target_returns_400(self, client):
        response = _post(client, "/api/intelligence/optimize-parameters",
                         {"tool": "nmap"})
        assert response.status_code == 400

    def test_optimize_missing_tool_returns_400(self, client):
        response = _post(client, "/api/intelligence/optimize-parameters",
                         {"target": "192.168.1.1"})
        assert response.status_code == 400

    def test_optimize_returns_target_and_tool(self, client):
        data = _post(client, "/api/intelligence/optimize-parameters",
                     {"target": "192.168.1.1", "tool": "gobuster"}).get_json()
        assert data["target"] == "192.168.1.1"
        assert data["tool"] == "gobuster"


# ---------------------------------------------------------------------------
# /api/intelligence/create-attack-chain
# ---------------------------------------------------------------------------

class TestCreateAttackChain:
    def test_chain_returns_200(self, client):
        response = _post(client, "/api/intelligence/create-attack-chain",
                         {"target": "192.168.1.1"})
        assert response.status_code == 200

    def test_chain_success_true(self, client):
        data = _post(client, "/api/intelligence/create-attack-chain",
                     {"target": "192.168.1.1"}).get_json()
        assert data["success"] is True

    def test_chain_returns_attack_chain(self, client):
        data = _post(client, "/api/intelligence/create-attack-chain",
                     {"target": "192.168.1.1"}).get_json()
        assert "attack_chain" in data
        assert isinstance(data["attack_chain"], dict)

    def test_chain_missing_target_returns_400(self, client):
        response = _post(client, "/api/intelligence/create-attack-chain", {})
        assert response.status_code == 400

    def test_chain_with_objective(self, client):
        data = _post(client, "/api/intelligence/create-attack-chain",
                     {"target": "192.168.1.1", "objective": "stealth"}).get_json()
        assert data["success"] is True
        assert data["objective"] == "stealth"

    def test_chain_returns_timestamp(self, client):
        data = _post(client, "/api/intelligence/create-attack-chain",
                     {"target": "192.168.1.1"}).get_json()
        assert "timestamp" in data
