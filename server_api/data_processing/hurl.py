from flask import Blueprint, request, jsonify
import logging
import shlex
import shutil

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_data_processing_hurl_bp = Blueprint("api_data_processing_hurl", __name__)

_MODE_FLAGS = {
    "base64_encode": "-B",
    "base64_decode": "-b",
    "url_encode": "-U",
    "url_decode": "-u",
    "double_url_encode": "-D",
    "double_url_decode": "-d",
    "html_encode": "-H",
    "html_decode": "-h",
    "hex_encode": "-X",
    "hex_decode": "-x",
    "sha1": "-2",
    "sha256": "-4",
    "sha512": "-6",
    "md5": "-m",
    "rot13_encode": "-7",
    "rot13_decode": "-8",
}


@api_data_processing_hurl_bp.route("/api/tools/data_processing/hurl", methods=["POST"])
def hurl():
    """Hexadecimal & URL encoder + decoder with support for various encodings and transformations."""
    try:
        params = request.json or {}
        input_value = str(params.get("input", params.get("target", ""))).strip()
        mode = str(params.get("mode", "base64_encode")).strip()
        suppress = params.get("suppress", True)
        additional_args = str(params.get("additional_args", "")).strip()

        if not input_value:
            logger.warning("🧪 hURL called without input parameter")
            return jsonify({"error": "input parameter is required"}), 400

        if mode not in _MODE_FLAGS:
            return jsonify({
                "error": "Invalid mode",
                "valid_modes": sorted(_MODE_FLAGS.keys()),
            }), 400

        hurl_executable = shutil.which("hURL") or shutil.which("hurl")
        if not hurl_executable:
            logger.error("Neither 'hURL' nor 'hurl' found on system PATH")
            return jsonify({
                "error": "hURL tool not found",
                "install_hint": "sudo apt install hurl",
            }), 400

        args = [hurl_executable, _MODE_FLAGS[mode]]
        if suppress:
            args.append("-s")
        if additional_args:
            args.extend(shlex.split(additional_args))
        args.append(input_value)

        command = " ".join(shlex.quote(arg) for arg in args)

        logger.info(f"🧪 Starting hURL request (mode={mode}): {input_value}")
        result = execute_command(command, use_cache=False)
        logger.info(f"📊 hURL request completed (mode={mode})")
        return jsonify(result)
    except ValueError as e:
        logger.error(f"💥 Invalid hurl arguments: {str(e)}")
        return jsonify({"error": f"Invalid arguments: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"💥 Error in hurl endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
