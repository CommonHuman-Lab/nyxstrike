import os
from flask import Blueprint, request, jsonify
import logging
from server_core import config_core
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_probe_httpx_bp = Blueprint("api_web_probe_httpx", __name__)


@api_web_probe_httpx_bp.route("/api/tools/httpx", methods=["POST"])
def httpx():
    """Execute httpx for fast HTTP probing and technology detection"""
    try:
        
        home_path = os.path.expanduser("~")
        paths_ovrrides = config_core.get("PATHS", {})
        httpx_bin_template = paths_ovrrides.get("GO_BINARYS", "{HOME}/go/bin/")
        httpx_bin = httpx_bin_template.replace("{HOME}", home_path) + "httpx"

        if not os.path.isfile(httpx_bin) or not os.access(httpx_bin, os.X_OK):
            logger.error(f"🚫 httpx binary not found or not executable at {httpx_bin}")    

        params = request.json
        target = params.get("target", "")
        probe = params.get("probe", True)
        tech_detect = params.get("tech_detect", False)
        status_code = params.get("status_code", False)
        content_length = params.get("content_length", False)
        title = params.get("title", False)
        web_server = params.get("web_server", False)
        threads = params.get("threads", 50)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🌐 httpx called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400
        
        command = f"{httpx_bin} -u {target} -t {threads}"

        if probe:
            command += " -probe"

        if tech_detect:
            command += " -tech-detect"

        if status_code:
            command += " -sc"

        if content_length:
            command += " -cl"

        if title:
            command += " -title"

        if web_server:
            command += " -server"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🌍 Starting httpx probe: {target}")
        result = execute_command(command)
        logger.info(f"📊 httpx probe completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in httpx endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
