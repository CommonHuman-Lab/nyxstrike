"""
server_api/burp_agent/routes.py

Flask blueprint: Burp Agent Loop API.

This provides the backend for the NyxStrike Burp Suite extension.  The
extension sends a captured HTTP request/response from Burp and an autonomous
LLM-driven agent analyses it, selects relevant tools, and waits for operator
approval before executing each tool call.

Endpoints:
  POST /api/burp/agent/start
      Body: { http_request, http_response?, context? }
      Returns: { success, session_id }

  GET  /api/burp/agent/<session_id>/stream
      SSE stream of agent events:
        [THINKING]                     — LLM is reasoning
        [TOKEN] <chunk>                — streamed LLM token
        [TOOL_CONFIRM_REQUEST] {...}   — agent wants to run a tool; awaiting approval
        [TOOL_EXECUTING] {...}         — tool approved and running
        [TOOL_RESULT] {...}            — tool finished; result injected
        [FINAL_RESPONSE] <text>        — full final Markdown response
        [STATS] {...}                  — token stats (Ollama only)
        [DONE]                         — agent finished
        [CANCELLED]                    — agent cancelled by operator
        [ERROR] <msg>                  — unrecoverable error

  POST /api/burp/agent/<session_id>/confirm
      Body: { approved: bool }
      Returns: { success }
      Unblocks the agent: approved → execute tool; rejected → skip.

  POST /api/burp/agent/<session_id>/cancel
      Returns: { success }
      Signals the background agent thread to stop.

Agent loop design:
  1. Parse the raw HTTP request text to extract method, URL, host, path, headers,
     body for context injection.
  2. Build a focused pentest system prompt with the HTTP request embedded.
  3. Classify the target URL via /api/intelligence/classify-task to select
     relevant tool schemas (max 8 tools so the context stays manageable).
  4. Run up to NYXSTRIKE_LLM_MAX_LOOPS iterations:
       a. Call llm_client.chat() with tool schemas.
       b. Stream tokens to the SSE queue.
       c. On tool_call: emit [TOOL_CONFIRM_REQUEST], block on threading.Event.
       d. On approval:  execute tool via internal_api, inject result, continue.
       e. On rejection: inject skip notice, continue.
  5. Emit [FINAL_RESPONSE] + [DONE].

Session state is stored in a module-level dict keyed by session_id and cleaned
up after 1 hour of inactivity.
"""

import json
import logging
import queue
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from flask import Blueprint, Response, jsonify, request, stream_with_context
from server_core.singletons import llm_client
from server_core.internal_api_client import internal_api
from server_core.tool_schema import build_tool_schemas

logger = logging.getLogger(__name__)

api_burp_agent_bp = Blueprint("api_burp_agent", __name__)

# ── Session state ──────────────────────────────────────────────────────────────
# Each entry: {
#   "session_id":    str,
#   "status":        "running" | "waiting_confirm" | "done" | "cancelled" | "error",
#   "queue":         Queue[str],          — SSE event strings
#   "confirm_event": threading.Event,     — set by /confirm to unblock agent
#   "confirm_approved": bool,
#   "cancel_event":  threading.Event,     — set by /cancel
#   "created_at":    float,               — unix timestamp for TTL cleanup
#   "pending_tool":  dict | None,         — the tool awaiting confirmation
# }
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = threading.Lock()

# Maximum age (seconds) before an idle session is garbage-collected
_SESSION_TTL = 3600

# Maximum SSE queue depth; if the consumer is too slow we drop old events
_QUEUE_MAX = 2000

# System prompt template — {http_request} substituted at runtime
_SYSTEM_PROMPT = """\
You are NyxStrike, an autonomous penetration testing AI assistant embedded in Burp Suite.

The operator has captured the following HTTP request and sent it to you for analysis:

--- BEGIN HTTP REQUEST ---
{http_request}
--- END HTTP REQUEST ---

{http_response_section}

Your task:
1. Analyse the request for potential vulnerabilities (injections, auth issues,
   IDOR, SSRF, business logic flaws, etc.).
2. Decide which NyxStrike security tools would be most useful to investigate
   further.  Call tools one at a time using the tool_call mechanism.
3. After each tool result, interpret the findings and decide on the next step.
4. When you have gathered enough information, write a clear final penetration
   testing report in Markdown covering:
   - Target summary
   - Vulnerabilities found (with evidence)
   - Risk ratings
   - Recommended remediations

Be precise, technical, and concise.  Do not hallucinate tool output.
"""

_HTTP_RESPONSE_SECTION = """\
The operator also captured the server's HTTP response:

--- BEGIN HTTP RESPONSE ---
{http_response}
--- END HTTP RESPONSE ---
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _gc_sessions() -> None:
  """Remove sessions older than _SESSION_TTL. Called opportunistically."""
  now = time.time()
  with _sessions_lock:
    stale = [sid for sid, s in _sessions.items() if now - s["created_at"] > _SESSION_TTL]
    for sid in stale:
      _sessions.pop(sid, None)
      logger.debug("burp_agent: gc removed session %s", sid)


def _get_session(session_id: str) -> Optional[Dict[str, Any]]:
  with _sessions_lock:
    return _sessions.get(session_id)


def _push(sess: Dict[str, Any], event: str) -> None:
  """Push an SSE event string onto the session queue (drops if full)."""
  q: queue.Queue = sess["queue"]
  try:
    q.put_nowait(event)
  except queue.Full:
    logger.warning("burp_agent: queue full for session %s, dropping event", sess["session_id"])


def _sse(event_type: str, data: Any = None) -> str:
  """Format a single SSE data line."""
  if data is None:
    return f"data: [{event_type}]\n\n"
  if isinstance(data, str):
    return f"data: [{event_type}] {data}\n\n"
  return f"data: [{event_type}] {json.dumps(data)}\n\n"


def _parse_http_request(raw: str) -> Dict[str, Any]:
  """Extract method, url, host, path, headers, body from a raw HTTP request string."""
  result = {"method": "", "url": "", "host": "", "path": "/", "headers": {}, "body": ""}
  if not raw:
    return result
  try:
    lines = raw.replace("\r\n", "\n").split("\n")
    # Request line
    request_line = lines[0].strip()
    parts = request_line.split(" ")
    if len(parts) >= 2:
      result["method"] = parts[0]
      result["path"] = parts[1]

    # Headers (until blank line)
    header_section_done = False
    body_lines: List[str] = []
    headers: Dict[str, str] = {}
    for line in lines[1:]:
      if not header_section_done:
        if line.strip() == "":
          header_section_done = True
          continue
        if ":" in line:
          k, _, v = line.partition(":")
          headers[k.strip().lower()] = v.strip()
      else:
        body_lines.append(line)

    result["headers"] = headers
    result["body"] = "\n".join(body_lines).strip()
    host = headers.get("host", "")
    result["host"] = host
    if host:
      scheme = "https" if ":443" in host or not host else "http"
      result["url"] = f"{scheme}://{host}{result['path']}"
  except Exception as exc:
    logger.warning("burp_agent: HTTP parse error: %s", exc)
  return result


def _get_tool_schemas_for_target(url: str, http_context: str) -> List[Dict[str, Any]]:
  """Use classify-task to pick tool schemas relevant to this target."""
  try:
    # Build a description that hints at web pentest context
    parsed = urlparse(url)
    desc = f"web penetration test of {parsed.netloc} — analyse HTTP request at {url}"
    result = internal_api.classify_task(desc)
    if not result.get("success"):
      return []
    tools = result.get("tools") or []
    # Limit to 8 tools to keep context size manageable
    tools = tools[:8]
    return build_tool_schemas(tools)
  except Exception as exc:
    logger.warning("burp_agent: classify_task failed: %s", exc)
    return []


# ── Agent loop (runs in a background thread) ──────────────────────────────────

def _run_agent(session_id: str, http_request: str, http_response: str) -> None:
  """Main agent loop — runs in a daemon thread for each Burp agent session."""
  sess = _get_session(session_id)
  if not sess:
    return

  cancel: threading.Event = sess["cancel_event"]
  confirm_event: threading.Event = sess["confirm_event"]

  def push(event: str) -> None:
    _push(sess, event)

  try:
    # 1. Parse the HTTP request for context
    http_ctx = _parse_http_request(http_request)
    url = http_ctx.get("url", "")

    # 2. Build system prompt
    response_section = ""
    if http_response and http_response.strip():
      response_section = _HTTP_RESPONSE_SECTION.format(http_response=http_response[:3000])

    system_prompt = _SYSTEM_PROMPT.format(
      http_request=http_request[:4000],
      http_response_section=response_section,
    )

    # 3. Get tool schemas
    tool_schemas = _get_tool_schemas_for_target(url, http_request)

    # 4. Build initial message list
    messages: List[Dict[str, Any]] = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": (
        "Please begin your analysis of the captured HTTP request. "
        "Identify any potential vulnerabilities and use the available tools "
        "to investigate. Report your findings when complete."
      )},
    ]

    max_loops = llm_client.max_loops
    loop_count = 0

    push(_sse("THINKING"))

    while loop_count < max_loops:
      if cancel.is_set():
        push(_sse("CANCELLED"))
        sess["status"] = "cancelled"
        push(_sse("DONE"))
        return

      loop_count += 1
      logger.debug("burp_agent: session %s loop %d/%d", session_id, loop_count, max_loops)

      # 5. Call LLM (non-streaming when tools are present so we can inspect tool_calls)
      try:
        result = llm_client.chat(messages, tools=tool_schemas if tool_schemas else None)
      except Exception as exc:
        logger.error("burp_agent: LLM error in session %s: %s", session_id, exc)
        push(_sse("ERROR", str(exc)))
        sess["status"] = "error"
        push(_sse("DONE"))
        return

      # Normalise result
      if isinstance(result, dict):
        content: str = result.get("content", "") or ""
        tool_calls = result.get("tool_calls") or None
      else:
        content = str(result)
        tool_calls = None

      # 6. Stream content tokens to the client
      if content:
        # Emit content word-by-word for a live typing feel
        words = content.split(" ")
        for i, word in enumerate(words):
          chunk = word if i == 0 else " " + word
          push(_sse("TOKEN", chunk))
        # Append assistant message to history
        messages.append({"role": "assistant", "content": content})

      # 7. Handle tool call
      if tool_calls:
        tc = tool_calls[0]
        fn = tc.get("function", {})
        tool_name = fn.get("name", "")
        arguments = fn.get("arguments", {})
        if not isinstance(arguments, dict):
          arguments = {}

        # Look up endpoint in registry
        from tool_registry import get_tool
        tool_def = get_tool(tool_name)
        if not tool_def:
          logger.warning("burp_agent: model requested unknown tool %r", tool_name)
          messages.append({
            "role": "tool",
            "content": f"Tool '{tool_name}' is not available. Choose a different approach.",
          })
          continue

        # Store the pending tool info and emit confirm request
        sess["pending_tool"] = {
          "tool_name": tool_name,
          "tool_endpoint": tool_def["endpoint"],
          "arguments": arguments,
          "description": tool_def.get("desc", ""),
        }
        sess["status"] = "waiting_confirm"
        confirm_event.clear()

        push(_sse("TOOL_CONFIRM_REQUEST", {
          "tool_name": tool_name,
          "arguments": arguments,
          "description": tool_def.get("desc", ""),
        }))

        # Block until operator confirms or cancels
        logger.debug("burp_agent: session %s waiting for tool confirm (%s)", session_id, tool_name)
        while not confirm_event.wait(timeout=1.0):
          if cancel.is_set():
            push(_sse("CANCELLED"))
            sess["status"] = "cancelled"
            push(_sse("DONE"))
            return

        sess["status"] = "running"
        approved: bool = sess.get("confirm_approved", False)

        if approved:
          push(_sse("TOOL_EXECUTING", {"tool_name": tool_name, "arguments": arguments}))
          logger.info("burp_agent: executing tool %r for session %s", tool_name, session_id)
          tool_result = internal_api.run_tool(tool_def["endpoint"], arguments)
          result_text = json.dumps(tool_result, indent=2)
          if len(result_text) > 4000:
            result_text = result_text[:4000] + "\n... (truncated)"
          push(_sse("TOOL_RESULT", {"tool_name": tool_name, "result": result_text}))
          messages.append({
            "role": "tool",
            "content": f"Tool '{tool_name}' result:\n{result_text}",
          })
        else:
          push(_sse("TOKEN", f"\n\n*[Tool call '{tool_name}' was rejected by operator.]*\n\n"))
          messages.append({
            "role": "tool",
            "content": f"The operator rejected the call to '{tool_name}'. Do not call it again.",
          })

        # Continue the loop for the LLM to interpret the result
        push(_sse("THINKING"))
        continue

      # No tool call — LLM gave a final response
      break

    # 8. Emit the assembled final response
    final_content_parts = [
      m["content"] for m in messages
      if m["role"] == "assistant" and m["content"]
    ]
    final_response = "\n\n".join(final_content_parts) if final_content_parts else content
    push(_sse("FINAL_RESPONSE", final_response))
    sess["status"] = "done"
    push(_sse("DONE"))

  except Exception as exc:
    logger.exception("burp_agent: unhandled error in session %s: %s", session_id, exc)
    try:
      push(_sse("ERROR", str(exc)))
      sess["status"] = "error"
      push(_sse("DONE"))
    except Exception:
      pass


# ── Endpoints ─────────────────────────────────────────────────────────────────

@api_burp_agent_bp.route("/api/burp/agent/start", methods=["POST"])
def start_agent():
  """Start an autonomous Burp agent session.

  Request body:
    http_request  (str, required): Raw HTTP request text captured by Burp.
    http_response (str, optional): Raw HTTP response text captured by Burp.
    context       (str, optional): Free-text operator notes / target scope.

  Response:
    { success: true, session_id: str }
  """
  _gc_sessions()

  try:
    if not llm_client.is_available():
      return jsonify({"success": False, "error": "LLM is not available"}), 503

    body = request.get_json(force=True, silent=True) or {}
    http_request = (body.get("http_request") or "").strip()
    http_response = (body.get("http_response") or "").strip()

    if not http_request:
      return jsonify({"success": False, "error": "http_request is required"}), 400

    session_id = uuid.uuid4().hex

    sess: Dict[str, Any] = {
      "session_id": session_id,
      "status": "running",
      "queue": queue.Queue(maxsize=_QUEUE_MAX),
      "confirm_event": threading.Event(),
      "confirm_approved": False,
      "cancel_event": threading.Event(),
      "created_at": time.time(),
      "pending_tool": None,
    }

    with _sessions_lock:
      _sessions[session_id] = sess

    t = threading.Thread(
      target=_run_agent,
      args=(session_id, http_request, http_response),
      daemon=True,
      name=f"burp-agent-{session_id[:8]}",
    )
    t.start()

    logger.info("burp_agent: started session %s", session_id)
    return jsonify({"success": True, "session_id": session_id})

  except Exception as exc:
    logger.error("burp_agent start: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_burp_agent_bp.route("/api/burp/agent/<session_id>/stream", methods=["GET"])
def stream_agent(session_id: str):
  """Stream SSE events for a running agent session.

  Produces text/event-stream.  The client should read until [DONE] or
  [CANCELLED] is received, or the connection is closed.
  """
  sess = _get_session(session_id)
  if not sess:
    return jsonify({"success": False, "error": "Session not found"}), 404

  def generate():
    q: queue.Queue = sess["queue"]
    # Send a keep-alive comment immediately so the client knows the stream is live
    yield ": connected\n\n"
    while True:
      try:
        event = q.get(timeout=25)
        yield event
        if "[DONE]" in event or "[CANCELLED]" in event:
          break
      except queue.Empty:
        # Send SSE keep-alive comment to prevent proxy timeouts
        yield ": keepalive\n\n"
      except GeneratorExit:
        break

  return Response(
    stream_with_context(generate()),
    mimetype="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
      "Connection": "keep-alive",
    },
  )


@api_burp_agent_bp.route("/api/burp/agent/<session_id>/confirm", methods=["POST"])
def confirm_tool(session_id: str):
  """Approve or reject a pending tool call.

  Request body:
    approved (bool): true to execute the tool, false to skip.

  Response:
    { success: true }
  """
  try:
    sess = _get_session(session_id)
    if not sess:
      return jsonify({"success": False, "error": "Session not found"}), 404

    if sess["status"] != "waiting_confirm":
      return jsonify({"success": False, "error": "No tool call pending for this session"}), 409

    body = request.get_json(force=True, silent=True) or {}
    approved = bool(body.get("approved", False))

    sess["confirm_approved"] = approved
    sess["confirm_event"].set()

    action = "approved" if approved else "rejected"
    tool_name = (sess.get("pending_tool") or {}).get("tool_name", "unknown")
    logger.info("burp_agent: operator %s tool %r for session %s", action, tool_name, session_id)
    return jsonify({"success": True, "action": action, "tool_name": tool_name})

  except Exception as exc:
    logger.error("burp_agent confirm: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_burp_agent_bp.route("/api/burp/agent/<session_id>/cancel", methods=["POST"])
def cancel_agent(session_id: str):
  """Cancel a running agent session.

  Response:
    { success: true }
  """
  try:
    sess = _get_session(session_id)
    if not sess:
      return jsonify({"success": False, "error": "Session not found"}), 404

    sess["cancel_event"].set()
    # Unblock any waiting confirm so the cancel propagates immediately
    sess["confirm_event"].set()
    logger.info("burp_agent: session %s cancelled by operator", session_id)
    return jsonify({"success": True})

  except Exception as exc:
    logger.error("burp_agent cancel: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_burp_agent_bp.route("/api/burp/agent/<session_id>/status", methods=["GET"])
def get_agent_status(session_id: str):
  """Return current status of an agent session.

  Response:
    { success: true, status: str, pending_tool: dict|null }
  """
  try:
    sess = _get_session(session_id)
    if not sess:
      return jsonify({"success": False, "error": "Session not found"}), 404
    return jsonify({
      "success": True,
      "status": sess["status"],
      "pending_tool": sess.get("pending_tool"),
    })
  except Exception as exc:
    logger.error("burp_agent status: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500
