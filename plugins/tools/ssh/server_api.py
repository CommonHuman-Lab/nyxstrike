import logging
import paramiko
from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor

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


def tool_response(success, stdout="", stderr="", return_code=0, **extra):
    response = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
        # Backward-compatible aliases for existing MCP/plugin callers.
        "output": stdout,
        "error": stderr,
        **extra
    }
    return response


def combine_stdout(*parts):
    return "\n".join(str(part).rstrip() for part in parts if str(part or "").strip())


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
    disconnect = data.get("disconnect", False)

    logger.warning(
        f"[SSH ENTRY] host={host}, port={port}, user={username}, "
        f"command={command}, disconnect={disconnect}"
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
                    ssh_sessions[key].close()
                except Exception as e:
                    logger.error(f"[SSH DISCONNECT ERROR] {e}")

                ssh_sessions.pop(key, None)

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
        if command:
            logger.warning(f"[SSH EXECUTE REQUEST] {command}")
            status_lines.append(f"Executing command: {command}")

            future = executor.submit(ssh_execute, client, command)
            result = future.result()

            logger.warning(f"[SSH RESPONSE READY] {result}")

            return jsonify({
                **tool_response(
                    result.get("exit_code", 1) == 0,
                    stdout=combine_stdout(*status_lines, result.get("output", "")),
                    stderr=result.get("error", ""),
                    return_code=result.get("exit_code", 1)
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
                ssh_sessions[key].close()
            except Exception:
                pass
            ssh_sessions.pop(key, None)

        return jsonify({
            **tool_response(
                False,
                stderr=str(e),
                return_code=1
            )
        }), 500
