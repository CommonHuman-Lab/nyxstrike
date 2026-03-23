from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import random
import string
import time

from server_core.file_ops import file_manager

logger = logging.getLogger(__name__)

api_file_ops_and_payload_gen_bp = Blueprint("api_file_ops_and_payload_gen", __name__)


@api_file_ops_and_payload_gen_bp.route("/api/files/create", methods=["POST"])
def create_file():
    """Create a new file"""
    try:
        params = request.json
        filename = params.get("filename", "")
        content = params.get("content", "")
        binary = params.get("binary", False)

        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        result = file_manager.create_file(filename, content, binary)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_file_ops_and_payload_gen_bp.route("/api/files/modify", methods=["POST"])
def modify_file():
    """Modify an existing file"""
    try:
        params = request.json
        filename = params.get("filename", "")
        content = params.get("content", "")
        append = params.get("append", False)

        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        result = file_manager.modify_file(filename, content, append)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error modifying file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_file_ops_and_payload_gen_bp.route("/api/files/delete", methods=["DELETE"])
def delete_file():
    """Delete a file or directory"""
    try:
        params = request.json
        filename = params.get("filename", "")

        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        result = file_manager.delete_file(filename)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_file_ops_and_payload_gen_bp.route("/api/files/list", methods=["GET"])
def list_files():
    """List files in a directory"""
    try:
        directory = request.args.get("directory", ".")
        result = file_manager.list_files(directory)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_file_ops_and_payload_gen_bp.route("/api/payloads/generate", methods=["POST"])
def generate_payload():
    """Generate large payloads for testing"""
    try:
        params = request.json
        payload_type = params.get("type", "buffer")
        size = params.get("size", 1024)
        pattern = params.get("pattern", "A")
        filename = params.get("filename", f"payload_{int(time.time())}")

        if size > 100 * 1024 * 1024:  # 100MB limit
            return jsonify({"error": "Payload size too large (max 100MB)"}), 400

        if payload_type == "buffer":
            content = pattern * (size // len(pattern))
        elif payload_type == "cyclic":
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            content = ""
            for i in range(size):
                content += alphabet[i % len(alphabet)]
        elif payload_type == "random":
            content = ''.join(random.choices(string.ascii_letters + string.digits, k=size))
        else:
            return jsonify({"error": "Invalid payload type"}), 400

        result = file_manager.create_file(filename, content)
        result["payload_info"] = {
            "type": payload_type,
            "size": size,
            "pattern": pattern
        }

        logger.info(f"Generated {payload_type} payload: {filename} ({size} bytes)")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error generating payload: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
