import os
from flask import Blueprint, send_from_directory, send_file, abort

_STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "dashboard",
)

api_ui_bp = Blueprint("api_ui", __name__)


@api_ui_bp.route("/", methods=["GET"])
def index():
    return send_file(os.path.join(_STATIC_DIR, "index.html"))


@api_ui_bp.route("/assets/<path:filename>", methods=["GET"])
def assets(filename):
    return send_from_directory(os.path.join(_STATIC_DIR, "assets"), filename)


@api_ui_bp.route("/<path:path>", methods=["GET"])
def catch_all(path: str):
    """Fallback for any non-API path — serves the SPA so the hash router can take over."""
    if path.startswith("api/") or path.startswith("assets/"):
        abort(404)
    return send_file(os.path.join(_STATIC_DIR, "index.html"))
