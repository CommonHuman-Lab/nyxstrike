from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_crawl_hakrawler_bp = Blueprint("api_web_crawl_hakrawler", __name__)


@api_web_crawl_hakrawler_bp.route("/api/tools/hakrawler", methods=["POST"])
def hakrawler():
    """
    Execute Hakrawler for web endpoint discovery with enhanced logging

    Note: This implementation uses the standard Kali Linux hakrawler (hakluke/hakrawler)
    command line arguments, NOT the Elsfa7-110 fork. The standard version uses:
    - echo URL | hakrawler (stdin input)
    - -d for depth (not -depth)
    - -s for showing sources (not -forms)
    - -u for unique URLs
    - -subs for subdomain inclusion
    """
    try:
        params = request.json
        url = params.get("url", "")
        depth = params.get("depth", 2)
        forms = params.get("forms", True)
        robots = params.get("robots", True)
        sitemap = params.get("sitemap", True)
        wayback = params.get("wayback", False)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🕷️ Hakrawler called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        # Build command for standard Kali Linux hakrawler (hakluke version)
        command = f"echo '{url}' | hakrawler -d {depth}"

        if forms:
            command += " -s"  # Show sources (includes forms)
        if robots or sitemap or wayback:
            command += " -subs"  # Include subdomains for better coverage

        # Add unique URLs flag for cleaner output
        command += " -u"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🕷️ Starting Hakrawler crawling: {url}")
        result = execute_command(command)
        logger.info(f"📊 Hakrawler crawling completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in hakrawler endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
