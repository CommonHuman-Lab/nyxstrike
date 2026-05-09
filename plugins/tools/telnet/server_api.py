import logging
import re
import socket
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)
blueprint = Blueprint("plugin_telnet_client", __name__)

executor = ThreadPoolExecutor(max_workers=10)

telnet_sessions = {}
telnet_lock = Lock()

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240

ANSI_ESCAPE_RE = re.compile(
    r"(?:\x1B\][^\x07]*(?:\x07|\x1B\\))|(?:\x1B\[[0-?]*[ -/]*[@-~])"
)


def tool_response(success, stdout="", stderr="", return_code=0, **extra):
    return {
        "success": success,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
        "output": stdout,
        "error": stderr,
        **extra,
    }


def combine_stdout(*parts):
    return "\n".join(str(part).rstrip() for part in parts if str(part or "").strip())


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_session_key(host, username, port):
    user = username or "anonymous"
    return f"{user}@{host}:{port}"


def clean_terminal_output(output):
    output = ANSI_ESCAPE_RE.sub("", output)
    output = output.replace("\r", "")
    output = output.replace("\x00", "")
    return output


def looks_like_prompt(output):
    tail = clean_terminal_output(output).rstrip()
    if not tail:
        return False
    last_line = tail.splitlines()[-1].strip()
    return bool(re.search(r"([$#>])\s*$", last_line))


def looks_like_password_prompt(output):
    tail = clean_terminal_output(output).lower().rstrip()
    return bool(re.search(r"(password|passphrase)(?: for [^:]+)?:\s*$", tail))


class TelnetSession:
    def __init__(self, host, port, username, password, timeout=10):
        self.host = host
        self.port = port
        self.username = username or ""
        self.password = password or ""
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(0.2)
        self.lock = Lock()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def _send_raw(self, data):
        self.sock.sendall(data)

    def send_line(self, text):
        self._send_raw((text + "\n").encode("utf-8", "ignore"))

    def _negotiate(self, command, option):
        if command in (DO, DONT):
            self._send_raw(bytes([IAC, WONT, option]))
        elif command in (WILL, WONT):
            self._send_raw(bytes([IAC, DONT, option]))

    def read_available(self, timeout=0.4):
        output = bytearray()
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                data = self.sock.recv(4096)
            except socket.timeout:
                time.sleep(0.03)
                continue
            except OSError:
                break
            if not data:
                break

            i = 0
            while i < len(data):
                byte = data[i]
                if byte != IAC:
                    output.append(byte)
                    i += 1
                    continue

                if i + 1 >= len(data):
                    break
                command = data[i + 1]
                if command == IAC:
                    output.append(IAC)
                    i += 2
                elif command in (DO, DONT, WILL, WONT):
                    if i + 2 < len(data):
                        self._negotiate(command, data[i + 2])
                    i += 3
                elif command == SB:
                    i += 2
                    while i + 1 < len(data) and not (data[i] == IAC and data[i + 1] == SE):
                        i += 1
                    i += 2
                else:
                    i += 2

            end_time = time.time() + timeout

        return output.decode("utf-8", "ignore")

    def read_until_prompt(self, timeout=10):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            chunk = self.read_available(timeout=0.25)
            if chunk:
                output += chunk
                lower = output.lower()
                if "login:" in lower or "username:" in lower or "password:" in lower:
                    break
                if looks_like_prompt(output):
                    break
            else:
                time.sleep(0.05)
        return output

    def login(self):
        output = self.read_until_prompt(timeout=8)
        lower = output.lower()

        if ("login:" in lower or "username:" in lower) and self.username:
            self.send_line(self.username)
            output += self.read_until_prompt(timeout=8)
            lower = output.lower()

        if "password:" in lower and self.password:
            self.send_line(self.password)
            output += self.read_until_prompt(timeout=8)

        self.send_line("export TERM=dumb 2>/dev/null; unset PROMPT_COMMAND 2>/dev/null; PS1='' 2>/dev/null; stty -echo 2>/dev/null")
        self.read_available(timeout=0.6)
        return clean_terminal_output(output)

    def get_prompt(self, fallback):
        marker = f"__NYXSTRIKE_PROMPT_{uuid.uuid4().hex}__"
        self.send_line(f"printf '\\n%s:%s@%s:%s\\n' {marker} \"$USER\" \"$(hostname -s)\" \"$PWD\"")
        output = self.read_until_marker(marker, timeout=3)
        output = clean_terminal_output(output)
        if marker not in output:
            return fallback
        prompt_line = output.split(marker, 1)[1].splitlines()[0].lstrip(":").strip()
        return prompt_line or fallback

    def read_until_marker(self, marker, timeout=30):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            chunk = self.read_available(timeout=0.25)
            if chunk:
                output += chunk
                if marker in output:
                    break
                continue
            time.sleep(0.05)
        return output

    def execute(self, key, command, timeout=30):
        with self.lock:
            self.send_line("export TERM=dumb 2>/dev/null; unset PROMPT_COMMAND 2>/dev/null; PS1='' 2>/dev/null; stty -echo 2>/dev/null")
            self.read_available(timeout=0.4)

            prompt = self.get_prompt(key)
            marker = f"__NYXSTRIKE_DONE_{uuid.uuid4().hex}__"
            self.send_line(command.rstrip())
            self.send_line(f"printf '\\n%s:%s\\n' {marker} $?")
            output = self.read_until_marker(marker, timeout=timeout)

            if marker not in output:
                return {
                    "exit_code": 124,
                    "output": clean_terminal_output(output),
                    "error": "Telnet command timed out",
                    "prompt": prompt,
                }

            output = clean_terminal_output(output)
            before_marker, after_marker = output.split(marker, 1)
            exit_code_text = after_marker.splitlines()[0].lstrip(":").strip()
            try:
                exit_code = int(exit_code_text)
            except ValueError:
                exit_code = 0

            cleaned_lines = []
            for line in before_marker.splitlines():
                stripped = line.strip()
                if stripped == command.strip():
                    continue
                if stripped.startswith("export TERM="):
                    continue
                if stripped.startswith("unset PROMPT_COMMAND"):
                    continue
                if stripped.startswith("PS1="):
                    continue
                if stripped.startswith("stty "):
                    continue
                if stripped.startswith("printf ") and marker in stripped:
                    continue
                cleaned_lines.append(line.rstrip())

            cleaned_output = "\n".join(line for line in cleaned_lines if line.strip()).strip()
            prompt = self.get_prompt(prompt)

            return {
                "exit_code": exit_code,
                "output": f"{cleaned_output}\n" if cleaned_output else "",
                "error": "",
                "prompt": prompt,
            }

    def send_interactive_line(self, key, command, timeout=5, idle_timeout=0.8):
        with self.lock:
            self.send_line(command)

            output = ""
            end_time = time.time() + timeout
            idle_end = time.time() + idle_timeout
            while time.time() < end_time:
                chunk = self.read_available(timeout=0.2)
                if chunk:
                    output += chunk
                    idle_end = time.time() + idle_timeout
                    if looks_like_password_prompt(output):
                        break
                    continue
                if time.time() >= idle_end:
                    break
                time.sleep(0.05)

            output = clean_terminal_output(output)
            awaiting_input = looks_like_password_prompt(output)
            prompt = key if awaiting_input else self.get_prompt(key)

            return {
                "exit_code": 0,
                "output": output.strip(),
                "error": "",
                "prompt": prompt,
                "awaiting_sensitive_input": awaiting_input,
                "terminal_raw": True,
            }


def get_or_create_session(host, port, username, password):
    key = get_session_key(host, username, port)
    with telnet_lock:
        session = telnet_sessions.get(key)
        if session is not None:
            return key, session, False

        logger.warning("[TELNET CONNECT] initiating connection to %s:%s as %s", host, port, username)
        session = TelnetSession(host, port, username, password)
        session.login()
        telnet_sessions[key] = session
        logger.warning("[TELNET CONNECT] connection established to %s:%s", host, port)
        return key, session, True


@blueprint.route("/api/plugins/telnet", methods=["POST"])
def telnet_entry():
    data = request.get_json(force=True) or {}

    host = data.get("host")
    port = int(data.get("port", 23))
    username = data.get("username") or ""
    password = data.get("password") or ""
    command = data.get("command") or ""
    disconnect = parse_bool(data.get("terminal_disconnect", False))
    terminal_raw = str(data.get("terminal_mode", "")).strip().lower() == "raw"
    timeout = int(data.get("timeout", 30))

    logger.warning(
        "[TELNET ENTRY] host=%s, port=%s, user=%s, command=%s, terminal_disconnect=%s",
        host, port, username, command, disconnect,
    )

    if not host:
        return jsonify(tool_response(False, stderr="Missing host", return_code=1)), 400

    key = get_session_key(host, username, port)

    try:
        if disconnect:
            with telnet_lock:
                session = telnet_sessions.pop(key, None)
            if session is not None:
                session.close()
            message = f"Disconnected Telnet session {key}"
            return jsonify(tool_response(True, stdout=message, message=message))

        key, session, created = get_or_create_session(host, port, username, password)
        status_lines = [f"Connected to {host}:{port} as {username or 'anonymous'}"] if created else [f"Reusing Telnet session {key}"]

        if command or terminal_raw:
            if terminal_raw:
                future = executor.submit(session.send_interactive_line, key, command)
            else:
                future = executor.submit(session.execute, key, command, timeout)
            result = future.result()
            return jsonify({
                **tool_response(
                    result.get("exit_code", 1) == 0,
                    stdout=result.get("output", ""),
                    stderr=result.get("error", ""),
                    return_code=result.get("exit_code", 1),
                    prompt=result.get("prompt", key),
                    awaiting_sensitive_input=result.get("awaiting_sensitive_input", False),
                    terminal_raw=result.get("terminal_raw", False),
                ),
                "exit_code": result.get("exit_code", 1),
            })

        prompt = session.get_prompt(key)
        return jsonify(tool_response(True, stdout=combine_stdout(*status_lines), message="Connected", prompt=prompt))

    except Exception as e:
        logger.error("[TELNET ERROR] %s", e)
        with telnet_lock:
            session = telnet_sessions.pop(key, None)
        if session is not None:
            session.close()
        return jsonify(tool_response(False, stderr=str(e), return_code=1)), 500
