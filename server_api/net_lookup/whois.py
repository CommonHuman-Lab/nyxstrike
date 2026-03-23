from flask import Blueprint, request, jsonify
import logging
import subprocess

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

    try:
        result = subprocess.run(
            ["whois", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return jsonify({"success": result.returncode == 0, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
