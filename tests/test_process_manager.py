"""
tests/test_process_manager.py

Pure-Python unit tests for server_core/process_manager.py::ProcessManager.
No subprocess, no Flask, no server calls.
"""

from unittest.mock import MagicMock

from server_core.process_manager import ProcessManager, active_processes


def _cleanup(pid):
    ProcessManager.cleanup_process(pid)


def test_register_process_stores_task_id():
    pid = 900001
    try:
        ProcessManager.register_process(pid, "echo hi", MagicMock(), task_id="abc")
        assert active_processes[pid]["task_id"] == "abc"
    finally:
        _cleanup(pid)


def test_register_process_defaults_task_id_to_empty_string():
    pid = 900002
    try:
        ProcessManager.register_process(pid, "echo hi", MagicMock())
        assert active_processes[pid]["task_id"] == ""
    finally:
        _cleanup(pid)
