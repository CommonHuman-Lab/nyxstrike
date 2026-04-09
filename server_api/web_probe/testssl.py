from flask import Blueprint, request, jsonify
import logging
import shlex
import shutil
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_probe_testssl_bp = Blueprint("api_web_probe_testssl", __name__)


def _append_value(args, flag, value):
    if value not in ("", None):
        args.extend([flag, str(value)])


def _append_bool(args, enabled, flag):
    if enabled:
        args.append(flag)


@api_web_probe_testssl_bp.route("/api/tools/testssl", methods=["POST"])
def testssl():
    """Execute testssl.sh for TLS/SSL analysis"""
    try:
        params = request.json or {}

        target = str(params.get("target", "")).strip()
        help_mode = params.get("help_mode", False)
        banner = params.get("banner", False)
        version = params.get("version", False)
        local_mode = params.get("local_mode", False)
        local_pattern = str(params.get("local_pattern", "")).strip()

        standalone_count = sum([
            bool(help_mode),
            bool(banner),
            bool(version),
            bool(local_mode or local_pattern),
        ])

        if standalone_count > 1:
            return jsonify({"error": "Only one standalone mode may be used at a time"}), 400

        if standalone_count and target:
            return jsonify({"error": "Standalone modes cannot be combined with a target URI"}), 400

        file_input = str(params.get("file_input", "")).strip()
        mx = str(params.get("mx", "")).strip()

        if not standalone_count and not target and not file_input and not mx:
            logger.warning("🔐 testssl.sh called without target or standalone mode")
            return jsonify({"error": "Target is required unless using a standalone mode, --file, or --mx"}), 400

        valid_modes = {"serial", "parallel"}
        valid_warnings = {"", "batch", "off"}
        valid_nodns = {"", "min", "none"}
        valid_mapping = {"", "openssl", "iana", "rfc", "no-openssl", "no-iana", "no-rfc"}
        valid_severity = {"", "LOW", "MEDIUM", "HIGH", "CRITICAL"}

        mode = str(params.get("mode", "serial")).strip()
        warnings = str(params.get("warnings", "")).strip()
        nodns = str(params.get("nodns", "")).strip()
        mapping = str(params.get("mapping", "")).strip()
        severity = str(params.get("severity", "")).strip().upper()

        if mode not in valid_modes:
            return jsonify({"error": "mode must be one of: serial, parallel"}), 400
        if warnings not in valid_warnings:
            return jsonify({"error": "warnings must be one of: batch, off"}), 400
        if nodns not in valid_nodns:
            return jsonify({"error": "nodns must be one of: min, none"}), 400
        if mapping not in valid_mapping:
            return jsonify({"error": "mapping must be one of: openssl, iana, rfc, no-openssl, no-iana, no-rfc"}), 400
        if severity not in valid_severity:
            return jsonify({"error": "severity must be one of: LOW, MEDIUM, HIGH, CRITICAL"}), 400

        color = params.get("color", 0)
        debug = params.get("debug", 0)
        socket_timeout = params.get("socket_timeout", 0)
        openssl_timeout = params.get("openssl_timeout", 0)

        if color not in (0, 1, 2, 3):
            return jsonify({"error": "color must be one of: 0, 1, 2, 3"}), 400
        if not isinstance(debug, int) or debug < 0 or debug > 6:
            return jsonify({"error": "debug must be an integer between 0 and 6"}), 400
        if not isinstance(socket_timeout, int) or socket_timeout < 0:
            return jsonify({"error": "socket_timeout must be a non-negative integer"}), 400
        if not isinstance(openssl_timeout, int) or openssl_timeout < 0:
            return jsonify({"error": "openssl_timeout must be a non-negative integer"}), 400

        testssl_executable = shutil.which('testssl') or shutil.which('testssl.sh')
        if not testssl_executable:
            logger.error("Neither 'testssl' nor 'testssl.sh' found on system PATH.")
            return jsonify({"error": "testssl tool not found"}), 400

        # Prepare argument list with the appropriate executable
        args = [testssl_executable]

        if help_mode:
            args.append("--help")
        elif banner:
            args.append("--banner")
        elif version:
            args.append("--version")
        elif local_mode or local_pattern:
            args.append("--local")
            if local_pattern:
                args.append(local_pattern)
        else:
            _append_value(args, "--starttls", str(params.get("starttls", "")).strip())
            _append_value(args, "--xmpphost", str(params.get("xmpphost", "")).strip())
            _append_value(args, "--mx", mx)
            _append_value(args, "--file", file_input)
            _append_value(args, "--mode", mode)
            _append_value(args, "--warnings", warnings)
            if socket_timeout:
                _append_value(args, "--socket-timeout", socket_timeout)
            if openssl_timeout:
                _append_value(args, "--openssl-timeout", openssl_timeout)

            _append_bool(args, params.get("each_cipher", False), "--each-cipher")
            _append_bool(args, params.get("cipher_per_proto", False), "--cipher-per-proto")
            _append_bool(args, params.get("categories", False), "--std")
            _append_bool(args, params.get("forward_secrecy", False), "--forward-secrecy")
            _append_bool(args, params.get("protocols", True), "--protocols")
            _append_bool(args, params.get("grease", False), "--grease")
            _append_bool(args, params.get("server_defaults", True), "--server-defaults")
            _append_bool(args, params.get("server_preference", False), "--server-preference")
            _append_value(args, "--single-cipher", str(params.get("single_cipher", "")).strip())
            _append_bool(args, params.get("client_simulation", False), "--client-simulation")
            _append_bool(args, params.get("headers", False), "--headers")
            _append_bool(args, params.get("vulnerable", False), "--vulnerable")

            _append_bool(args, params.get("full", False), "--full")
            _append_bool(args, params.get("bugs", False), "--bugs")
            _append_bool(args, params.get("assume_http", False), "--assume-http")
            _append_bool(args, params.get("ssl_native", False), "--ssl-native")
            _append_value(args, "--openssl", str(params.get("openssl_path", "")).strip())
            _append_value(args, "--proxy", str(params.get("proxy", "")).strip())
            _append_bool(args, params.get("ipv4_only", False), "-4")
            _append_bool(args, params.get("ipv6_only", False), "-6")
            _append_value(args, "--ip", str(params.get("ip", "")).strip())
            _append_value(args, "--nodns", nodns)
            _append_bool(args, params.get("sneaky", False), "--sneaky")
            _append_value(args, "--user-agent", str(params.get("user_agent", "")).strip())
            _append_bool(args, params.get("ids_friendly", False), "--ids-friendly")
            _append_bool(args, params.get("phone_out", False), "--phone-out")
            _append_value(args, "--add-ca", str(params.get("add_ca", "")).strip())
            _append_value(args, "--mtls", str(params.get("mtls", "")).strip())
            _append_value(args, "--basicauth", str(params.get("basicauth", "")).strip())
            _append_value(args, "--reqheader", str(params.get("reqheader", "")).strip())
            _append_bool(args, params.get("rating_only", False), "--rating-only")

            _append_bool(args, params.get("quiet", True), "--quiet")
            _append_bool(args, params.get("wide", False), "--wide")
            _append_bool(args, params.get("show_each", False), "--show-each")
            _append_value(args, "--mapping", mapping)
            _append_value(args, "--color", color)
            _append_bool(args, params.get("colorblind", False), "--colorblind")
            if debug:
                _append_value(args, "--debug", debug)
            _append_bool(args, params.get("disable_rating", False), "--disable-rating")

            _append_value(args, "--logfile", str(params.get("logfile", "")).strip())
            _append_bool(args, params.get("json_output", False), "--json")
            _append_value(args, "--jsonfile", str(params.get("jsonfile", "")).strip())
            _append_bool(args, params.get("json_pretty", False), "--json-pretty")
            _append_value(args, "--jsonfile-pretty", str(params.get("jsonfile_pretty", "")).strip())
            _append_bool(args, params.get("csv_output", False), "--csv")
            _append_value(args, "--csvfile", str(params.get("csvfile", "")).strip())
            _append_bool(args, params.get("html_output", False), "--html")
            _append_value(args, "--htmlfile", str(params.get("htmlfile", "")).strip())
            _append_value(args, "--outfile", str(params.get("outfile", "")).strip())
            _append_bool(args, params.get("hints", False), "--hints")
            _append_value(args, "--severity", severity)
            _append_bool(args, params.get("append", False), "--append")
            _append_bool(args, params.get("overwrite", False), "--overwrite")
            _append_value(args, "--outprefix", str(params.get("outprefix", "")).strip())

            additional_args = str(params.get("additional_args", "")).strip()
            if additional_args:
                args.extend(shlex.split(additional_args))

            if target:
                args.append(target)

        command = " ".join(shlex.quote(arg) for arg in args)

        logger.info(f"🔐 Starting testssl.sh analysis: {target or 'standalone mode'}")
        result = execute_command(command, use_cache=False)
        logger.info(f"📊 testssl.sh analysis completed for {target or 'standalone mode'}")
        return jsonify(result)
    except ValueError as e:
        logger.error(f"💥 Invalid testssl.sh arguments: {str(e)}")
        return jsonify({"error": f"Invalid arguments: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"💥 Error in testssl.sh endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
