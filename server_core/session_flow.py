import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from server_core.singletons import session_store


def now_ts() -> int:
    return int(time.time())


def generate_session_id(prefix: str = "sess") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _infer_param_value(param_name: str, target: str) -> Optional[str]:
    key = (param_name or "").lower()
    if key in ["target", "host", "query"]:
        return target
    if key in ["url", "endpoint"]:
        if target.startswith("http://") or target.startswith("https://"):
            return target
        return f"https://{target}"
    if key == "domain":
        return target.replace("http://", "").replace("https://", "").split("/")[0]
    return None


def _sanitize_parameters(value: Any) -> Any:
    """Strip noisy/internal keys from persisted step parameters."""
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and k.startswith("_"):
                continue
            cleaned[k] = _sanitize_parameters(v)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_parameters(v) for v in value]
    return value


def normalize_step(step: Any, target: str = "") -> Optional[Dict[str, Any]]:
    if isinstance(step, str):
        return {"tool": step, "parameters": {}}

    if not isinstance(step, dict):
        return None

    tool = step.get("tool") or step.get("name") or step.get("action")
    if not isinstance(tool, str) or not tool.strip():
        return None

    params = step.get("parameters", step.get("params", {}))
    if not isinstance(params, dict):
        params = {}
    params = _sanitize_parameters(params)

    required = step.get("required_params", {})
    if isinstance(required, dict) and target:
        for param_name in required.keys():
            if params.get(param_name):
                continue
            inferred = _infer_param_value(param_name, target)
            if inferred:
                params[param_name] = inferred

    return {
        "tool": tool,
        "parameters": params,
        "expected_outcome": step.get("expected_outcome", ""),
        "success_probability": step.get("success_probability", 0),
        "execution_time_estimate": step.get("execution_time_estimate", 0),
        "dependencies": step.get("dependencies", []),
    }


def extract_workflow_steps(workflow: Any, target: str = "") -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    seen: set = set()

    def _add_step(candidate: Any):
        normalized = normalize_step(candidate, target)
        if not normalized:
            return
        dedupe_key = (normalized.get("tool", ""), str(normalized.get("parameters", {})))
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)
        steps.append(normalized)

    def _walk(node: Any):
        if isinstance(node, dict):
            if "tool" in node and isinstance(node.get("tool"), str):
                _add_step(node)

            tools = node.get("tools")
            if isinstance(tools, list):
                for item in tools:
                    _add_step(item)

            for value in node.values():
                _walk(value)

        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(workflow)
    return steps


def create_session(
    target: str,
    steps: List[Dict[str, Any]],
    source: str = "web",
    objective: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    name: str = "",
    description: str = "",
) -> Dict[str, Any]:
    ts = now_ts()
    sid = session_id or generate_session_id()
    step_list = [normalize_step(s, target) for s in steps]
    step_list = [s for s in step_list if s]

    session_dict: Dict[str, Any] = {
        "session_id": sid,
        "name": name or "",
        "description": description or "",
        "target": target,
        "status": "active",
        "total_findings": 0,
        "findings": [],
        "iterations": 0,
        "tools_executed": [s["tool"] for s in step_list],
        "workflow_steps": step_list,
        "source": source,
        "objective": objective,
        "handover_history": [],
        "run_log": [],
        "event_log": [
            {
                "type": "session_created",
                "timestamp": ts,
                "message": f"Session created for target: {target}",
                "data": {"source": source, "step_count": len(step_list)},
            }
        ],
        "created_at": ts,
        "updated_at": ts,
    }
    if metadata:
        session_dict["metadata"] = metadata

    session_store.save(sid, session_dict)
    return session_dict


def append_event(session_id: str, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Append an event to the session event log. Non-fatal — fails silently on missing session."""
    loaded = load_session_any(session_id)
    if not loaded:
        return
    session_dict, _state = loaded
    event_log = session_dict.get("event_log", [])
    if not isinstance(event_log, list):
        event_log = []
    event_log.append({
        "type": event_type,
        "timestamp": now_ts(),
        "message": message,
        "data": data or {},
    })
    session_dict["event_log"] = event_log
    session_dict["updated_at"] = now_ts()
    if str(session_dict.get("status", "")).lower() == "completed" or _state == "completed":
        session_store.archive(session_id, session_dict)
    else:
        session_store.save(session_id, session_dict)


def append_run_log(session_id: str, entry: Dict[str, Any]) -> None:
    """Append a tool run entry to the session's run_log. Non-fatal — fails silently."""
    loaded = load_session_any(session_id)
    if not loaded:
        return
    session_dict, _state = loaded
    run_log = session_dict.get("run_log", [])
    if not isinstance(run_log, list):
        run_log = []
    run_log.append(entry)
    session_dict["run_log"] = run_log
    session_dict["updated_at"] = now_ts()
    if str(session_dict.get("status", "")).lower() == "completed" or _state == "completed":
        session_store.archive(session_id, session_dict)
    else:
        session_store.save(session_id, session_dict)


def load_session_any(session_id: str) -> Optional[Tuple[Dict[str, Any], str]]:
    active = session_store.load(session_id)
    if active:
        return active, "active"
    completed = session_store.load_completed(session_id)
    if completed:
        return completed, "completed"
    return None


def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    loaded = load_session_any(session_id)
    if not loaded:
        return None

    session_dict, state = loaded
    ts = now_ts()

    # Track status change for event log
    old_status = str(session_dict.get("status", "")).lower()
    new_status = str(updates.get("status", old_status)).lower()

    for key, value in updates.items():
        session_dict[key] = value

    session_dict["updated_at"] = ts

    if "workflow_steps" in updates and isinstance(updates["workflow_steps"], list):
        steps = [normalize_step(s, session_dict.get("target", "")) for s in updates["workflow_steps"]]
        session_dict["workflow_steps"] = [s for s in steps if s]
        session_dict["tools_executed"] = [s["tool"] for s in session_dict["workflow_steps"]]

    # Auto-append event log entries for notable changes
    event_log = session_dict.get("event_log", [])
    if not isinstance(event_log, list):
        event_log = []

    if new_status != old_status:
        event_log.append({
            "type": "status_changed",
            "timestamp": ts,
            "message": f"Session status changed from {old_status} to {new_status}",
            "data": {"old_status": old_status, "new_status": new_status},
        })

    if "handover_history" in updates and isinstance(updates["handover_history"], list):
        history = updates["handover_history"]
        if history:
            latest = history[-1]
            event_log.append({
                "type": "handover",
                "timestamp": ts,
                "message": f"Session handed over — category: {latest.get('category', 'unknown')}",
                "data": {
                    "category": latest.get("category", "unknown"),
                    "confidence": latest.get("confidence", 0),
                    "note": latest.get("note", ""),
                },
            })

    session_dict["event_log"] = event_log
    target_status = str(session_dict.get("status", "")).lower()

    if target_status == "completed":
        session_store.archive(session_id, session_dict)
    elif state == "completed":
        session_store.archive(session_id, session_dict)
    else:
        session_store.save(session_id, session_dict)

    return session_dict
