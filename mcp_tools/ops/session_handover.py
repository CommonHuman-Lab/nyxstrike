from typing import Dict, Any, List
import asyncio

from tool_registry import SUGGESTED_APPROACHES


def _build_continuation_plan(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return all workflow steps with full metadata — no cap."""
    steps = session.get("workflow_steps", []) if isinstance(session, dict) else []
    if not isinstance(steps, list):
        steps = []

    plan = []
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        plan.append({
            "order": idx + 1,
            "tool": step.get("tool", ""),
            "parameters": step.get("parameters", {}),
            "expected_outcome": step.get("expected_outcome", ""),
            "success_probability": step.get("success_probability", 0),
            "execution_time_estimate": step.get("execution_time_estimate", 0),
            "dependencies": step.get("dependencies", []),
        })
    return plan


def _build_execution_progress(session: Dict[str, Any]) -> Dict[str, Any]:
    """Summarise how far through the workflow the session is."""
    steps = session.get("workflow_steps", [])
    if not isinstance(steps, list):
        steps = []
    total_steps = len(steps)

    tools_executed = session.get("tools_executed", [])
    if not isinstance(tools_executed, list):
        tools_executed = []
    completed_steps = len(tools_executed)

    return {
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "pending_steps": max(0, total_steps - completed_steps),
        "iterations": session.get("iterations", 0),
        "total_findings": session.get("total_findings", 0),
    }


def _build_prior_handovers(session: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """Return the most recent handover history entries, newest first."""
    history = session.get("handover_history", [])
    if not isinstance(history, list):
        return []
    recent = history[-limit:] if len(history) > limit else history[:]
    recent.reverse()
    return recent


def register_session_handover_tools(mcp, api_client, logger):
    @mcp.tool()
    async def handover_session(session_id: str, note: str = "") -> Dict[str, Any]:
        """
        Handover a persisted session to AI using session ID and return full continuation context.

        Returns everything the AI needs to pick up the engagement immediately:
        session state, classified next action with a suggested approach, the full
        workflow plan (all steps with metadata), execution progress, and prior handover history.

        Args:
            session_id: Existing session ID from the Sessions page/API
            note: Optional operator note/context for this handover

        Returns:
            session, handover classification, continuation_context (with suggested_approach
            and full next_steps), execution_progress, and prior_handovers
        """
        logger.info(f"Handing over session {session_id}")

        loop = asyncio.get_running_loop()
        session_resp = await loop.run_in_executor(
            None, lambda: api_client.safe_get(f"api/sessions/{session_id}")
        )
        if not session_resp.get("success"):
            logger.error(f"Session {session_id} not found")
            return session_resp

        handover_resp = await loop.run_in_executor(
            None, lambda: api_client.safe_post(
                f"api/sessions/{session_id}/handover", {"note": note}
            )
        )
        if not handover_resp.get("success"):
            logger.error(f"Session handover failed for {session_id}")
            return handover_resp

        session = handover_resp.get("session") or session_resp.get("session", {})
        handover = handover_resp.get("handover", {})
        category = handover.get("category", "")

        continuation_plan = _build_continuation_plan(session)
        execution_progress = _build_execution_progress(session)
        prior_handovers = _build_prior_handovers(session)

        logger.info(
            "Session handover complete | category=%s confidence=%.2f",
            category,
            float(handover.get("confidence", 0)),
        )

        return {
            "success": True,
            "session_id": session_id,
            "session": session,
            "handover": handover,
            "continuation_context": {
                "target": session.get("target", ""),
                "status": session.get("status", "active"),
                "objective": session.get("objective", ""),
                "source": session.get("source", ""),
                "suggested_approach": SUGGESTED_APPROACHES.get(category, ""),
                "next_steps": continuation_plan,
            },
            "execution_progress": execution_progress,
            "prior_handovers": prior_handovers,
        }
