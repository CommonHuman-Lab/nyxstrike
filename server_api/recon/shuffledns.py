from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_recon_shuffledns_bp = Blueprint("api_recon_shuffledns", __name__)


@api_recon_shuffledns_bp.route("/api/tools/shuffledns", methods=["POST"])
def shuffledns():
    """Execute shuffleDNS for subdomain bruteforce/resolve/filter with wildcard handling."""
    try:
        params = request.json or {}

        domain = params.get("domain", "")
        domains = params.get("domains", [])
        auto_domain = params.get("auto_domain", False)
        list_file = params.get("list", "")
        wordlist = params.get("wordlist", "")
        resolver = params.get("resolver", "")
        trusted_resolver = params.get("trusted_resolver", "")
        raw_input = params.get("raw_input", "")
        mode = params.get("mode", "")

        threads = params.get("threads", 10000)

        output = params.get("output", "")
        json_output = params.get("json", False)
        wildcard_output = params.get("wildcard_output", "")

        massdns = params.get("massdns", "")
        massdns_cmd = params.get("massdns_cmd", "")
        directory = params.get("directory", "")

        retries = params.get("retries", 5)
        strict_wildcard = params.get("strict_wildcard", False)
        wildcard_threads = params.get("wildcard_threads", 250)

        silent = params.get("silent", False)
        version = params.get("version", False)
        verbose = params.get("verbose", False)
        no_color = params.get("no_color", False)

        update = params.get("update", False)
        disable_update_check = params.get("disable_update_check", False)

        additional_args = params.get("additional_args", "")

        if isinstance(domains, str):
            domains = [domains]
        elif not isinstance(domains, list):
            domains = []

        normalized_domains = []
        if isinstance(domain, str) and domain.strip():
            normalized_domains.append(domain.strip())
        for d in domains:
            if isinstance(d, str) and d.strip():
                normalized_domains.append(d.strip())

        valid_modes = {"", "bruteforce", "resolve", "filter"}
        if mode not in valid_modes:
            logger.warning("🌐 shuffleDNS called with invalid mode")
            return jsonify({
                "error": "Invalid mode. Use one of: bruteforce, resolve, filter"
            }), 400

        if not update and not version:
            if not normalized_domains and not list_file and not raw_input:
                logger.warning("🌐 shuffleDNS called without input source")
                return jsonify({
                    "error": "Provide at least one input: domain/domains, list, or raw_input"
                }), 400

            if mode == "bruteforce" and not wordlist:
                logger.warning("🌐 shuffleDNS bruteforce called without wordlist")
                return jsonify({
                    "error": "wordlist is required when mode is bruteforce"
                }), 400

        command_parts = ["shuffledns"]

        for d in normalized_domains:
            command_parts.extend(["-d", d])

        if auto_domain:
            command_parts.append("-ad")
        if list_file:
            command_parts.extend(["-l", list_file])
        if wordlist:
            command_parts.extend(["-w", wordlist])
        if resolver:
            command_parts.extend(["-r", resolver])
        if trusted_resolver:
            command_parts.extend(["-tr", trusted_resolver])
        if raw_input:
            command_parts.extend(["-ri", raw_input])
        if mode:
            command_parts.extend(["-mode", mode])

        if threads:
            command_parts.extend(["-t", str(threads)])

        if output:
            command_parts.extend(["-o", output])
        if json_output:
            command_parts.append("-j")
        if wildcard_output:
            command_parts.extend(["-wo", wildcard_output])

        if massdns:
            command_parts.extend(["-m", massdns])
        if massdns_cmd:
            command_parts.extend(["-mcmd", massdns_cmd])
        if directory:
            command_parts.extend(["-directory", directory])

        if retries:
            command_parts.extend(["-retries", str(retries)])
        if strict_wildcard:
            command_parts.append("-sw")
        if wildcard_threads:
            command_parts.extend(["-wt", str(wildcard_threads)])

        if silent:
            command_parts.append("-silent")
        if version:
            command_parts.append("-version")
        if verbose:
            command_parts.append("-v")
        if no_color:
            command_parts.append("-nc")

        if update:
            command_parts.append("-up")
        if disable_update_check:
            command_parts.append("-duc")

        if additional_args:
            command_parts.append(additional_args)

        command = " ".join(command_parts)

        logger.info("🔍 Starting shuffleDNS")
        result = execute_command(command)
        logger.info("📊 shuffleDNS completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in shuffledns endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
