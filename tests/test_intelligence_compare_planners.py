import pytest
from unittest.mock import patch, MagicMock

from server_core.singletons import decision_engine
from nyxstrike_server import app

_MOCK_RESULT = {"success": True, "output": "mocked", "returncode": 0}


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    app.config["NYXSTRIKE_API_TOKEN"] = None
    with app.test_client() as c:
        yield c


def test_compare_planner_modes_directly_for_same_target():
    profile = decision_engine.analyze_target("https://example.com/api")

    advanced_tools = decision_engine.select_optimal_tools(profile, "api_security", planner_mode="advanced")
    legacy_tools = decision_engine.select_optimal_tools(profile, "api_security", planner_mode="legacy")

    assert isinstance(advanced_tools, list)
    assert isinstance(legacy_tools, list)
    assert advanced_tools
    assert legacy_tools
    assert len(advanced_tools) <= 8
    assert len(legacy_tools) <= 8
    # The two planners must produce different selections — if identical the
    # mode switch has no effect and the test is vacuous.
    assert set(advanced_tools) != set(legacy_tools), (
        "advanced and legacy planners returned identical tool sets — "
        "mode switching appears to have no effect"
    )


@patch("server_core.command_executor.execute_command", return_value=_MOCK_RESULT)
def test_compare_planners_endpoint_contains_recommendation_fields(_mock_exec, client):
    response = client.post(
        "/api/intelligence/compare-planners",
        json={"target": "https://example.com/api", "objective": "api_security"},
    )

    assert response.status_code != 404
    body = response.get_json()
    assert isinstance(body, dict)
    assert body.get("success") is True
    assert body.get("recommendation") in {"advanced", "legacy"}
    assert isinstance(body.get("recommendation_reason"), str)
    coverage = body.get("coverage", {})
    assert isinstance(coverage.get("required_capabilities"), list)
