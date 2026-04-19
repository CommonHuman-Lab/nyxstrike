"""
server_api/ai_assist/chat.py

Flask blueprint for the persistent chat widget.

Endpoints:
  POST   /api/chat/sessions                       Create a new chat session
  GET    /api/chat/sessions                       List all chat sessions
  DELETE /api/chat/sessions/<id>                  Delete a session + all messages
  GET    /api/chat/sessions/<id>/messages         Load full message history
  POST   /api/chat/sessions/<id>/message          Send a message — SSE streaming response

Design notes:
  - Client sends only { message, context } — never the full history.
  - Server loads history from SQLite, compresses old messages into a rolling
    summary when the non-summarized count exceeds CHAT_SUMMARIZATION_THRESHOLD.
  - Response is streamed token-by-token via text/event-stream.
  - Session context (current page / session findings) is injected as a system
    message, never stored in the message log.
  - Stop is handled by the client closing the SSE connection — Flask detects
    GeneratorExit and the generator terminates cleanly.
"""

import json
import logging
import uuid
from datetime import datetime

from flask import Blueprint, Response, jsonify, request, stream_with_context

import server_core.config_core as config_core
from server_core.singletons import db, llm_client, run_history, session_store

logger = logging.getLogger(__name__)

api_chat_bp = Blueprint("api_chat", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _session_context_snippet(page: str, session_id: str) -> str:
  """Build a concise context string from a NyxStrike workflow session."""
  if not session_id or page not in ("session-detail", "sessions"):
    return ""
  try:
    sess = session_store.get(session_id)
    if not sess:
      return ""
    max_chars = int(config_core.get("CHAT_CONTEXT_INJECTION_CHARS", 4000))
    lines = [
      f"Current session: {sess.get('name', session_id)}",
      f"Target: {sess.get('target', 'unknown')}",
      f"Created: {sess.get('created_at', '')}",
      "Recent tool runs:",
    ]
    runs = run_history.list_for_session(session_id, limit=10)
    chars_used = sum(len(l) for l in lines)
    for run in runs:
      tool = run.get("tool", "")
      exit_code = run.get("exit_code", "")
      stdout = (run.get("stdout") or "")[:500]
      entry = f"  [{tool}] exit={exit_code}\n  {stdout}"
      if chars_used + len(entry) > max_chars:
        break
      lines.append(entry)
      chars_used += len(entry)
    return "\n".join(lines)
  except Exception as exc:
    logger.warning("chat: context injection failed: %s", exc)
    return ""


def _maybe_summarize(chat_session_id: str) -> None:
  """If non-summarized messages exceed threshold, summarize the oldest half."""
  threshold = int(config_core.get("CHAT_SUMMARIZATION_THRESHOLD", 20))
  count = db.count_active_chat_messages(chat_session_id)
  if count < threshold:
    return

  active = db.get_active_chat_messages(chat_session_id)
  half = len(active) // 2
  to_summarize = active[:half]
  if not to_summarize:
    return

  # Build summary messages for the LLM
  summary_messages = [{"role": m["role"], "content": m["content"]} for m in to_summarize]
  try:
    new_summary = llm_client.generate_summary(summary_messages)
  except Exception as exc:
    logger.warning("chat: summarization failed (non-fatal): %s", exc)
    return

  # Append to existing summary
  session = db.get_chat_session(chat_session_id)
  existing = (session or {}).get("summary", "") or ""
  if existing:
    combined = f"{existing}\n\nMore recently: {new_summary}"
  else:
    combined = new_summary

  db.update_chat_summary(chat_session_id, combined)
  db.mark_messages_summarized([m["id"] for m in to_summarize])
  logger.debug(
    "chat: summarized %d messages for session %s", len(to_summarize), chat_session_id
  )


def _build_llm_messages(
  chat_session_id: str,
  new_message: str,
  page: str = "",
  session_id: str = "",
) -> list:
  """Construct the full message list to send to the LLM."""
  messages = []

  # 1. System persona
  system_prompt = config_core.get(
    "CHAT_SYSTEM_PROMPT",
    "You are NyxStrike, an expert penetration testing AI assistant.",
  )
  messages.append({"role": "system", "content": system_prompt})

  # 2. Session context (current page)
  ctx = _session_context_snippet(page, session_id)
  if ctx:
    messages.append({
      "role": "system",
      "content": f"The operator is currently viewing:\n{ctx}",
    })

  # 3. Rolling summary of old messages
  chat_sess = db.get_chat_session(chat_session_id)
  summary = (chat_sess or {}).get("summary", "") or ""
  if summary:
    messages.append({
      "role": "system",
      "content": f"Earlier in this conversation:\n{summary}",
    })

  # 4. Active (non-summarized) message history
  active = db.get_active_chat_messages(chat_session_id)
  for m in active:
    messages.append({"role": m["role"], "content": m["content"]})

  # 5. New user message
  messages.append({"role": "user", "content": new_message})
  return messages


# ── Endpoints ─────────────────────────────────────────────────────────────────

@api_chat_bp.route("/api/chat/sessions", methods=["POST"])
def create_chat_session():
  """Create a new named chat session."""
  try:
    if not llm_client.is_available():
      return jsonify({"success": False, "error": "LLM is not available"}), 503
    session_id = uuid.uuid4().hex
    sess = db.create_chat_session(session_id, name="")
    return jsonify({"success": True, "session": sess})
  except Exception as exc:
    logger.error("create_chat_session: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_chat_bp.route("/api/chat/sessions", methods=["GET"])
def list_chat_sessions():
  """List all chat sessions, newest first."""
  try:
    sessions = db.list_chat_sessions()
    return jsonify({"success": True, "sessions": sessions})
  except Exception as exc:
    logger.error("list_chat_sessions: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_chat_bp.route("/api/chat/sessions/<chat_session_id>", methods=["DELETE"])
def delete_chat_session(chat_session_id: str):
  """Delete a chat session and all its messages."""
  try:
    db.delete_chat_session(chat_session_id)
    return jsonify({"success": True})
  except Exception as exc:
    logger.error("delete_chat_session: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_chat_bp.route("/api/chat/sessions/<chat_session_id>", methods=["PATCH"])
def rename_chat_session(chat_session_id: str):
  """Rename a chat session."""
  try:
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
      return jsonify({"success": False, "error": "name is required"}), 400
    sess = db.get_chat_session(chat_session_id)
    if not sess:
      return jsonify({"success": False, "error": "Session not found"}), 404
    db.rename_chat_session(chat_session_id, name)
    return jsonify({"success": True})
  except Exception as exc:
    logger.error("rename_chat_session: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_chat_bp.route("/api/chat/sessions/<chat_session_id>/messages", methods=["GET"])
def get_chat_messages(chat_session_id: str):
  """Return the full visible message history for a session."""
  try:
    sess = db.get_chat_session(chat_session_id)
    if not sess:
      return jsonify({"success": False, "error": "Session not found"}), 404
    messages = db.get_all_chat_messages(chat_session_id)
    # Return only non-summarized so the UI shows the current window
    visible = [m for m in messages if not m.get("is_summarized")]
    return jsonify({"success": True, "messages": visible, "session": sess})
  except Exception as exc:
    logger.error("get_chat_messages: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_chat_bp.route("/api/chat/sessions/<chat_session_id>/message", methods=["POST"])
def send_chat_message(chat_session_id: str):
  """Send a user message and stream the assistant's response via SSE.

  Request body:
    message (str): The user's message text.
    context (dict): Optional { "page": str, "session_id": str }

  Response: text/event-stream
    data: <token>\\n\\n   — one event per token chunk
    data: [DONE]\\n\\n    — signals end of stream
    data: [ERROR] <msg>  — on failure
  """
  try:
    if not llm_client.is_available():
      return jsonify({"success": False, "error": "LLM is not available"}), 503

    body = request.get_json(force=True, silent=True) or {}
    user_message = (body.get("message") or "").strip()
    if not user_message:
      return jsonify({"success": False, "error": "message is required"}), 400

    ctx = body.get("context") or {}
    page = str(ctx.get("page") or "")
    ctx_session_id = str(ctx.get("session_id") or "")

    sess = db.get_chat_session(chat_session_id)
    if not sess:
      return jsonify({"success": False, "error": "Chat session not found"}), 404

    # Auto-name from first message (truncated to 50 chars)
    if not (sess.get("name") or "").strip():
      auto_name = user_message[:50] + ("…" if len(user_message) > 50 else "")
      db.rename_chat_session(chat_session_id, auto_name)

    # Persist user message
    db.add_chat_message(chat_session_id, "user", user_message)

    # Run summarization if threshold exceeded (before building prompt)
    _maybe_summarize(chat_session_id)

    # Build LLM message list
    llm_messages = _build_llm_messages(chat_session_id, user_message, page, ctx_session_id)

    def generate():
      full_response = []
      response_stats = None
      try:
        yield "data: [THINKING]\n\n"
        for chunk in llm_client.stream_chat(llm_messages):
          if isinstance(chunk, dict):
            # Stats metadata from the final Ollama chunk
            response_stats = chunk
            yield f"data: [STATS] {json.dumps(chunk)}\n\n"
            continue
          full_response.append(chunk)
          # SSE format: data: <payload>\n\n
          yield f"data: {json.dumps(chunk)}\n\n"
        # Persist the complete assistant response (with stats if available)
        complete = "".join(full_response)
        stats_json = json.dumps(response_stats) if response_stats else None
        db.add_chat_message(chat_session_id, "assistant", complete, stats=stats_json)
        yield "data: [DONE]\n\n"
      except GeneratorExit:
        # Client disconnected (stop button) — save whatever arrived
        if full_response:
          partial = "".join(full_response)
          db.add_chat_message(chat_session_id, "assistant", partial)
        logger.debug("chat: stream cancelled by client for session %s", chat_session_id)
      except Exception as exc:
        logger.error("chat: stream error: %s", exc)
        yield f"data: [ERROR] {str(exc)}\n\n"

    return Response(
      stream_with_context(generate()),
      mimetype="text/event-stream",
      headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
      },
    )
  except Exception as exc:
    logger.error("send_chat_message: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500
