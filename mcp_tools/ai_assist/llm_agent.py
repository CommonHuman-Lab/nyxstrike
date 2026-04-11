# mcp_tools/ai_assist/llm_agent.py
#
# MCP tool wrappers for the LLM agent endpoints.
# Exposes three tools to MCP clients:
#   analyze_session       — analyse a completed NyxStrike session's run logs
#   llm_agent_scan_result — retrieve a past analysis session by ID
#   llm_status            — check LLM backend availability

from typing import Any, Dict
import asyncio


def register_llm_agent_tools(mcp, api_client, logger, CliColors=None):

  @mcp.tool()
  async def analyze_session(session_id: str) -> Dict[str, Any]:
    """
    Analyse an existing NyxStrike workflow session using the LLM.

    Fetches all tool run logs associated with the session, sends them to
    the configured LLM for interpretation, and persists structured
    vulnerability findings to NyxStrikeDB.  The LLM does NOT dispatch
    any tools — this is a pure analysis pass over already-executed output.

    Args:
        session_id: A ``sess_`` prefixed session ID from SessionStore
                    (e.g. "sess_abc1234567").

    Returns:
        Dict with llm_session_id, session_id, target, objective,
        risk_level, summary, vulnerabilities, logs_analysed,
        full_response, and success flag.
    """
    logger.info(f"[analyze_session] session_id={session_id!r}")

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
      None,
      lambda: api_client.safe_post(
        "api/intelligence/analyze-session",
        {"session_id": session_id},
      ),
    )

    if not result.get("success"):
      logger.error(
        f"[analyze_session] failed for session={session_id!r}: "
        f"{result.get('error', 'unknown error')}"
      )
    else:
      risk = result.get("risk_level", "UNKNOWN")
      vulns = len(result.get("vulnerabilities", []))
      logs = result.get("logs_analysed", 0)
      logger.info(
        f"[analyze_session] complete — risk={risk} vulns={vulns} logs={logs}"
      )

    return result

  @mcp.tool()
  async def llm_agent_scan_result(session_id: str) -> Dict[str, Any]:
    """
    Retrieve the results of a completed LLM agent scan session.

    Args:
        session_id: The session ID returned by llm_agent_scan.

    Returns:
        Dict with session metadata, vulnerabilities, and tool call log.
    """
    logger.info(f"[llm_agent_scan_result] fetching session={session_id!r}")

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
      None,
      lambda: api_client.safe_get(
        f"api/intelligence/llm-agent-scan/{session_id}"
      ),
    )

    if not result.get("success"):
      logger.error(
        f"[llm_agent_scan_result] failed for session={session_id!r}: "
        f"{result.get('error', 'unknown error')}"
      )

    return result

  @mcp.tool()
  async def llm_status() -> Dict[str, Any]:
    """
    Check whether the LLM backend is available and report its configuration.

    Returns:
        Dict with available (bool), provider, model, max_loops, and error (if any).
    """
    logger.info("[llm_status] checking LLM backend status")

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
      None,
      lambda: api_client.safe_get("api/intelligence/llm-status"),
    )

    available = result.get("available", False)
    provider = result.get("provider", "unknown")
    model = result.get("model", "unknown")

    if available:
      logger.info(f"[llm_status] available — provider={provider} model={model}")
    else:
      logger.warning(
        f"[llm_status] NOT available — provider={provider} model={model} "
        f"error={result.get('error', '')}"
      )

    return result
