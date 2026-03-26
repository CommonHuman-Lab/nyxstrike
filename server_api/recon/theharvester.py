# server_api/recon/theharvester.py

from flask import Blueprint, request, jsonify
from server_core.command_executor import execute_command
import logging

logger = logging.getLogger(__name__)

api_recon_theharvester_bp = Blueprint("api_recon_theharvester", __name__)

@api_recon_theharvester_bp.route("/api/tools/recon/theharvester", methods=["POST"])
def theharvester():
    """
    Execute TheHarvester for passive information gathering.

    Endpoint: POST /api/tools/recon/theharvester

    Description:
        This endpoint executes TheHarvester for passive information gathering on a specified domain.
        It accepts a target domain and optional additional arguments for TheHarvester, runs the tool,
        and returns the results.
    
    Request (application/json):
        {
            "domain": "<string, required> The target domain for TheHarvester.",
            "additional_args": "<string, optional> Extra CLI flags for TheHarvester (e.g., '-b', '-l')."
        }

    Response (application/json):
        {
            "success": "<boolean> Indicates if the scan was successful.",
            "data": "<object> The results of the TheHarvester scan."
        }
    """
    data = request.get_json()
    domain = data.get("domain")
    additional_args = data.get("additional_args", "")

    if not domain:
        return jsonify({"success": False, "error": "Domain is required"}), 400


    command = f"theHarvester -d {domain} {additional_args}"
    logger.info(f"🔍 Starting TheHarvester: {domain}")
    result = execute_command(command, use_cache=True)
    if result.get("success"):
        logger.info(f"✅ TheHarvester completed for {domain}")
    else:
        logger.error(f"❌ TheHarvester failed for {domain}")
    return jsonify(result)