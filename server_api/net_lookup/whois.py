from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_net_lookup_whois_bp = Blueprint("api_net_lookup_whois", __name__)


@api_net_lookup_whois_bp.route("/api/tools/whois", methods=["POST"])
def whois():
    """
    WHOIS lookup tool endpoint.
    Expects JSON: { "target": "example.com" }
    """
    data = request.get_json(force=True)
    target = data.get("target", "")
    if not target:
        return jsonify({"error": "Missing 'target' parameter"}), 400

    result = execute_command(f"whois {target}", use_cache=False, timeout=30)
    output = result.get("stdout") or result.get("stderr") or ""
    return jsonify({"success": result.get("success", False), "output": output})
