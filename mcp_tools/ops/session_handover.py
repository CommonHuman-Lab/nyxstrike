from typing import Dict, Any, List
import asyncio


def _build_continuation_plan(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = session.get("workflow_steps", []) if isinstance(session, dict) else []
    if not isinstance(steps, list):
        steps = []

    plan = []
    for idx, step in enumerate(steps[:8]):
        if not isinstance(step, dict):
            continue
        plan.append({
            "order": idx + 1,
            "tool": step.get("tool", ""),
            "parameters": step.get("parameters", {}),
            "expected_outcome": step.get("expected_outcome", ""),
        })
    return plan


def register_session_handover_tools(mcp, hexstrike_client, logger):
    @mcp.tool()
    async def handover_session(session_id: str, note: str = "") -> Dict[str, Any]:
        """
        Handover a persisted session to AI using session ID and return continuation context.

        Args:
            session_id: Existing session ID from the Sessions page/API
            note: Optional operator note/context for this handover

        Returns:
            Session details, handover classification, and a continuation plan
        """
        logger.info(f"🤝 Handing over session {session_id}")

        loop = asyncio.get_running_loop()
        session_resp = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_get(f"api/sessions/{session_id}")
        )
        if not session_resp.get("success"):
            logger.error(f"❌ Session {session_id} not found")
            return session_resp

        handover_resp = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_post(f"api/sessions/{session_id}/handover", {"note": note})
        )
        if not handover_resp.get("success"):
            logger.error(f"❌ Session handover failed for {session_id}")
            return handover_resp

        session = handover_resp.get("session") or session_resp.get("session", {})
        handover = handover_resp.get("handover", {})
        continuation_plan = _build_continuation_plan(session)

        logger.info(
            "✅ Session handover complete | category=%s confidence=%.2f",
            handover.get("category", "unknown"),
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
                "next_steps": continuation_plan,
            },
        }
