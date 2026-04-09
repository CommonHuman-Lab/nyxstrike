import time
import threading
import logging
import re as _re
import subprocess
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from wcwidth import wcswidth as _wcswidth
import server_core.config_core as config_core
from server_core.process_manager import ProcessManager
from server_core.modern_visual_engine import ModernVisualEngine

_ANSI = _re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
_BOX_WIDTH = 66  # visible columns between the two │ borders


def _strip_ansi(text: str) -> str:
    return _ANSI.sub('', text)


def _is_decorative_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True

    if _re.fullmatch(r"[A-Z0-9 _\-/\\`'.]{10,}", stripped):
        letters = [c for c in stripped if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) / len(letters) > 0.85:
            return True

    if _re.fullmatch(r"[-_=*~`.:+|/\\<>\[\]{}()#]{6,}", stripped):
        return True

    visible_chars = [c for c in stripped if not c.isspace()]
    if not visible_chars:
        return True

    alpha_num = sum(c.isalnum() for c in visible_chars)
    ratio = alpha_num / len(visible_chars)
    return len(visible_chars) >= 10 and ratio < 0.35


def _is_banner_text_line(line: str) -> bool:
    stripped = line.strip()
    lower = stripped.lower()

    if "http://" in lower or "https://" in lower:
        return True

    if any(token in lower for token in ("github.com", "discord", "twitter", "blog")):
        return True

    if _re.fullmatch(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,}\.??", stripped):
        return True

    if _re.fullmatch(r"[A-Za-z][A-Za-z ]{8,}:\s+.+[.!?]", stripped):
        return True

    return False


def _strip_leading_banner_block(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1

    if start >= len(lines) or not _is_decorative_line(lines[start]):
        return text

    i = start
    non_empty_consumed = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or _is_decorative_line(line) or _is_banner_text_line(line):
            if line.strip():
                non_empty_consumed += 1
            i += 1
            continue
        break

    if non_empty_consumed < 3:
        return text

    while i < len(lines) and not lines[i].strip():
        i += 1

    return "\n".join(lines[i:])


def _clean_output(text: str, command: str = "") -> str:
    cleaned = _strip_ansi(text)
    cleaned = _strip_leading_banner_block(cleaned)
    return cleaned


def _box_row(content_with_ansi: str) -> str:
    C = ModernVisualEngine.COLORS
    visible = _ANSI.sub('', content_with_ansi)
    w = _wcswidth(visible)
    if w < 0:
        w = len(visible)
    padding = ' ' * (_BOX_WIDTH - w)
    return f"{C['MATRIX_GREEN']}{C['BOLD']}│{C['RESET']}{content_with_ansi}{padding}{C['MATRIX_GREEN']}{C['BOLD']}│{C['RESET']}"

# Global telemetry collector
from server_core.telemetry_collector import TelemetryCollector
telemetry = TelemetryCollector()

logger = logging.getLogger(__name__)
COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # Default to 5 minutes if not set
COMMAND_INACTIVITY_TIMEOUT = config_core.get("COMMAND_INACTIVITY_TIMEOUT", 900)
COMMAND_MAX_RUNTIME = config_core.get("COMMAND_MAX_RUNTIME", 86400)
class EnhancedCommandExecutor:
    """Enhanced command executor with caching, progress tracking, and better output handling"""

    def __init__(self, command: str, timeout: Optional[int] = COMMAND_TIMEOUT):
        self.command = command
        self.timeout = timeout
        self.process = None
        self.stdout_data = ""
        self.stderr_data = ""
        self._stdout_chunks: list = []
        self._stderr_chunks: list = []
        self.stdout_thread = None
        self.stderr_thread = None
        self.return_code = None
        self.timed_out = False
        self.timeout_reason = ""
        self.start_time = None
        self.end_time = None
        self.last_output_time = time.time()

    def _read_stdout(self):
        """Thread function to continuously read and display stdout"""
        if not self.process or not self.process.stdout:
            return
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self._stdout_chunks.append(line)
                    self.last_output_time = time.time()
                    # Real-time output display
                    logger.info(f"📤 STDOUT: {_strip_ansi(line).strip()}")
        except Exception as e:
            logger.error(f"Error reading stdout: {e}")
        finally:
            self.stdout_data = "".join(self._stdout_chunks)

    def _read_stderr(self):
        """Thread function to continuously read and display stderr"""
        if not self.process or not self.process.stderr:
            return
        try:
            for line in iter(self.process.stderr.readline, ''):
                if line:
                    self._stderr_chunks.append(line)
                    self.last_output_time = time.time()
                    # Real-time error output display
                    logger.warning(f"📥 STDERR: {_strip_ansi(line).strip()}")
        except Exception as e:
            logger.error(f"Error reading stderr: {e}")
        finally:
            self.stderr_data = "".join(self._stderr_chunks)

    def _show_progress(self):
        """Show enhanced progress indication for long-running commands"""
        progress_chars = ModernVisualEngine.PROGRESS_STYLES['dots']
        start = time.time()
        i = 0
        while self.process and self.process.poll() is None:
            elapsed = time.time() - start
            char = progress_chars[i % len(progress_chars)]

            # Calculate progress percentage (rough estimate)
            progress_base = self.timeout if isinstance(self.timeout, int) and self.timeout > 0 else COMMAND_MAX_RUNTIME
            progress_percent = min((elapsed / progress_base) * 100, 99.9)
            progress_fraction = progress_percent / 100

            # Calculate ETA
            eta = 0
            if progress_percent > 5:  # Only show ETA after 5% progress
                eta = ((elapsed / progress_percent) * 100) - elapsed

            # Calculate speed
            bytes_processed = sum(len(c) for c in self._stdout_chunks) + sum(len(c) for c in self._stderr_chunks)
            speed = f"{bytes_processed/elapsed:.0f} B/s" if elapsed > 0 else "0 B/s"

            # Update process manager with progress
            ProcessManager.update_process_progress(
                self.process.pid,
                progress_fraction,
                f"Running for {elapsed:.1f}s",
                bytes_processed
            )

            # Create beautiful progress bar using ModernVisualEngine
            progress_bar = ModernVisualEngine.render_progress_bar(
                progress_fraction,
                width=30,
                style='cyber',
                label=f"⚡ PROGRESS {char}",
                eta=eta,
                speed=speed
            )

            logger.info(f"{progress_bar} | {elapsed:.1f}s | PID: {self.process.pid}")
            time.sleep(0.8)
            i += 1
            if isinstance(self.timeout, int) and self.timeout > 0 and elapsed > self.timeout:
                break

    def execute(self) -> Dict[str, Any]:
        """Execute the command with enhanced monitoring and output"""
        # Reset per-execution state so the instance can be reused across calls
        self.stdout_data = ""
        self.stderr_data = ""
        self._stdout_chunks = []
        self._stderr_chunks = []
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.return_code = None
        self.timed_out = False
        self.timeout_reason = ""
        self.end_time = None
        self.start_time = time.time()
        self.last_output_time = self.start_time

        logger.info(f"🚀 EXECUTING: {self.command}")
        timeout_label = f"{self.timeout}s" if isinstance(self.timeout, int) and self.timeout > 0 else "none"
        logger.info(f"⏱️  TIMEOUT: {timeout_label} | PID: Starting...")

        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            pid = self.process.pid
            logger.info(f"🆔 PROCESS: PID {pid} started")

            # Register process with ProcessManager (v5.0 enhancement)
            ProcessManager.register_process(pid, self.command, self.process)

            # Start threads to read output continuously
            self.stdout_thread = threading.Thread(target=self._read_stdout)
            self.stderr_thread = threading.Thread(target=self._read_stderr)
            self.stdout_thread.daemon = True
            self.stderr_thread.daemon = True
            self.stdout_thread.start()
            self.stderr_thread.start()

            # Start progress tracking for long-running commands and unlimited timeout mode
            if self.timeout is None or (isinstance(self.timeout, int) and self.timeout > 2):
                progress_thread = threading.Thread(target=self._show_progress)
                progress_thread.daemon = True
                progress_thread.start()

            # Wait for the process to complete, enforcing optional timeout/watchdog constraints
            try:
                wait_timeout = self.timeout if isinstance(self.timeout, int) and self.timeout > 0 else None
                while self.process.poll() is None:
                    try:
                        self.process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        pass

                    now = time.time()
                    elapsed = now - self.start_time
                    inactivity = now - self.last_output_time

                    if wait_timeout is not None and elapsed > wait_timeout:
                        self.timeout_reason = f"configured timeout ({wait_timeout}s)"
                        raise subprocess.TimeoutExpired(self.command, wait_timeout)
                    if COMMAND_INACTIVITY_TIMEOUT > 0 and inactivity > COMMAND_INACTIVITY_TIMEOUT:
                        self.timeout_reason = f"inactivity timeout ({COMMAND_INACTIVITY_TIMEOUT}s)"
                        raise subprocess.TimeoutExpired(self.command, COMMAND_INACTIVITY_TIMEOUT)
                    if COMMAND_MAX_RUNTIME > 0 and elapsed > COMMAND_MAX_RUNTIME:
                        self.timeout_reason = f"max runtime ({COMMAND_MAX_RUNTIME}s)"
                        raise subprocess.TimeoutExpired(self.command, COMMAND_MAX_RUNTIME)

                self.return_code = self.process.returncode
                self.end_time = time.time()

                # Process completed, join the threads
                self.stdout_thread.join(timeout=1)
                self.stderr_thread.join(timeout=1)

                execution_time = self.end_time - self.start_time

                # Cleanup process from registry (v5.0 enhancement)
                ProcessManager.cleanup_process(pid)

                if self.return_code == 0:
                    logger.info(f"✅ SUCCESS: Command completed | Exit Code: {self.return_code} | Duration: {execution_time:.2f}s")
                    telemetry.record_execution(True, execution_time)
                else:
                    logger.warning(f"⚠️  WARNING: Command completed with errors | Exit Code: {self.return_code} | Duration: {execution_time:.2f}s")
                    telemetry.record_execution(False, execution_time)

            except subprocess.TimeoutExpired:
                self.end_time = time.time()
                execution_time = self.end_time - self.start_time

                # Process timed out but we might have partial results
                self.timed_out = True
                reason = self.timeout_reason or (f"configured timeout ({self.timeout}s)" if self.timeout else "watchdog timeout")
                logger.warning(f"⏰ TIMEOUT: Command stopped due to {reason} | Terminating PID {self.process.pid}")

                # Try to terminate gracefully first
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    logger.error(f"🔪 FORCE KILL: Process {self.process.pid} not responding to termination")
                    self.process.kill()

                self.return_code = -1
                telemetry.record_execution(False, execution_time)

            # Always consider it a success if we have output, even with timeout
            success = True if self.timed_out and (self.stdout_data or self.stderr_data) else (self.return_code == 0)

            # Normalize noisy terminal output for logs/API consumers
            if config_core.get("CLEAN_TOOL_OUTPUT", True):
                self.stdout_data = _clean_output(self.stdout_data, self.command)
                self.stderr_data = _clean_output(self.stderr_data, self.command)

            # Log enhanced final results with summary using ModernVisualEngine
            output_size = len(self.stdout_data) + len(self.stderr_data)
            execution_time = self.end_time - self.start_time if self.end_time else 0

            # Create status summary
            status_icon = "✅" if success else "❌"
            status_color = ModernVisualEngine.COLORS['MATRIX_GREEN'] if success else ModernVisualEngine.COLORS['HACKER_RED']
            timeout_status = f" {ModernVisualEngine.COLORS['WARNING']}[TIMEOUT]{ModernVisualEngine.COLORS['RESET']}" if self.timed_out else ""

            # Create beautiful results summary
            C = ModernVisualEngine.COLORS
            _hr = '─' * _BOX_WIDTH
            box_lines = [
                f"{C['MATRIX_GREEN']}{C['BOLD']}╭{_hr}╮{C['RESET']}",
                _box_row(f" {status_color}📊 FINAL RESULTS {status_icon}{C['RESET']}"),
                f"{C['MATRIX_GREEN']}{C['BOLD']}├{_hr}┤{C['RESET']}",
                _box_row(f" {C['NEON_BLUE']}🚀 Command:{C['RESET']} {self.command[:55]}{'...' if len(self.command) > 55 else ''}"),
                _box_row(f" {C['CYBER_ORANGE']}⏰ Duration:{C['RESET']} {execution_time:.2f}s{timeout_status}"),
                _box_row(f" {C['WARNING']}📊 Output Size:{C['RESET']} {output_size} bytes"),
                _box_row(f" {C['ELECTRIC_PURPLE']}🔢 Exit Code:{C['RESET']} {self.return_code}"),
                _box_row(f" {status_color}📈 Status:{C['RESET']} {'SUCCESS' if success else 'FAILED'} | Cached: Yes"),
                f"{C['MATRIX_GREEN']}{C['BOLD']}╰{_hr}╯{C['RESET']}",
            ]
            print('\n'.join(box_lines), flush=True)

            return {
                "stdout": self.stdout_data,
                "stderr": self.stderr_data,
                "return_code": self.return_code,
                "success": success,
                "timed_out": self.timed_out,
                "timeout_reason": self.timeout_reason,
                "partial_results": self.timed_out and (self.stdout_data or self.stderr_data),
                "execution_time": self.end_time - self.start_time if self.end_time else 0,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time if self.start_time else 0

            logger.error(f"💥 ERROR: Command execution failed: {str(e)}")
            logger.error(f"🔍 TRACEBACK: {traceback.format_exc()}")
            telemetry.record_execution(False, execution_time)

            return {
                "stdout": self.stdout_data,
                "stderr": f"Error executing command: {str(e)}\n{self.stderr_data}",
                "return_code": -1,
                "success": False,
                "timed_out": False,
                "timeout_reason": self.timeout_reason,
                "partial_results": bool(self.stdout_data or self.stderr_data),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
