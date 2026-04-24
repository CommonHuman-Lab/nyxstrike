"""
server_api/ai_assist/chat.py

Flask blueprint for the persistent chat widget.

Endpoints:
  POST   /api/chat/sessions                            Create a new chat session
  GET    /api/chat/sessions                            List all chat sessions
  DELETE /api/chat/sessions/<id>                       Delete a session + all messages
  PATCH  /api/chat/sessions/<id>                       Rename a session
  GET    /api/chat/sessions/<id>/messages              Load full message history
  POST   /api/chat/sessions/<id>/message               Send a message — SSE streaming response
  POST   /api/chat/sessions/<id>/tool-confirm          Approve or reject a pending tool call

Design notes:
  - Client sends only { message, context } — never the full history.
  - Server loads history from SQLite, compresses old messages into a rolling
    summary when the non-summarized count exceeds CHAT_SUMMARIZATION_THRESHOLD.
  - Response is streamed token-by-token via text/event-stream.
  - Session context (current page / session findings) is injected as a system
    message, never stored in the message log.
  - Stop is handled by the client closing the SSE connection — Flask detects
    GeneratorExit and the generator terminates cleanly.

Tool-calling flow (human-in-the-loop):
  1. On /message the server calls classify-task to get a relevant tool shortlist.
  2. Tool schemas are injected into the LLM call.
  3. If the model responds with tool_calls the server emits a [TOOL_CALL_PENDING]
     SSE event and the stream ends — nothing is executed yet.
  4. The UI shows a confirmation card.  The operator POSTs to /tool-confirm.
  5. On approval the server executes the tool, injects the result as a tool
     message, and re-runs the LLM to produce a follow-up response streamed
     back to the client.
  6. On rejection a cancellation message is injected and the LLM responds.
"""

import json
import logging
import uuid
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify, request, stream_with_context

import server_core.config_core as config_core
from server_core.singletons import db, llm_client, run_history, session_store
from server_core.tool_schema import build_tool_schemas
from server_core.internal_api_client import internal_api
from tool_registry import get_tool

logger = logging.getLogger(__name__)

api_chat_bp = Blueprint("api_chat", __name__)

# In-memory store for pending tool calls keyed by chat_session_id.
# Shape: { chat_session_id: { "tool_call_id": str, "tool_name": str,
#                              "tool_endpoint": str, "arguments": dict,
#                              "llm_messages": list } }
_pending_tool_calls: Dict[str, Dict[str, Any]] = {}


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

  summary_messages = [{"role": m["role"], "content": m["content"]} for m in to_summarize]
  try:
    new_summary = llm_client.generate_summary(summary_messages)
  except Exception as exc:
    logger.warning("chat: summarization failed (non-fatal): %s", exc)
    return

  session = db.get_chat_session(chat_session_id)
  existing = (session or {}).get("summary", "") or ""
  combined = f"{existing}\n\nMore recently: {new_summary}" if existing else new_summary

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


# Tools that must never be offered to the chat LLM — they are AI orchestration
# pipelines that would trigger recursive / runaway LLM-on-LLM execution.
_CHAT_TOOL_BLOCKLIST = frozenset({
  "ai_analyze_session",
  "ai_recon_session",
  "ai_vuln_session",
  "ai_profiling_session",
  "ai_osint_session",
})


# Minimum confidence required before we inject tool schemas into the LLM call.
# classify_intent returns 0.5 when there is zero keyword signal (pure fallback),
# 0.75 for a narrow keyword win or LLM-assisted classification, and 1.0 for a
# clear keyword winner.  We skip tool injection at 0.5 to avoid offering scan
# tools for casual / conversational messages that happened to contain no
# security keywords.
_TOOL_INJECT_MIN_CONFIDENCE: float = 0.6

# Short conversational phrases that should never trigger tool injection.
# These are checked before calling classify-task to avoid a pointless round-trip.
_CONVERSATIONAL_PATTERNS = (
  "thank", "thanks", "cheers", "ok", "okay", "cool", "got it",
  "sounds good", "makes sense", "perfect", "great", "nice",
  "hello", "hi ", "hey ", "howdy",
  "what is ", "what's ", "what are ", "explain ", "tell me ",
  "how does ", "how do ", "can you ", "could you ", "would you ",
  "help me understand", "what does ", "describe ",
)


def _is_conversational(message: str) -> bool:
  """Return True if the message looks like casual chat rather than a task request."""
  lower = message.lower().strip()
  # Very short messages are almost always conversational
  if len(lower) < 20:
    return True
  for pat in _CONVERSATIONAL_PATTERNS:
    if lower.startswith(pat) or f" {pat}" in lower:
      return True
  return False


def _get_tool_schemas_for_message(user_message: str) -> List[Dict[str, Any]]:
  """Use classify-task to get a focused tool shortlist for the user message.

  Returns a list of Ollama tool schemas (may be empty if classification fails,
  confidence is too low, or the message is clearly conversational).
  """
  # Fast path: skip tool injection entirely for conversational messages.
  if _is_conversational(user_message):
    logger.debug("chat: skipping tool injection — message looks conversational")
    return []

  try:
    result = internal_api.classify_task(user_message)
    if not result.get("success"):
      logger.debug("chat: classify_task returned no success: %s", result.get("error"))
      return []

    confidence = float(result.get("confidence") or 0.0)
    if confidence < _TOOL_INJECT_MIN_CONFIDENCE:
      logger.debug(
        "chat: skipping tool injection — confidence %.2f below threshold %.2f (category=%s)",
        confidence, _TOOL_INJECT_MIN_CONFIDENCE, result.get("category"),
      )
      return []

    tools = result.get("tools") or []
    if not tools:
      return []
    # Strip AI orchestration tools — they must never be called from the chat widget.
    tools = [t for t in tools if t.get("name") not in _CHAT_TOOL_BLOCKLIST]
    if not tools:
      return []
    schemas = build_tool_schemas(tools)
    logger.debug(
      "chat: injecting %d tool schemas (category=%s confidence=%.2f)",
      len(schemas), result.get("category"), confidence,
    )
    return schemas
  except Exception as exc:
    logger.warning("chat: tool schema build failed (non-fatal): %s", exc)
    return []


def _stream_llm_with_tools(
  chat_session_id: str,
  llm_messages: List[Dict[str, Any]],
  tool_schemas: List[Dict[str, Any]],
):
  """Generator: stream LLM response, handling tool_call responses.

  Yields SSE data strings.  If the model returns a tool_call the generator
  emits a [TOOL_CALL_PENDING] event and stores the pending call for /tool-confirm.
  """
  full_response: List[str] = []
  response_stats = None

  # --- Non-streaming call when tool schemas are present ---
  # We must use non-streaming chat() so we can inspect tool_calls in the response
  # before deciding whether to stream tokens or emit a pending event.
  if tool_schemas:
    try:
      yield "data: [THINKING]\n\n"
      result = llm_client.chat(llm_messages, tools=tool_schemas)

      # result is a dict: {"content": str, "tool_calls": list|None}
      tool_calls = result.get("tool_calls") if isinstance(result, dict) else None
      content = result.get("content", "") if isinstance(result, dict) else str(result)

      if tool_calls:
        # Model wants to call a tool — pick the first call
        tc = tool_calls[0]
        fn = tc.get("function", {})
        tool_name = fn.get("name", "")
        arguments = fn.get("arguments", {})

        # Look up the tool endpoint in the registry
        tool_def = get_tool(tool_name)
        if tool_def:
          # Store pending call — not executed yet
          _pending_tool_calls[chat_session_id] = {
            "tool_call_id": tc.get("id") or uuid.uuid4().hex,
            "tool_name": tool_name,
            "tool_endpoint": tool_def["endpoint"],
            "arguments": arguments if isinstance(arguments, dict) else {},
            "llm_messages": llm_messages,
          }
          # Persist the assistant's intent as a message so history is coherent
          intent_text = (
            f"[Tool call requested: **{tool_name}**]\n"
            f"Arguments: `{json.dumps(arguments, indent=2)}`"
          )
          db.add_chat_message(chat_session_id, "assistant", intent_text)
          pending_payload = {
            "tool_name": tool_name,
            "arguments": arguments if isinstance(arguments, dict) else {},
            "description": tool_def.get("desc", ""),
          }
          yield f"data: [TOOL_CALL_PENDING] {json.dumps(pending_payload)}\n\n"
          yield "data: [DONE]\n\n"
          return
        else:
          # Unknown tool — treat as plain text
          logger.warning("chat: model requested unknown tool %r, ignoring tool_calls", tool_name)

      # Plain text response (no tool call, or unknown tool)
      if content:
        for chunk in content:
          full_response.append(chunk)
          yield f"data: {json.dumps(chunk)}\n\n"
        complete = "".join(full_response)
        db.add_chat_message(chat_session_id, "assistant", complete)
      yield "data: [DONE]\n\n"
      return

    except GeneratorExit:
      if full_response:
        db.add_chat_message(chat_session_id, "assistant", "".join(full_response))
      return
    except Exception as exc:
      logger.error("chat: tool-call LLM error: %s", exc)
      yield f"data: [ERROR] {str(exc)}\n\n"
      return

  # --- Normal streaming path (no tool schemas) ---
  try:
    yield "data: [THINKING]\n\n"
    for chunk in llm_client.stream_chat(llm_messages):
      if isinstance(chunk, dict):
        response_stats = chunk
        yield f"data: [STATS] {json.dumps(chunk)}\n\n"
        continue
      full_response.append(chunk)
      yield f"data: {json.dumps(chunk)}\n\n"
    complete = "".join(full_response)
    stats_json = json.dumps(response_stats) if response_stats else None
    db.add_chat_message(chat_session_id, "assistant", complete, stats=stats_json)
    yield "data: [DONE]\n\n"
  except GeneratorExit:
    if full_response:
      partial = "".join(full_response)
      db.add_chat_message(chat_session_id, "assistant", partial)
    logger.debug("chat: stream cancelled by client for session %s", chat_session_id)
  except Exception as exc:
    logger.error("chat: stream error: %s", exc)
    yield f"data: [ERROR] {str(exc)}\n\n"


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
    _pending_tool_calls.pop(chat_session_id, None)
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
    data: [THINKING]\\n\\n              — model is working
    data: <token>\\n\\n                 — one event per token chunk
    data: [STATS] {...}\\n\\n           — Ollama performance stats
    data: [TOOL_CALL_PENDING] {...}\\n\\n — model wants to run a tool (awaiting confirmation)
    data: [DONE]\\n\\n                  — end of stream
    data: [ERROR] <msg>               — on failure
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

    # Auto-name from first message
    if not (sess.get("name") or "").strip():
      auto_name = user_message[:50] + ("…" if len(user_message) > 50 else "")
      db.rename_chat_session(chat_session_id, auto_name)

    # Persist user message
    db.add_chat_message(chat_session_id, "user", user_message)

    _maybe_summarize(chat_session_id)

    llm_messages = _build_llm_messages(chat_session_id, user_message, page, ctx_session_id)

    # Get focused tool schemas for this message (may be empty list)
    tool_schemas = _get_tool_schemas_for_message(user_message)

    return Response(
      stream_with_context(_stream_llm_with_tools(chat_session_id, llm_messages, tool_schemas)),
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


@api_chat_bp.route("/api/chat/sessions/<chat_session_id>/tool-confirm", methods=["POST"])
def confirm_tool_call(chat_session_id: str):
  """Approve or reject a pending tool call, then stream the follow-up response.

  Request body:
    approved (bool): True to execute the tool, False to cancel.

  Response: text/event-stream (same SSE format as /message)
    On approval:  tool result is injected and the LLM continues.
    On rejection: a cancellation notice is injected and the LLM responds.
  """
  try:
    if not llm_client.is_available():
      return jsonify({"success": False, "error": "LLM is not available"}), 503

    pending = _pending_tool_calls.get(chat_session_id)
    if not pending:
      return jsonify({"success": False, "error": "No pending tool call for this session"}), 404

    body = request.get_json(force=True, silent=True) or {}
    approved = bool(body.get("approved", False))

    tool_name = pending["tool_name"]
    tool_endpoint = pending["tool_endpoint"]
    arguments = pending["arguments"]
    llm_messages = list(pending["llm_messages"])  # copy

    # Clear the pending call regardless of outcome
    _pending_tool_calls.pop(chat_session_id, None)

    def generate():
      yield "data: [THINKING]\n\n"

      if approved:
        # Execute the tool via internal REST call
        logger.info(
          "chat: operator approved tool call %r with args %s (session %s)",
          tool_name, arguments, chat_session_id,
        )
        tool_result = internal_api.run_tool(tool_endpoint, arguments)

        # Summarise result for the LLM (cap at 4000 chars to stay within context)
        result_text = json.dumps(tool_result, indent=2)
        if len(result_text) > 4000:
          result_text = result_text[:4000] + "\n… (truncated)"

        # Record execution in chat history
        exec_record = (
          f"[Tool executed: **{tool_name}**]\n"
          f"Arguments: `{json.dumps(arguments)}`\n"
          f"Result:\n```json\n{result_text}\n```"
        )
        db.add_chat_message(chat_session_id, "assistant", exec_record)

        # Build continuation messages: add tool result as a tool role message
        llm_messages.append({
          "role": "tool",
          "content": result_text,
        })
      else:
        logger.info(
          "chat: operator rejected tool call %r (session %s)", tool_name, chat_session_id
        )
        cancel_text = f"[Tool call cancelled by operator: {tool_name}]"
        db.add_chat_message(chat_session_id, "assistant", cancel_text)
        llm_messages.append({
          "role": "tool",
          "content": f"The operator chose not to run {tool_name}.",
        })

      # Stream the LLM follow-up (no tools this round — just interpret the result)
      full_response: list = []
      response_stats = None
      try:
        for chunk in llm_client.stream_chat(llm_messages):
          if isinstance(chunk, dict):
            response_stats = chunk
            yield f"data: [STATS] {json.dumps(chunk)}\n\n"
            continue
          full_response.append(chunk)
          yield f"data: {json.dumps(chunk)}\n\n"
        complete = "".join(full_response)
        stats_json = json.dumps(response_stats) if response_stats else None
        db.add_chat_message(chat_session_id, "assistant", complete, stats=stats_json)
        yield "data: [DONE]\n\n"
      except GeneratorExit:
        if full_response:
          db.add_chat_message(chat_session_id, "assistant", "".join(full_response))
      except Exception as exc:
        logger.error("chat: tool-confirm stream error: %s", exc)
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
    logger.error("confirm_tool_call: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500
