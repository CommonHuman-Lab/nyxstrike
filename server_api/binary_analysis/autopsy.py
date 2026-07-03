# server_api/binary_analysis/autopsy.py

from flask import Blueprint, request, jsonify
from server_core.command_executor import execute_command
import logging

logger = logging.getLogger(__name__)

api_binary_analysis_autopsy_bp = Blueprint("api_binary_analysis_autopsy", __name__)

@api_binary_analysis_autopsy_bp.route("/api/tools/binary_analysis/autopsy", methods=["POST"])
def autopsy_analysis():
    """
    Launch Autopsy and return access instructions.

    Endpoint: POST /api/tools/binary_analysis/autopsy

    Description:
        This endpoint launches the Autopsy web server for binary analysis and returns access instructions.
    
    Request (application/json):
        {}
   
    Response (application/json):
        {
            "success": "<boolean> Indicates if Autopsy was launched successfully.",
            "data": "<object> Access instructions for Autopsy web interface."
        }
    """
    logger.info("🔍 Launching Autopsy web server")
    result = execute_command("autopsy &", use_cache=False, use_recovery=True)
    if result.get("success"):
        logger.info(f"✅ Autopsy started successfully")
    else:
        logger.error(f"❌ Autopsy failed to start")
    return jsonify(result)