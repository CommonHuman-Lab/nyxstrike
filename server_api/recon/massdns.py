from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_recon_massdns_bp = Blueprint("api_recon_massdns", __name__)


@api_recon_massdns_bp.route("/api/tools/massdns", methods=["POST"])
def massdns():
    """Execute massdns for high-performance DNS resolution/bruteforce workflows."""
    try:
        params = request.json or {}

        domainlist = params.get("domainlist", "")
        bindto = params.get("bindto", "")
        busy_poll = params.get("busy_poll", False)
        resolve_count = params.get("resolve_count", 50)
        drop_group = params.get("drop_group", "")
        drop_user = params.get("drop_user", "")
        extended_input = params.get("extended_input", False)
        filter_code = params.get("filter", "")
        flush = params.get("flush", False)
        ignore_code = params.get("ignore", "")
        interval = params.get("interval", 500)
        error_log = params.get("error_log", "")
        norecurse = params.get("norecurse", False)
        output = params.get("output", "")
        predictable = params.get("predictable", False)
        processes = params.get("processes", 1)
        quiet = params.get("quiet", False)
        rand_src_ipv6 = params.get("rand_src_ipv6", "")
        rcvbuf = params.get("rcvbuf", 0)
        retry = params.get("retry", "")
        resolvers = params.get("resolvers", "")
        root = params.get("root", False)
        hashmap_size = params.get("hashmap_size", 10000)
        sndbuf = params.get("sndbuf", 0)
        status_format = params.get("status_format", "")
        sticky = params.get("sticky", False)
        socket_count = params.get("socket_count", 1)
        record_type = params.get("record_type", "A")
        verify_ip = params.get("verify_ip", False)
        outfile = params.get("outfile", "")
        additional_args = params.get("additional_args", "")

        if not domainlist and not resolvers and not additional_args:
            logger.warning("🌐 massdns called without domainlist")
            return jsonify({
                "error": "domainlist is required (path to input names file)"
            }), 400

        if status_format and status_format not in {"json", "ansi"}:
            logger.warning("🌐 massdns called with invalid status_format")
            return jsonify({
                "error": "status_format must be either 'json' or 'ansi'"
            }), 400

        command_parts = ["massdns"]

        if bindto:
            command_parts.extend(["-b", bindto])
        if busy_poll:
            command_parts.append("--busy-poll")
        if resolve_count:
            command_parts.extend(["-c", str(resolve_count)])
        if drop_group:
            command_parts.extend(["--drop-group", drop_group])
        if drop_user:
            command_parts.extend(["--drop-user", drop_user])
        if extended_input:
            command_parts.append("--extended-input")
        if filter_code:
            command_parts.extend(["--filter", str(filter_code)])
        if flush:
            command_parts.append("--flush")
        if ignore_code:
            command_parts.extend(["--ignore", str(ignore_code)])
        if interval:
            command_parts.extend(["-i", str(interval)])
        if error_log:
            command_parts.extend(["-l", error_log])
        if norecurse:
            command_parts.append("--norecurse")
        if output:
            command_parts.extend(["-o", output])
        if predictable:
            command_parts.append("--predictable")
        if processes:
            command_parts.extend(["--processes", str(processes)])
        if quiet:
            command_parts.append("-q")
        if rand_src_ipv6:
            command_parts.extend(["--rand-src-ipv6", rand_src_ipv6])
        if rcvbuf:
            command_parts.extend(["--rcvbuf", str(rcvbuf)])
        if retry:
            command_parts.extend(["--retry", str(retry)])
        if resolvers:
            command_parts.extend(["-r", resolvers])
        if root:
            command_parts.append("--root")
        if hashmap_size:
            command_parts.extend(["-s", str(hashmap_size)])
        if sndbuf:
            command_parts.extend(["--sndbuf", str(sndbuf)])
        if status_format:
            command_parts.extend(["--status-format", status_format])
        if sticky:
            command_parts.append("--sticky")
        if socket_count:
            command_parts.extend(["--socket-count", str(socket_count)])
        if record_type:
            command_parts.extend(["-t", record_type])
        if verify_ip:
            command_parts.append("--verify-ip")
        if outfile:
            command_parts.extend(["-w", outfile])

        if additional_args:
            command_parts.append(additional_args)

        if domainlist:
            command_parts.append(domainlist)

        command = " ".join(command_parts)

        logger.info("🔍 Starting massdns")
        result = execute_command(command)
        logger.info("📊 massdns completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in massdns endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
