# Process management for command termination
import threading
import time
import logging
import os
import signal

active_processes = {}  # pid -> process info
process_lock = threading.Lock()
logger = logging.getLogger(__name__)

class ProcessManager:
    """Enhanced process manager for command termination and monitoring"""

    @staticmethod
    def register_process(pid, command, process_obj):
        """Register a new active process"""
        with process_lock:
            active_processes[pid] = {
                "pid": pid,
                "command": command,
                "process": process_obj,
                "start_time": time.time(),
                "status": "running",
                "progress": 0.0,
                "last_output": "",
                "bytes_processed": 0
            }
            logger.info(f"🆔 REGISTERED: Process {pid} - {command[:50]}...")

    @staticmethod
    def update_process_progress(pid, progress, last_output="", bytes_processed=0):
        """Update process progress and stats"""
        with process_lock:
            if pid in active_processes:
                active_processes[pid]["progress"] = progress
                active_processes[pid]["last_output"] = last_output
                active_processes[pid]["bytes_processed"] = bytes_processed
                runtime = time.time() - active_processes[pid]["start_time"]

                # Calculate ETA if progress > 0
                eta = 0
                if progress > 0:
                    eta = (runtime / progress) * (1.0 - progress)

                active_processes[pid]["runtime"] = runtime
                active_processes[pid]["eta"] = eta

    @staticmethod
    def terminate_process(pid):
        """Terminate a specific process"""
        with process_lock:
            if pid in active_processes:
                process_info = active_processes[pid]
                try:
                    process_obj = process_info["process"]
                    if process_obj and process_obj.poll() is None:
                        process_obj.terminate()
                        time.sleep(1)  # Give it a chance to terminate gracefully
                        if process_obj.poll() is None:
                            process_obj.kill()  # Force kill if still running

                        active_processes[pid]["status"] = "terminated"
                        active_processes.pop(pid, None)
                        logger.warning(f"🛑 TERMINATED: Process {pid} - {process_info['command'][:50]}...")
                        return True
                except Exception as e:
                    logger.error(f"💥 Error terminating process {pid}: {str(e)}")
                    return False
            return False

    @staticmethod
    def cleanup_process(pid):
        """Remove process from active registry"""
        with process_lock:
            if pid in active_processes:
                process_info = active_processes.pop(pid)
                logger.info(f"🧹 CLEANUP: Process {pid} removed from registry")
                return process_info
            return None

    @staticmethod
    def get_process_status(pid):
        """Get status of a specific process"""
        with process_lock:
            return active_processes.get(pid, None)

    @staticmethod
    def list_active_processes():
        """List all active processes"""
        with process_lock:
            return dict(active_processes)

    @staticmethod
    def pause_process(pid):
        """Pause a specific process (SIGSTOP)"""
        with process_lock:
            if pid in active_processes:
                try:
                    process_obj = active_processes[pid]["process"]
                    if process_obj and process_obj.poll() is None:
                        os.kill(pid, signal.SIGSTOP)
                        active_processes[pid]["status"] = "paused"
                        logger.info(f"⏸️  PAUSED: Process {pid}")
                        return True
                except Exception as e:
                    logger.error(f"💥 Error pausing process {pid}: {str(e)}")
            return False

    @staticmethod
    def resume_process(pid):
        """Resume a paused process (SIGCONT)"""
        with process_lock:
            if pid in active_processes:
                try:
                    process_obj = active_processes[pid]["process"]
                    if process_obj and process_obj.poll() is None:
                        os.kill(pid, signal.SIGCONT)
                        active_processes[pid]["status"] = "running"
                        logger.info(f"▶️  RESUMED: Process {pid}")
                        return True
                except Exception as e:
                    logger.error(f"💥 Error resuming process {pid}: {str(e)}")
            return False


# ── In-process AI task tracker ──────────────────────────────────────────────
# Used by built-in tools (e.g. ai_analyze_session) that run entirely inside the
# Flask worker thread and therefore never produce an OS PID.  The frontend polls
# /api/processes/list to decide whether a running-step UI should be restored
# after navigation; merging these tasks into that response closes the gap.

active_ai_tasks = {}  # task_id (str) -> task info dict
ai_task_lock = threading.Lock()


class AITaskManager:
    """Lightweight tracker for in-process AI tasks that have no OS PID."""

    @staticmethod
    def register_task(task_id: str, label: str, session_id: str = "") -> None:
        """Register a new in-flight AI task."""
        with ai_task_lock:
            active_ai_tasks[task_id] = {
                "task_id": task_id,
                "label": label,
                "session_id": session_id,
                "start_time": time.time(),
                "status": "running",
            }
            logger.info("🤖 AI Task: %s — %s", task_id, label)

    @staticmethod
    def unregister_task(task_id: str) -> None:
        """Remove an AI task from the active registry (call in a finally block)."""
        with ai_task_lock:
            if task_id in active_ai_tasks:
                active_ai_tasks.pop(task_id)
                logger.info("🤖 AI TASK DONE: %s", task_id)

    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """Mark an AI task as cancelled and remove it from the visible registry.

        The underlying LLM HTTP call cannot be interrupted mid-flight, but
        marking the task cancelled immediately hides it from the UI.  The
        ``analyze_session_endpoint`` checks ``is_cancelled`` in its finally
        block and discards the result if True.

        Returns True if the task was found, False otherwise.
        """
        with ai_task_lock:
            if task_id not in active_ai_tasks:
                return False
            active_ai_tasks[task_id]["cancelled"] = True
            active_ai_tasks[task_id]["status"] = "cancelling"
            logger.info("🤖 AI TASK CANCEL REQUESTED: %s", task_id)
        return True

    @staticmethod
    def is_cancelled(task_id: str) -> bool:
        """Return True if the task has been marked for cancellation."""
        with ai_task_lock:
            info = active_ai_tasks.get(task_id)
            return bool(info and info.get("cancelled"))

    @staticmethod
    def list_active_tasks() -> dict:
        """Return a shallow copy of the active AI tasks dict (excluding cancelling ones)."""
        with ai_task_lock:
            return {k: v for k, v in active_ai_tasks.items() if v.get("status") != "cancelling"}
