from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_crawl_gospider_bp = Blueprint("api_web_crawl_gospider", __name__)


@api_web_crawl_gospider_bp.route("/api/tools/gospider", methods=["POST"])
def gospider():
    """Execute GoSpider for web crawling and endpoint discovery."""
    try:
        params = request.json or {}

        site = params.get("site", "")
        sites = params.get("sites", "")
        proxy = params.get("proxy", "")
        output = params.get("output", "")
        user_agent = params.get("user_agent", "web")
        cookie = params.get("cookie", "")
        headers = params.get("headers", [])
        burp = params.get("burp", "")
        blacklist = params.get("blacklist", "")
        threads = params.get("threads", 1)
        concurrent = params.get("concurrent", 5)
        depth = params.get("depth", 1)
        delay = params.get("delay", 0)
        random_delay = params.get("random_delay", 0)
        timeout = params.get("timeout", 10)
        sitemap = params.get("sitemap", False)
        robots = params.get("robots", True)
        other_source = params.get("other_source", False)
        include_subs = params.get("include_subs", False)
        include_other_source = params.get("include_other_source", False)
        debug = params.get("debug", False)
        verbose = params.get("verbose", False)
        no_redirect = params.get("no_redirect", False)
        version = params.get("version", False)
        additional_args = params.get("additional_args", "")

        if not version and not site and not sites:
            logger.warning("🕷️ GoSpider called without site/sites parameter")
            return jsonify({"error": "Provide either site or sites parameter"}), 400

        command_parts = ["gospider"]

        if site:
            command_parts.extend(["-s", site])
        if sites:
            command_parts.extend(["-S", sites])
        if proxy:
            command_parts.extend(["-p", proxy])
        if output:
            command_parts.extend(["-o", output])
        if user_agent:
            command_parts.extend(["-u", user_agent])
        if cookie:
            command_parts.extend(["--cookie", cookie])

        if isinstance(headers, str) and headers:
            command_parts.extend(["-H", headers])
        elif isinstance(headers, list):
            for header in headers:
                if isinstance(header, str) and header:
                    command_parts.extend(["-H", header])

        if burp:
            command_parts.extend(["--burp", burp])
        if blacklist:
            command_parts.extend(["--blacklist", blacklist])

        if threads:
            command_parts.extend(["-t", str(threads)])
        if concurrent:
            command_parts.extend(["-c", str(concurrent)])
        if depth is not None:
            command_parts.extend(["-d", str(depth)])
        if delay:
            command_parts.extend(["-k", str(delay)])
        if random_delay:
            command_parts.extend(["-K", str(random_delay)])
        if timeout:
            command_parts.extend(["-m", str(timeout)])

        if sitemap:
            command_parts.append("--sitemap")
        if robots:
            command_parts.append("--robots")
        if other_source:
            command_parts.append("-a")
        if include_subs:
            command_parts.append("-w")
        if include_other_source:
            command_parts.append("-r")
        if debug:
            command_parts.append("--debug")
        if verbose:
            command_parts.append("-v")
        if no_redirect:
            command_parts.append("--no-redirect")
        if version:
            command_parts.append("--version")

        if additional_args:
            command_parts.append(additional_args)

        command = " ".join(command_parts)

        logger.info("🕷️ Starting GoSpider crawling")
        result = execute_command(command)
        logger.info("📊 GoSpider crawling completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in gospider endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
