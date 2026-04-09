# server_api/password_cracking/aircrack_ng

from flask import Blueprint, request, jsonify
from server_core.command_executor import execute_command
import logging

logger = logging.getLogger(__name__)

api_password_cracking_aircrack_ng_bp = Blueprint("api_password_cracking_aircrack_ng", __name__)
@api_password_cracking_aircrack_ng_bp.route("/api/tools/password_cracking/aircrack_ng", methods=["POST"])
def aircrack_ng():
    """
    Execute Aircrack-ng for Wi-Fi password cracking.

    Endpoint: POST /api/tools/password_cracking/aircrack_ng

    Description:
        This endpoint executes Aircrack-ng for Wi-Fi password cracking based on provided capture files,
        an optional target BSSID, and a required wordlist. It accepts a list of capture files and returns
        the results of the cracking attempt.
    Request (application/json):
        {
            "capture_files": ["<string, required> List of capture file paths (.cap, .ivs, etc.)"],
            "wordlist": "<string, required> Path to a wordlist file.",
            "bssid": "<string, optional> Target BSSID (AP MAC address)."
        }
    Response (application/json):
        {
            "success": "<boolean> Indicates if the cracking attempt was successful.",
            "data": "<object> The results from the Aircrack-ng analysis or error information."
        }
    """
    data = request.get_json()
    capture_files = data.get("capture_files", [])
    wordlist = data.get("wordlist")
    bssid = data.get("bssid")

    if not capture_files:
        return jsonify({"success": False, "error": "At least one capture file must be provided."}), 400
    
    if not wordlist:
        return jsonify({"success": False, "error": "A wordlist file must be provided."}), 400

    command = f"aircrack-ng {' '.join(capture_files)} -w {wordlist}"
    if bssid:
        command += f" -b {bssid}"

    logger.info(f"🔍 Starting Aircrack-ng analysis with command: {command}")
    result = execute_command(command, use_cache=False, tool="aircrack-ng")
    if result.get("success"):
        logger.info("✅ Aircrack-ng analysis completed successfully")
    else:
        logger.error("❌ Aircrack-ng analysis failed")
    return jsonify(result)
