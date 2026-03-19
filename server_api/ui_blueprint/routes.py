import os
from flask import Blueprint, send_from_directory, send_file

_STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "server_static",
)

api_ui_bp = Blueprint("api_ui", __name__)


@api_ui_bp.route("/", methods=["GET"])
def index():
    return send_file(os.path.join(_STATIC_DIR, "index.html"))


@api_ui_bp.route("/assets/<path:filename>", methods=["GET"])
def assets(filename):
    return send_from_directory(os.path.join(_STATIC_DIR, "assets"), filename)
