from flask import Blueprint, request, jsonify
import logging
import shlex
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_api_fuzz_schemathesis_bp = Blueprint("api_api_fuzz_schemathesis", __name__)


@api_api_fuzz_schemathesis_bp.route("/api/tools/api_fuzz/schemathesis", methods=["POST"])
def schemathesis():
    """Execute schemathesis property-based API testing against an OpenAPI/GraphQL schema."""
    try:
        params = request.json or {}
        schema = params.get("schema", "")
        base_url = params.get("base_url", "")
        checks = params.get("checks", "all")
        workers = params.get("workers", 1)
        max_examples = params.get("max_examples", 100)
        headers = params.get("headers", "")
        auth = params.get("auth", "")
        request_timeout = params.get("request_timeout", 10)
        timeout = params.get("timeout", 600)
        phases = params.get("phases", "")
        mode = params.get("mode", "")
        rate_limit = params.get("rate_limit", "")
        report_formats = params.get("report_formats", "")
        report_dir = params.get("report_dir", "")
        include_operation_id = params.get("include_operation_id", "")
        exclude_operation_id = params.get("exclude_operation_id", "")
        max_failures = params.get("max_failures", 0)
        additional_args = params.get("additional_args", "")

        if not schema:
            logger.warning("🧪 Schemathesis called without schema parameter")
            return jsonify({"error": "schema parameter is required"}), 400

        if mode and str(mode).lower() not in {"positive", "negative", "all"}:
            return jsonify({
                "error": "mode must be one of 'positive', 'negative', 'all'"
            }), 400

        parts = ["schemathesis", "run", shlex.quote(str(schema))]

        if checks:
            parts += ["--checks", shlex.quote(str(checks))]
        if workers:
            parts += ["--workers", str(int(workers))]
        if max_examples:
            parts += ["--max-examples", str(int(max_examples))]
        if request_timeout:
            parts += ["--request-timeout", str(int(request_timeout))]
        if base_url:
            parts += ["--url", shlex.quote(str(base_url))]
        if auth:
            parts += ["--auth", shlex.quote(str(auth))]
        if headers:
            for hdr in [h.strip() for h in str(headers).split(";") if h.strip()]:
                parts += ["-H", shlex.quote(hdr)]
        if phases:
            parts += ["--phases", shlex.quote(str(phases))]
        if mode:
            parts += ["--mode", shlex.quote(str(mode).lower())]
        if rate_limit:
            parts += ["--rate-limit", shlex.quote(str(rate_limit))]
        if report_formats:
            # --report takes a single comma-separated list of formats.
            # Passing repeated --report flags causes later values to
            # overwrite earlier ones, so join here.
            fmts = ",".join(
                f.strip() for f in str(report_formats).split(",") if f.strip()
            )
            if fmts:
                parts += ["--report", shlex.quote(fmts)]
        if report_dir:
            parts += ["--report-dir", shlex.quote(str(report_dir))]
        if include_operation_id:
            for op in [o.strip() for o in str(include_operation_id).split(",") if o.strip()]:
                parts += ["--include-operation-id", shlex.quote(op)]
        if exclude_operation_id:
            for op in [o.strip() for o in str(exclude_operation_id).split(",") if o.strip()]:
                parts += ["--exclude-operation-id", shlex.quote(op)]
        if max_failures and int(max_failures) > 0:
            parts += ["--max-failures", str(int(max_failures))]
        if additional_args:
            parts.append(str(additional_args))

        command = " ".join(parts)

        logger.info(
            f"🧪 Starting Schemathesis: schema={schema} workers={workers} "
            f"max_examples={max_examples}"
        )
        result = execute_command(command, timeout=timeout)

        # Remap success semantics. Schemathesis exit codes:
        #   0 = no findings, 1 = findings, 2 = usage/config error.
        # Treat "ran to completion" (0 or 1) as success=True and surface a
        # separate `findings` flag so callers can distinguish "clean run
        # with issues" from "tool failed to run".
        rc = result.get("return_code")
        timed_out = bool(result.get("timed_out"))
        if timed_out or rc is None:
            result["success"] = False
            result["findings"] = None
        elif rc in (0, 1):
            result["success"] = True
            result["findings"] = (rc == 1)
        else:
            result["success"] = False
            result["findings"] = None

        logger.info(
            f"📊 Schemathesis scan completed rc={rc} "
            f"findings={result.get('findings')}"
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in schemathesis endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
