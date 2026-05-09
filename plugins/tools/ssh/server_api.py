import logging
import re
import time
import uuid
import paramiko
from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

logger = logging.getLogger(__name__)
blueprint = Blueprint("plugin_ssh_client", __name__)

# -------------------------
# Thread pool (safe blocking SSH execution)
# -------------------------
executor = ThreadPoolExecutor(max_workers=10)

# -------------------------
# SSH session cache
# -------------------------
ssh_sessions = {}
ssh_shells = {}
ssh_shell_locks = {}
ssh_shell_locks_guard = Lock()

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
        **extra
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


def looks_like_password_prompt(output):
    tail = clean_terminal_output(output).lower().rstrip()
    return bool(re.search(r"(password|passphrase)(?: for [^:]+)?:\s*$", tail))


def get_session_key(host, username, port):
    return f"{username}@{host}:{port}"


# -------------------------
# CONNECT
# -------------------------
def ssh_connect(host, port, username, password):
    logger.warning(f"[SSH CONNECT] initiating connection to {host}:{port} as {username}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        timeout=10
    )

    logger.warning(f"[SSH CONNECT] connection established to {host}:{port}")

    return client


# -------------------------
# EXECUTE COMMAND (RELIABLE)
# -------------------------
def ssh_execute(client, command):
    logger.warning(f"[SSH EXEC] command received: {command}")

    stdin, stdout, stderr = client.exec_command(command)

    exit_code = stdout.channel.recv_exit_status()

    output = stdout.read().decode(errors="ignore")
    error = stderr.read().decode(errors="ignore")

    logger.warning(
        f"[SSH OUTPUT] exit_code={exit_code} stdout={output} stderr={error}"
    )

    return {
        "exit_code": exit_code,
        "output": output,
        "error": error
    }


def drain_shell(channel, timeout=0.2):
    output = ""
    end_time = time.time() + timeout
    while time.time() < end_time:
        if channel.recv_ready():
            output += channel.recv(65535).decode(errors="ignore")
            end_time = time.time() + timeout
            continue
        time.sleep(0.03)
    return output


def clean_terminal_output(output):
    output = ANSI_ESCAPE_RE.sub("", output)
    output = output.replace("\r", "")
    return output


def get_shell_prompt(shell, fallback):
    marker = f"__NYXSTRIKE_PROMPT_{uuid.uuid4().hex}__"
    shell.send(f"printf '\\n%s:%s@%s:%s\\n' {marker} \"$USER\" \"$(hostname -s)\" \"$PWD\"\n")
    output = ""
    end_time = time.time() + 2
    while time.time() < end_time:
        if shell.recv_ready():
            output += shell.recv(65535).decode(errors="ignore")
            if marker in output:
                break
            continue
        time.sleep(0.05)

    output = clean_terminal_output(output)
    if marker not in output:
        return fallback

    prompt_line = output.split(marker, 1)[1].splitlines()[0].lstrip(":").strip()
    return prompt_line or fallback


def get_shell(client, key):
    shell = ssh_shells.get(key)
    if shell is None or shell.closed:
        shell = client.invoke_shell(term="xterm", width=160, height=40)
        ssh_shells[key] = shell
        drain_shell(shell, timeout=0.5)
        shell.send("export TERM=dumb\n")
        shell.send("unset PROMPT_COMMAND\n")
        shell.send("PS1=''\n")
        shell.send("stty -echo\n")
        drain_shell(shell, timeout=0.5)
    return shell


def get_shell_lock(key):
    with ssh_shell_locks_guard:
        lock = ssh_shell_locks.get(key)
        if lock is None:
            lock = Lock()
            ssh_shell_locks[key] = lock
        return lock


def ssh_send_shell_line(client, key, command, timeout=5, idle_timeout=0.8):
    logger.warning(f"[SSH SHELL RAW] line received for {key}")

    shell = get_shell(client, key)
    lock = get_shell_lock(key)

    with lock:
        shell.send(f"{command}\n")

        output = ""
        end_time = time.time() + timeout
        idle_end = time.time() + idle_timeout
        while time.time() < end_time:
            if shell.recv_ready():
                output += shell.recv(65535).decode(errors="ignore")
                idle_end = time.time() + idle_timeout
                if looks_like_password_prompt(output):
                    break
                continue
            if time.time() >= idle_end:
                break
            time.sleep(0.05)

        output = clean_terminal_output(output)
        awaiting_input = looks_like_password_prompt(output)
        prompt = key if awaiting_input else get_shell_prompt(shell, key)

        return {
            "exit_code": 0,
            "output": output.strip(),
            "error": "",
            "prompt": prompt,
            "awaiting_sensitive_input": awaiting_input,
            "terminal_raw": True
        }


def ssh_execute_shell(client, key, command, timeout=30):
    logger.warning(f"[SSH SHELL EXEC] command received: {command}")

    shell = get_shell(client, key)
    prompt = get_shell_prompt(shell, key)
    marker = f"__NYXSTRIKE_DONE_{uuid.uuid4().hex}__"
    shell.send(f"{command.rstrip()}\n")
    shell.send(f"printf '\\n%s:%s\\n' {marker} $?\n")

    output = ""
    end_time = time.time() + timeout
    while time.time() < end_time:
        if shell.recv_ready():
            output += shell.recv(65535).decode(errors="ignore")
            if marker in output:
                break
            continue
        time.sleep(0.05)

    if marker not in output:
        return {
            "exit_code": 124,
            "output": output,
            "error": "Interactive shell command timed out",
            "prompt": prompt
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
    prompt = get_shell_prompt(shell, prompt)
    logger.warning(
        f"[SSH SHELL OUTPUT] exit_code={exit_code} stdout={cleaned_output}"
    )

    return {
        "exit_code": exit_code,
        "output": f"{cleaned_output}\n" if cleaned_output else "",
        "error": "",
        "prompt": prompt
    }


# -------------------------
# API ENTRY
# -------------------------
@blueprint.route("/api/plugins/ssh", methods=["POST"])
def ssh_entry():
    data = request.get_json(force=True) or {}

    host = data.get("host")
    port = int(data.get("port", 22))
    username = data.get("username")
    password = data.get("password")
    command = data.get("command")
    disconnect = parse_bool(data.get("terminal_disconnect", False))
    interactive = parse_bool(data.get("interactive", False))
    terminal_raw = str(data.get("terminal_mode", "")).strip().lower() == "raw"

    logger.warning(
        f"[SSH ENTRY] host={host}, port={port}, user={username}, "
        f"command={command}, terminal_disconnect={disconnect}, interactive={interactive}"
    )

    if not host or not username:
        logger.error("[SSH ENTRY] missing host or username")
        return jsonify(tool_response(
            False,
            stderr="Missing host or username",
            return_code=1
        )), 400

    key = get_session_key(host, username, port)
    status_lines = []

    try:
        # -------------------------
        # DISCONNECT
        # -------------------------
        if disconnect:
            logger.warning(f"[SSH DISCONNECT] key={key}")

            if key in ssh_sessions:
                try:
                    shell = ssh_shells.pop(key, None)
                    if shell is not None:
                        shell.close()
                    ssh_sessions[key].close()
                except Exception as e:
                    logger.error(f"[SSH DISCONNECT ERROR] {e}")

                ssh_sessions.pop(key, None)
                ssh_shell_locks.pop(key, None)

            message = f"Disconnected SSH session {key}"
            return jsonify(tool_response(True, stdout=message, message=message))

        # -------------------------
        # CONNECT (if needed)
        # -------------------------
        if key not in ssh_sessions:
            if not password:
                logger.error("[SSH CONNECT] missing password")
                return jsonify(tool_response(
                    False,
                    stderr="Password required",
                    return_code=1
                )), 400

            logger.warning(f"[SSH SESSION] creating new session for {key}")

            client = ssh_connect(host, port, username, password)
            ssh_sessions[key] = client
            status_lines.append(f"Connected to {host}:{port} as {username}")

        else:
            logger.warning(f"[SSH SESSION] reusing session for {key}")
            status_lines.append(f"Reusing SSH session {key}")

        client = ssh_sessions[key]

        # -------------------------
        # EXECUTE COMMAND
        # -------------------------
        if command is not None and (command or terminal_raw):
            logger.warning(f"[SSH EXECUTE REQUEST] {command}")
            status_lines.append(f"Executing command: {command}")

            if terminal_raw:
                future = executor.submit(ssh_send_shell_line, client, key, command)
            else:
                execute_fn = ssh_execute_shell if interactive else ssh_execute
                future = executor.submit(execute_fn, client, key, command) if interactive else executor.submit(execute_fn, client, command)
            result = future.result()

            logger.warning(f"[SSH RESPONSE READY] {result}")

            return jsonify({
                **tool_response(
                    result.get("exit_code", 1) == 0,
                    stdout=result.get("output", "") if interactive else combine_stdout(*status_lines, result.get("output", "")),
                    stderr=result.get("error", ""),
                    return_code=result.get("exit_code", 1),
                    prompt=result.get("prompt", key),
                    awaiting_sensitive_input=result.get("awaiting_sensitive_input", False),
                    terminal_raw=result.get("terminal_raw", False)
                ),
                "exit_code": result.get("exit_code", 1)
            })

        # -------------------------
        # JUST CONNECTED
        # -------------------------
        logger.warning("[SSH ENTRY] connected without command")

        return jsonify({
            **tool_response(
                True,
                stdout=combine_stdout(*status_lines),
                message="Connected"
            )
        })

    except Exception as e:
        logger.error(f"[SSH ERROR] {e}")

        if key in ssh_sessions:
            try:
                shell = ssh_shells.pop(key, None)
                if shell is not None:
                    shell.close()
                ssh_sessions[key].close()
            except Exception:
                pass
            ssh_sessions.pop(key, None)
            ssh_shell_locks.pop(key, None)

        return jsonify({
            **tool_response(
                False,
                stderr=str(e),
                return_code=1
            )
        }), 500
