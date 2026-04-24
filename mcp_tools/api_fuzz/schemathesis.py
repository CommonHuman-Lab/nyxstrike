# mcp_tools/api_fuzz/schemathesis.py

from typing import Dict, Any
import asyncio


def register_api_fuzz_schemathesis_tool(mcp, api_client, logger):

    @mcp.tool()
    async def schemathesis(
        schema: str,
        base_url: str = "",
        checks: str = "all",
        workers: int = 1,
        max_examples: int = 100,
        headers: str = "",
        auth: str = "",
        request_timeout: int = 10,
        timeout: int = 600,
        phases: str = "",
        mode: str = "",
        rate_limit: str = "",
        report_formats: str = "",
        report_dir: str = "",
        include_operation_id: str = "",
        exclude_operation_id: str = "",
        max_failures: int = 0,
        additional_args: str = "",
    ) -> Dict[str, Any]:
        """
        Run Schemathesis property-based API testing against an OpenAPI or GraphQL schema.

        Args:
            schema: URL or file path to the OpenAPI/GraphQL schema (required)
            base_url: Override the API base URL from the schema
            checks: Comma-separated checks to run (e.g. "all", "not_a_server_error,status_code_conformance")
            workers: Number of parallel workers (default 1)
            max_examples: Hypothesis max examples per endpoint (default 100)
            headers: Extra headers as "Name: value" pairs separated by ';' (e.g. "Authorization: Bearer X;X-Env: qa")
            auth: Basic auth credentials in "user:pass" form
            request_timeout: Per-request timeout in seconds (default 10)
            timeout: Overall run timeout in seconds (default 600)
            phases: Comma-separated phases to run, e.g. "examples,coverage,fuzzing,stateful" (maps to --phases)
            mode: Test data generation mode — one of "positive", "negative", "all" (maps to --mode)
            rate_limit: Throttle requests, e.g. "3/s", "120/m" (maps to --rate-limit)
            report_formats: Comma-separated report formats, e.g. "har,ndjson,junit" (one --report flag per value)
            report_dir: Directory to write reports into (maps to --report-dir)
            include_operation_id: Comma-separated operationIds to include (one --include-operation-id per value)
            exclude_operation_id: Comma-separated operationIds to exclude (one --exclude-operation-id per value)
            max_failures: Stop the run after N failures (maps to --max-failures; 0 disables)
            additional_args: Additional schemathesis flags to pass through

        Returns:
            Schemathesis run results including discovered issues and summary
        """
        data = {
            "schema": schema,
            "base_url": base_url,
            "checks": checks,
            "workers": workers,
            "max_examples": max_examples,
            "headers": headers,
            "auth": auth,
            "request_timeout": request_timeout,
            "timeout": timeout,
            "phases": phases,
            "mode": mode,
            "rate_limit": rate_limit,
            "report_formats": report_formats,
            "report_dir": report_dir,
            "include_operation_id": include_operation_id,
            "exclude_operation_id": exclude_operation_id,
            "max_failures": max_failures,
            "additional_args": additional_args,
        }

        logger.info(
            f"🧪 Starting Schemathesis scan: schema={schema} "
            f"workers={workers} max_examples={max_examples}"
        )
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/api_fuzz/schemathesis", data)
        )

        if result.get("success"):
            if result.get("findings"):
                logger.info("✅ Schemathesis scan completed — findings reported")
            else:
                logger.info("✅ Schemathesis scan completed — no findings")
        else:
            logger.error("❌ Schemathesis scan failed to run")

        return result
