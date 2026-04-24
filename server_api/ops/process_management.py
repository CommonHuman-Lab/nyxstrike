
"""
Process management API endpoints (list, status, terminate, pause, resume, dashboard).
"""

import time
from flask import Blueprint, jsonify, Response, stream_with_context
from datetime import datetime
import psutil
from server_core.process_manager import ProcessManager, AITaskManager
from server_core.modern_visual_engine import ModernVisualEngine
from server_core.singletons import enhanced_process_manager
import logging
import json
logger = logging.getLogger(__name__)

api_process_management_bp = Blueprint("process_management", __name__)


def _annotate_process(info: dict, now: float = 0.0) -> None:
    """Mutate a process info dict to add runtime_formatted and eta_formatted."""
    if not now:
        now = time.time()
    runtime = now - info["start_time"]
    info["runtime_formatted"] = f"{runtime:.1f}s"
    if info["progress"] > 0:
        eta = (runtime / info["progress"]) * (1.0 - info["progress"])
        info["eta_formatted"] = f"{eta:.1f}s"
    else:
        info["eta_formatted"] = "Unknown"


def _json_safe_process(info: dict) -> dict:
    """Return a JSON-safe copy of process info."""
    safe = dict(info)
    safe.pop("process", None)
    return safe

@api_process_management_bp.route("/api/processes/list", methods=["GET"])
def list_processes():
    """List all active processes"""
    try:
        processes = ProcessManager.list_active_processes()

        # Add calculated fields for each process
        safe_processes = {}
        for pid, info in processes.items():
            _annotate_process(info)
            safe_processes[str(pid)] = _json_safe_process(info)

        # Merge in-process AI tasks so the frontend running-step check sees them
        ai_tasks = AITaskManager.list_active_tasks()
        for task_id, info in ai_tasks.items():
            safe_processes[f"ai:{task_id}"] = {
                "pid": None,
                "task_id": task_id,
                "command": info.get("label", "ai_task"),
                "status": info.get("status", "running"),
                "start_time": info.get("start_time", 0),
                "progress": 0.0,
                "last_output": "",
                "bytes_processed": 0,
                "session_id": info.get("session_id", ""),
                "ai_task": True,
            }

        return jsonify({
            "success": True,
            "active_processes": safe_processes,
            "total_count": len(safe_processes)
        })
    except Exception as e:
        logger.error(f"💥 Error listing processes: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_process_management_bp.route("/api/processes/status/<int:pid>", methods=["GET"])
def get_process_status(pid):
    """Get status of a specific process"""
    try:
        process_info = ProcessManager.get_process_status(pid)

        if process_info:
            # Add calculated fields
            _annotate_process(process_info)

            return jsonify({
                "success": True,
                "process": _json_safe_process(process_info)
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Process {pid} not found"
            }), 404

    except Exception as e:
        logger.error(f"💥 Error getting process status: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_process_management_bp.route("/api/processes/terminate/<int:pid>", methods=["POST"])
def terminate_process(pid):
    """Terminate a specific process"""
    try:
        success = ProcessManager.terminate_process(pid)

        if success:
            logger.info(f"🛑 Process {pid} terminated successfully")
            return jsonify({
                "success": True,
                "message": f"Process {pid} terminated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to terminate process {pid} or process not found"
            }), 404

    except Exception as e:
        logger.error(f"💥 Error terminating process {pid}: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_process_management_bp.route("/api/processes/cancel-ai-task/<task_id>", methods=["POST"])
def cancel_ai_task(task_id: str):
    """Cancel an in-process AI task by its task_id (e.g. ai_analyze_xxxxxxxx).

    The underlying LLM HTTP call cannot be interrupted immediately, but the
    task is removed from the visible registry at once so the UI reflects the
    cancellation without delay.
    """
    try:
        found = AITaskManager.cancel_task(task_id)
        if found:
            logger.info(f"🛑 AI task {task_id} cancel requested")
            return jsonify({"success": True, "message": f"AI task {task_id} cancelled"})
        return jsonify({"success": False, "error": f"AI task {task_id} not found"}), 404
    except Exception as e:
        logger.error(f"💥 Error cancelling AI task {task_id}: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_process_management_bp.route("/api/processes/pause/<int:pid>", methods=["POST"])
def pause_process(pid):
    """Pause a specific process"""
    try:
        success = ProcessManager.pause_process(pid)

        if success:
            logger.info(f"⏸️ Process {pid} paused successfully")
            return jsonify({
                "success": True,
                "message": f"Process {pid} paused successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to pause process {pid} or process not found"
            }), 404

    except Exception as e:
        logger.error(f"💥 Error pausing process {pid}: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@api_process_management_bp.route("/api/processes/resume/<int:pid>", methods=["POST"])
def resume_process(pid):
    """Resume a paused process"""
    try:
        success = ProcessManager.resume_process(pid)

        if success:
            logger.info(f"▶️ Process {pid} resumed successfully")
            return jsonify({
                "success": True,
                "message": f"Process {pid} resumed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to resume process {pid} or process not found"
            }), 404

    except Exception as e:
        logger.error(f"💥 Error resuming process {pid}: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def _build_dashboard_payload() -> dict:
    """Build the dashboard dict including both OS processes and in-process AI tasks."""
    processes = ProcessManager.list_active_processes()
    current_time = time.time()
    dashboard_visual = ModernVisualEngine.create_live_dashboard(processes)

    entries = []

    for pid, info in processes.items():
        runtime = current_time - info["start_time"]
        progress_fraction = info.get("progress", 0)
        progress_bar = ModernVisualEngine.render_progress_bar(
            progress_fraction,
            width=25,
            style='cyber',
            eta=info.get("eta", 0)
        )
        entries.append({
            "pid": pid,
            "command": info["command"][:60] + "..." if len(info["command"]) > 60 else info["command"],
            "status": info["status"],
            "runtime": f"{runtime:.1f}s",
            "progress_percent": f"{progress_fraction * 100:.1f}%",
            "progress_bar": progress_bar,
            "eta": f"{info.get('eta', 0):.0f}s" if info.get('eta', 0) > 0 else "Calculating...",
            "bytes_processed": info.get("bytes_processed", 0),
            "last_output": info.get("last_output", "")[:100],
            "ai_task": False,
            "task_id": None,
        })

    # Merge in-process AI tasks (no OS PID)
    for task_id, info in AITaskManager.list_active_tasks().items():
        runtime = current_time - info.get("start_time", current_time)
        entries.append({
            "pid": None,
            "task_id": task_id,
            "command": info.get("label", "ai_task"),
            "status": info.get("status", "running"),
            "runtime": f"{runtime:.1f}s",
            "progress_percent": "—",
            "progress_bar": "",
            "eta": "—",
            "bytes_processed": 0,
            "last_output": "",
            "ai_task": True,
            "session_id": info.get("session_id", ""),
        })

    total = len(processes) + len(AITaskManager.list_active_tasks())
    return {
        "timestamp": datetime.now().isoformat(),
        "total_processes": total,
        "visual_dashboard": dashboard_visual,
        "processes": entries,
        "system_load": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "active_connections": len(psutil.net_connections())
        }
    }


@api_process_management_bp.route("/api/processes/dashboard", methods=["GET"])
def process_dashboard():
    """Get enhanced process dashboard with visual status using ModernVisualEngine"""
    try:
        return jsonify(_build_dashboard_payload())
    except Exception as e:
        logger.error(f"💥 Error getting process dashboard: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# --- STREAMING ENDPOINTS ---
@api_process_management_bp.route("/api/processes/dashboard/stream", methods=["GET"])
def stream_process_dashboard():
    """
    SSE endpoint — streams the latest process dashboard state every 2 seconds.
    """
    _VOLATILE_DASHBOARD_KEYS = {"timestamp", "system_load"}

    def generate():
        last_stable = None
        while True:
            try:
                dashboard = _build_dashboard_payload()
                # Exclude timestamp and system_load (cpu/mem/connections change
                # every tick) so a keepalive is sent when process state is
                # unchanged rather than emitting a duplicate data event.
                stable = json.dumps(
                    {k: v for k, v in dashboard.items() if k not in _VOLATILE_DASHBOARD_KEYS},
                    separators=(",", ":"),
                    sort_keys=True,
                )
                if stable != last_stable:
                    yield f"data: {json.dumps(dashboard, separators=(',', ':'))}\n\n"
                    last_stable = stable
                else:
                    yield ": keepalive\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            time.sleep(2)
    return Response(stream_with_context(generate()), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _build_processes_stream_payload() -> dict:
    """Build a clean, structured payload combining process list and pool stats.

    Unlike _build_dashboard_payload(), this omits the ASCII visual_dashboard
    and emits structured data suitable for direct UI consumption.
    """
    processes = ProcessManager.list_active_processes()
    current_time = time.time()

    safe_processes: dict = {}
    for pid, info in processes.items():
        _annotate_process(info, now=current_time)
        safe_processes[str(pid)] = _json_safe_process(info)

    for task_id, info in AITaskManager.list_active_tasks().items():
        safe_processes[f"ai:{task_id}"] = {
            "pid": None,
            "task_id": task_id,
            "command": info.get("label", "ai_task"),
            "status": info.get("status", "running"),
            "start_time": info.get("start_time", current_time),
            "progress": 0.0,
            "last_output": "",
            "bytes_processed": 0,
            "session_id": info.get("session_id", ""),
            "ai_task": True,
        }

    try:
        pool_stats = enhanced_process_manager.get_comprehensive_stats()
    except Exception:
        pool_stats = {}

    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "processes": safe_processes,
        "total_count": len(safe_processes),
        "system_load": {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "active_connections": len(psutil.net_connections()),
        },
        "pool_stats": pool_stats,
    }


@api_process_management_bp.route("/api/processes/stream", methods=["GET"])
def stream_processes():
    """SSE endpoint — unified process list + pool stats stream.

    Emits a structured JSON payload every 2 seconds.  Only sends a data event
    when the payload changes; keepalive comments are sent otherwise so the
    connection stays open through proxies.

    Replaces the dual /api/processes/dashboard/stream +
    /api/process/pool-stats/stream pattern used by the Tasks UI.
    """
    _VOLATILE_STREAM_KEYS = {"timestamp", "system_load"}

    def generate():
        last_stable = None
        while True:
            try:
                payload = _build_processes_stream_payload()
                stable = json.dumps(
                    {k: v for k, v in payload.items() if k not in _VOLATILE_STREAM_KEYS},
                    separators=(",", ":"),
                    sort_keys=True,
                )
                if stable != last_stable:
                    yield f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"
                    last_stable = stable
                else:
                    yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"💥 Error in /api/processes/stream: {e}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            time.sleep(2)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
