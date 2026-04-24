import os
import time
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context

logger = logging.getLogger(__name__)

api_logs_bp = Blueprint("api_logs", __name__)

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "nyxstrike.log")
DEFAULT_LINES = 150
MAX_LINES = 500


def _tail(path: str, n: int) -> list[str]:
    """Return the last n lines from a file efficiently."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            buf = bytearray()
            pos = size
            found = 0
            chunk = 4096
            while pos > 0 and found <= n:
                read_size = min(chunk, pos)
                pos -= read_size
                f.seek(pos)
                buf = f.read(read_size) + buf
                found = buf.count(b"\n")
            lines = buf.decode("utf-8", errors="replace").splitlines()
            return lines[-n:] if len(lines) >= n else lines
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning("Could not read log file: %s", e)
        return []


@api_logs_bp.route("/api/logs", methods=["GET"])
def get_logs():
    """Return the last N lines from the server log file."""
    n = min(int(request.args.get("lines", DEFAULT_LINES)), MAX_LINES)
    lines = _tail(LOG_FILE, n)
    return jsonify({"success": True, "lines": lines, "log_file": LOG_FILE})


@api_logs_bp.route("/api/logs/stream", methods=["GET"])
def stream_logs():
    """SSE endpoint — streams new log lines as they are appended."""
    n = min(int(request.args.get("lines", 50)), MAX_LINES)

    def generate():
        # Send the last n lines as the initial burst
        initial = _tail(LOG_FILE, n)
        for line in initial:
            yield f"data: {line}\n\n"

        # Then tail for new lines
        try:
            size = os.path.getsize(LOG_FILE)
        except FileNotFoundError:
            size = 0

        while True:
            time.sleep(1)
            try:
                new_size = os.path.getsize(LOG_FILE)
            except FileNotFoundError:
                yield "data: [log file not found]\n\n"
                continue

            if new_size > size:
                try:
                    with open(LOG_FILE, "rb") as f:
                        f.seek(size)
                        chunk = f.read(new_size - size)
                    new_lines = chunk.decode("utf-8", errors="replace").splitlines()
                    for line in new_lines:
                        if line.strip():
                            yield f"data: {line}\n\n"
                except Exception as e:
                    yield f"data: [error reading log: {e}]\n\n"
                size = new_size
            else:
                # Keepalive comment so the browser doesn't time out
                yield ": keepalive\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
