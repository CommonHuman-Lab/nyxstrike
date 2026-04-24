"""
server_core/llm_client.py

Provider-agnostic LLM adapter for NyxStrike.

Selects a backend at construction time based on config/env vars and exposes a
single chat() method. All feature code calls LLMClient — never a backend
directly — so swapping providers is a one-line config change.

Supported backends:
  ollama     — local Ollama server (default, no API key needed)
  openai     — OpenAI or Azure OpenAI via the openai SDK
  anthropic  — Anthropic Claude via the anthropic SDK

Config keys (checked in order: env var → config_local.json → config.py defaults):
  NYXSTRIKE_LLM_PROVIDER    ollama | openai | anthropic
  NYXSTRIKE_LLM_MODEL       model name
  NYXSTRIKE_LLM_URL         base URL for API (Ollama only)
  NYXSTRIKE_LLM_API_KEY     API key (not needed for Ollama)
  NYXSTRIKE_LLM_MAX_LOOPS   max agentic tool loops
  NYXSTRIKE_LLM_TIMEOUT     request timeout in seconds
  NYXSTRIKE_LLM_THINK       enable model thinking/reasoning (default: false, Ollama only)

Defaults are defined in config.py and can be overridden via config_local.json
or environment variables without touching source code.

Usage:
  from server_core.singletons import llm_client
  if llm_client.is_available():
      response = llm_client.chat([{"role": "user", "content": "Hello"}])
"""

import logging
import json
import os
from typing import Generator, List, Dict, Any, Optional

import requests

import server_core.config_core as config_core

logger = logging.getLogger(__name__)


def _cfg(key: str, default: str = "") -> str:
  """Read config: env var overrides config_core, which overrides default."""
  return os.environ.get(key) or config_core.get(key, default)


DEFAULT_OLLAMA_URL = "http://localhost:11434"

# ── Backend implementations ────────────────────────────────────────────────────

class OllamaBackend:
  """Ollama local model server backend."""

  def __init__(self, base_url: str, model: str, timeout: int, think: bool = False, num_ctx: int = 4096) -> None:
    self._base_url = base_url.rstrip("/")
    self._model = model
    self._timeout = timeout
    self._think = think
    self._num_ctx = num_ctx
    self._chat_url = f"{self._base_url}/api/chat"
    self._tags_url = f"{self._base_url}/api/tags"

  def chat(self, messages: List[Dict[str, Any]], stop: List[str] = [], think: Optional[bool] = None, num_ctx: Optional[int] = None, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Send messages to Ollama /api/chat and return the response.

    When ``tools`` is provided the model may return tool_calls instead of (or
    in addition to) plain text content.  The return value is always a dict:
      {"content": str, "tool_calls": list | None}

    When called without tools the content string is still the primary value;
    callers that only care about text can do ``result["content"]``.
    """
    payload: Dict[str, Any] = {
      "model": self._model,
      "messages": messages,
      "stream": False,
      "think": think if think is not None else self._think,
      "options": {"num_ctx": num_ctx or self._num_ctx},
    }
    if stop:
      payload["options"]["stop"] = stop
    if tools:
      payload["tools"] = tools

    try:
      resp = requests.post(self._chat_url, json=payload, timeout=self._timeout)
      resp.raise_for_status()
      data = resp.json()
      msg = data.get("message", {})
      return {
        "content": (msg.get("content") or "").strip(),
        "tool_calls": msg.get("tool_calls") or None,
      }
    except requests.exceptions.ConnectionError:
      raise RuntimeError(
        f"Cannot connect to Ollama at {self._base_url}. "
        "Is the server running? Try: ollama serve"
      )
    except requests.exceptions.Timeout:
      raise RuntimeError(
        f"Ollama request timed out after {self._timeout}s. "
        "The model may still be loading — try again in a moment"
      )
    except requests.exceptions.HTTPError as exc:
      raise RuntimeError(f"Ollama HTTP error: {exc}")

  def is_available(self) -> bool:
    """Return True if Ollama is reachable and the configured model exists."""
    try:
      resp = requests.get(self._tags_url, timeout=5)
      if resp.status_code != 200:
        return False
      # Check that the model is actually pulled
      models = [m.get("name", "") for m in resp.json().get("models", [])]
      # Match prefix — "llama3.2" matches "llama3.2:latest"
      return any(m.startswith(self._model) for m in models)
    except Exception:
      return False

  def warm_up(self) -> None:
    """Send a minimal prompt to pre-load the model into memory.

    Called once at server startup in a background thread so the first real
    request does not stall waiting for the model to cold-load.
    """
    if not self.is_available():
      logger.warning("Ollama warm-up skipped: model '%s' not available.", self._model)
      return
    try:
      logger.info("Warming up Ollama model '%s'...", self._model)
      requests.post(
        self._chat_url,
        json={
          "model": self._model,
          "messages": [{"role": "user", "content": "hi"}],
          "stream": False,
          "think": False,
          "options": {"num_predict": 1},
        },
        timeout=self._timeout,
      )
      logger.info("Ollama model '%s' warm-up complete.", self._model)
    except Exception as exc:
      logger.warning("Ollama warm-up failed (non-fatal): %s", exc)

  def stream_chat(self, messages: List[Dict[str, Any]], num_ctx: Optional[int] = None) -> Generator:
    """Stream tokens from Ollama one chunk at a time via NDJSON.

    Yields:
      str — content token chunks
      dict — final item: response stats (eval_count, duration, tokens/sec, etc.)
    """
    keep_alive = int(os.environ.get("NYXSTRIKE_LLM_KEEP_ALIVE") or 300)
    payload: Dict[str, Any] = {
      "model": self._model,
      "messages": messages,
      "stream": True,
      "think": self._think,
      "keep_alive": keep_alive,
      "options": {"num_ctx": num_ctx or self._num_ctx},
    }
    try:
      with requests.post(self._chat_url, json=payload, timeout=self._timeout, stream=True) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
          if not line:
            continue
          try:
            data = json.loads(line)
          except json.JSONDecodeError:
            continue
          chunk = data.get("message", {}).get("content", "")
          if chunk:
            yield chunk
          if data.get("done"):
            # Extract stats from the final chunk
            eval_count = data.get("eval_count", 0)
            eval_duration = data.get("eval_duration", 0)
            total_duration = data.get("total_duration", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)
            # Durations are in nanoseconds
            eval_secs = eval_duration / 1e9 if eval_duration else 0
            total_secs = total_duration / 1e9 if total_duration else 0
            tokens_per_sec = eval_count / eval_secs if eval_secs > 0 else 0
            yield {
              "eval_count": eval_count,
              "prompt_eval_count": prompt_eval_count,
              "total_duration_s": round(total_secs, 2),
              "eval_duration_s": round(eval_secs, 2),
              "tokens_per_sec": round(tokens_per_sec, 1),
            }
            break
    except requests.exceptions.ConnectionError:
      raise RuntimeError(f"Cannot connect to Ollama at {self._base_url}.")
    except requests.exceptions.Timeout:
      raise RuntimeError(f"Ollama stream timed out after {self._timeout}s.")
    except requests.exceptions.HTTPError as exc:
      raise RuntimeError(f"Ollama HTTP error: {exc}")

  def generate_summary(self, messages: List[Dict[str, Any]]) -> str:
    """Summarize a list of messages into a short paragraph (non-streaming)."""
    conversation = "\n".join(
      f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )
    summary_prompt = (
      "Summarize the following conversation in 2-3 sentences, "
      "preserving key facts, targets, commands, and findings. "
      "Be concise and technical.\n\n" + conversation
    )
    result = self.chat([{"role": "user", "content": summary_prompt}])
    return result["content"] if isinstance(result, dict) else result

  @property
  def provider(self) -> str:
    return "ollama"

  @property
  def model(self) -> str:
    return self._model

class OpenAIBackend:
  """OpenAI / Azure OpenAI backend via the openai SDK."""

  def __init__(self, model: str, api_key: str, base_url: Optional[str], timeout: int) -> None:
    self._model = model
    self._timeout = timeout
    try:
      import openai  # noqa: F401 — optional dependency
      self._openai = openai
      kwargs: Dict[str, Any] = {"api_key": api_key}
      if base_url:
        kwargs["base_url"] = base_url
      self._client = openai.OpenAI(**kwargs)
    except ImportError:
      raise RuntimeError(
        "openai SDK not installed. Run: pip install openai"
      )

  def chat(self, messages: List[Dict[str, Any]], stop: List[str] = [], think: Optional[bool] = None, num_ctx: Optional[int] = None) -> str:
    kwargs: Dict[str, Any] = {
      "model": self._model,
      "messages": messages,
      "max_tokens": 4096,
      "temperature": 0.7,
    }
    if stop:
      kwargs["stop"] = stop
    try:
      resp = self._client.chat.completions.create(**kwargs)
      return resp.choices[0].message.content.strip()
    except Exception as exc:
      raise RuntimeError(f"OpenAI API error: {exc}")

  def stream_chat(self, messages: List[Dict[str, Any]], num_ctx: Optional[int] = None) -> Generator[str, None, None]:
    """Stream tokens from OpenAI one delta at a time."""
    kwargs: Dict[str, Any] = {
      "model": self._model,
      "messages": messages,
      "max_tokens": 4096,
      "temperature": 0.7,
      "stream": True,
    }
    try:
      stream = self._client.chat.completions.create(**kwargs)
      for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
          yield delta
    except Exception as exc:
      raise RuntimeError(f"OpenAI streaming error: {exc}")

  def generate_summary(self, messages: List[Dict[str, Any]]) -> str:
    """Summarize a list of messages into a short paragraph (non-streaming)."""
    conversation = "\n".join(
      f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )
    summary_prompt = (
      "Summarize the following conversation in 2-3 sentences, "
      "preserving key facts, targets, commands, and findings. "
      "Be concise and technical.\n\n" + conversation
    )
    return self.chat([{"role": "user", "content": summary_prompt}])

  def is_available(self) -> bool:
    return True

  @property
  def provider(self) -> str:
    return "openai"

  @property
  def model(self) -> str:
    return self._model


class AnthropicBackend:
  """Anthropic Claude backend via the anthropic SDK."""

  def __init__(self, model: str, api_key: str, timeout: int) -> None:
    self._model = model
    self._timeout = timeout
    try:
      import anthropic  # noqa: F401 — optional dependency
      self._client = anthropic.Anthropic(api_key=api_key)
    except ImportError:
      raise RuntimeError(
        "anthropic SDK not installed. Run: pip install anthropic"
      )

  def chat(self, messages: List[Dict[str, Any]], stop: List[str] = [], think: Optional[bool] = None, num_ctx: Optional[int] = None) -> str:
    # Anthropic separates system from human/assistant messages
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]
    system_text = "\n\n".join(system_parts)
    kwargs: Dict[str, Any] = {
      "model": self._model,
      "max_tokens": 4096,
      "messages": user_messages,
    }
    if system_text:
      kwargs["system"] = system_text
    if stop:
      kwargs["stop_sequences"] = stop
    try:
      resp = self._client.messages.create(**kwargs)
      return resp.content[0].text.strip()
    except Exception as exc:
      raise RuntimeError(f"Anthropic API error: {exc}")

  def stream_chat(self, messages: List[Dict[str, Any]], num_ctx: Optional[int] = None) -> Generator[str, None, None]:
    """Stream tokens from Anthropic one delta at a time."""
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]
    system_text = "\n\n".join(system_parts)
    kwargs: Dict[str, Any] = {
      "model": self._model,
      "max_tokens": 4096,
      "messages": user_messages,
    }
    if system_text:
      kwargs["system"] = system_text
    try:
      with self._client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
          if text:
            yield text
    except Exception as exc:
      raise RuntimeError(f"Anthropic streaming error: {exc}")

  def generate_summary(self, messages: List[Dict[str, Any]]) -> str:
    """Summarize a list of messages into a short paragraph (non-streaming)."""
    conversation = "\n".join(
      f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )
    summary_prompt = (
      "Summarize the following conversation in 2-3 sentences, "
      "preserving key facts, targets, commands, and findings. "
      "Be concise and technical.\n\n" + conversation
    )
    return self.chat([{"role": "user", "content": summary_prompt}])

  def is_available(self) -> bool:
    try:
      # Cheap check — list models endpoint
      self._client.models.list()
      return True
    except Exception:
      return False

  @property
  def provider(self) -> str:
    return "anthropic"

  @property
  def model(self) -> str:
    return self._model


# ── Public facade ─────────────────────────────────────────────────────────────

class LLMClient:
  """Provider-agnostic LLM client.

  Reads configuration at construction time and builds the appropriate backend.
  If construction fails (e.g. missing SDK, bad config), is_available() returns
  False and chat() raises RuntimeError — callers should guard with is_available().

  Attributes exposed for logging / persistence:
    provider  — "ollama" | "openai" | "anthropic"
    model     — model name string
    max_loops — configured maximum tool dispatch loops
  """

  def __init__(self) -> None:
    self.max_loops: int = int(_cfg("NYXSTRIKE_LLM_MAX_LOOPS") or 9)
    self._backend: Any = None
    self._init_error: str = ""

    # Only initialise a backend when AI mode is explicitly enabled..
    import os as _os
    if _os.environ.get("NYXSTRIKE_LLM_WARMUP") != "1":
      return

    provider = _cfg("NYXSTRIKE_LLM_PROVIDER").lower()
    model = _cfg("NYXSTRIKE_LLM_MODEL")
    base_url = _cfg("NYXSTRIKE_LLM_URL")
    api_key = _cfg("NYXSTRIKE_LLM_API_KEY")
    timeout = int(_cfg("NYXSTRIKE_LLM_TIMEOUT") or 300)
    think_raw = _cfg("NYXSTRIKE_LLM_THINK")
    think = str(think_raw).lower() in ("1", "true", "yes")
    num_ctx = int(_cfg("NYXSTRIKE_LLM_NUM_CTX") or 4096)
    self._num_ctx_analyse = int(_cfg("NYXSTRIKE_LLM_NUM_CTX_ANALYSE") or 16384)

    try:
      if provider == "ollama":
        self._backend = OllamaBackend(base_url, model, timeout, think, num_ctx)
      elif provider == "openai":
        self._backend = OpenAIBackend(model, api_key, base_url if base_url != DEFAULT_OLLAMA_URL else None, timeout)
      elif provider == "anthropic":
        self._backend = AnthropicBackend(model, api_key, timeout)
      else:
        raise ValueError(f"Unknown LLM provider: {provider!r}. Choose: ollama, openai, anthropic")

      logger.info(
        "llm_client: initialized provider=%s model=%s",
        self._backend.provider,
        self._backend.model,
      )
    except Exception as exc:
      self._init_error = str(exc)
      logger.warning("llm_client: initialization failed — %s", exc)

  @property
  def provider(self) -> str:
    return self._backend.provider if self._backend else "none"

  @property
  def model(self) -> str:
    return self._backend.model if self._backend else ""

  @property
  def num_ctx_analyse(self) -> int:
    return getattr(self, '_num_ctx_analyse', 16384)

  def is_available(self) -> bool:
    """Return True if the LLM backend is reachable. Never raises."""
    if self._backend is None:
      return False
    try:
      return self._backend.is_available()
    except Exception:
      return False

  def warm_up(self) -> None:
    """Pre-load the model into memory. No-op for non-Ollama backends."""
    if self._backend is None:
      return
    if hasattr(self._backend, "warm_up"):
      self._backend.warm_up()

  def chat(self, messages: List[Dict[str, Any]], stop: List[str] = [], think: Optional[bool] = None, num_ctx: Optional[int] = None, tools: Optional[List[Dict[str, Any]]] = None) -> Any:
    """Send messages and return the model's response.

    When ``tools`` is omitted (the common case) returns a plain ``str``.
    When ``tools`` is provided returns a dict:
      {"content": str, "tool_calls": list | None}
    so callers can inspect requested tool invocations.

    Args:
      messages: List of {"role": "system"|"user"|"assistant", "content": str}
      stop:     Optional stop sequences.
      think:    Override thinking mode for this call (None = use default).
      num_ctx:  Override context window size for this call (None = use default).
      tools:    Optional list of Ollama-format tool schemas.  If provided the
                model may respond with tool_calls instead of plain text.

    Raises:
      RuntimeError: If the backend is not initialized or the call fails.
    """
    if self._backend is None:
      raise RuntimeError(
        f"LLM client not initialized: {self._init_error or 'unknown error'}"
      )
    # Only OllamaBackend accepts tools; other backends fall back to plain text.
    if tools and hasattr(self._backend, 'chat'):
      try:
        result = self._backend.chat(messages, stop, think=think, num_ctx=num_ctx, tools=tools)
      except TypeError:
        # Backend doesn't accept tools kwarg — strip and call without
        result = self._backend.chat(messages, stop, think=think, num_ctx=num_ctx)
      # Normalise: if the backend returned a plain string, box it up
      if isinstance(result, str):
        return result
      return result  # dict with content + tool_calls
    # No tools requested — return plain string for backward compat
    result = self._backend.chat(messages, stop, think=think, num_ctx=num_ctx)
    if isinstance(result, dict):
      return result["content"]
    return result

  def stream_chat(self, messages: List[Dict[str, Any]], num_ctx: Optional[int] = None) -> Generator:
    """Stream the model's response token-by-token.

    Args:
      messages: List of {"role": "system"|"user"|"assistant", "content": str}
      num_ctx:  Override context window size (None = use default).

    Yields:
      String chunks as they arrive from the model.

    Raises:
      RuntimeError: If the backend is not initialized or streaming fails.
    """
    if self._backend is None:
      raise RuntimeError(
        f"LLM client not initialized: {self._init_error or 'unknown error'}"
      )
    if not hasattr(self._backend, "stream_chat"):
      raise RuntimeError(f"Backend {self.provider!r} does not support streaming")
    yield from self._backend.stream_chat(messages, num_ctx=num_ctx)

  def generate_summary(self, messages: List[Dict[str, Any]]) -> str:
    """Summarize a message list into a short paragraph.

    Used for rolling context compression in chat sessions.
    Falls back to non-streaming chat() internally.

    Raises:
      RuntimeError: If the backend is not initialized or the call fails.
    """
    if self._backend is None:
      raise RuntimeError(
        f"LLM client not initialized: {self._init_error or 'unknown error'}"
      )
    if hasattr(self._backend, "generate_summary"):
      return self._backend.generate_summary(messages)
    # Fallback: use chat() directly
    conversation = "\n".join(
      f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )
    prompt = (
      "Summarize the following conversation in 2-3 sentences, "
      "preserving key facts, targets, commands, and findings. "
      "Be concise and technical.\n\n" + conversation
    )
    return self.chat([{"role": "user", "content": prompt}])

  def status(self) -> Dict[str, Any]:
    """Return a status dict suitable for the /llm-status health endpoint."""
    available = self.is_available()
    return {
      "available": available,
      "provider": self.provider,
      "model": self.model,
      "max_loops": self.max_loops,
      "error": self._init_error if not available else "",
    }
