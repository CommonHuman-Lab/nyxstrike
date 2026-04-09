from flask import Blueprint, request, jsonify
import logging
import re
from urllib.parse import urlparse
from .waymore import run_waymore, _ALLOWED_EXTRA_FLAGS, _VALID_MODES

logger = logging.getLogger(__name__)

api_web_probe_waymore_bp = Blueprint("api_web_probe_waymore", __name__)
# Matches bare hostnames/domains: e.g. example.com, sub.example.co.uk
_DOMAIN_RE = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')


def _validate_input(value):
    """Return True if value is a valid URL or bare domain."""
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https"):
        return bool(parsed.netloc) and not parsed.path.startswith("/..")
    # Accept bare domain with no scheme
    return bool(_DOMAIN_RE.match(value))


@api_web_probe_waymore_bp.route("/api/tools/waymore", methods=["POST"])
def waymore():
    try:
        params = request.json or {}
        input = params.get("input")
        mode = params.get("mode", "U")

        if not input:
            return jsonify({"error": "Input is required"}), 400

        if not _validate_input(input):
            return jsonify({"error": "Invalid input: must be a valid URL or domain"}), 400

        if mode not in _VALID_MODES:
            return jsonify({"error": f"Invalid mode: must be one of {sorted(_VALID_MODES)}"}), 400

        output_urls = params.get("output_urls")
        output_responses = params.get("output_responses")
        additional_args = {
            k: v for k, v in params.items() if k in _ALLOWED_EXTRA_FLAGS
        }

        result = run_waymore(input=input, mode=mode, output_urls=output_urls, output_responses=output_responses, **additional_args)
        return result
    except Exception as e:
        logger.error(f"Error in waymore endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500
