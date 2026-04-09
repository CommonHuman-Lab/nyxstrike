# mcp_tools/vuln_scan/nuclei.py

from typing import Dict, Any
import asyncio

def register_nuclei(mcp, api_client, logger, CliColors):
    
    @mcp.tool()
    async def nuclei_scan(target: str, severity: str = "", tags: str = "", template: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Nuclei vulnerability scanner with enhanced logging and real-time progress.

        Args:
            target: The target URL or IP
            severity: Filter by severity (critical,high,medium,low,info)
            tags: Filter by tags (e.g. cve,rce,lfi)
            template: Custom template path
            additional_args: Additional Nuclei arguments

        Returns:
            Scan results with discovered vulnerabilities and telemetry
        """
        data: Dict[str, Any] = {
            "target": target,
            "severity": severity,
            "tags": tags,
            "template": template,
            "additional_args": additional_args
        }
        logger.info(f"{CliColors.BLOOD_RED}🔬 Starting Nuclei vulnerability scan: {target}{CliColors.RESET}")

        # Use enhanced error handling by default
        data["use_recovery"] = True
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/nuclei", data)
        )

        if result.get("success"):
            logger.info(f"{CliColors.SUCCESS}✅ Nuclei scan completed for {target}{CliColors.RESET}")

            # Enhanced vulnerability reporting
            if result.get("stdout") and "CRITICAL" in result["stdout"]:
                logger.warning(f"{CliColors.CRITICAL} CRITICAL vulnerabilities detected! {CliColors.RESET}")
            elif result.get("stdout") and "HIGH" in result["stdout"]:
                logger.warning(f"{CliColors.FIRE_RED} HIGH severity vulnerabilities found! {CliColors.RESET}")

            # Check for recovery information
            if result.get("recovery_info", {}).get("recovery_applied"):
                recovery_info = result["recovery_info"]
                attempts = recovery_info.get("attempts_made", 1)
                logger.info(f"{CliColors.HIGHLIGHT_YELLOW} Recovery applied: {attempts} attempts made {CliColors.RESET}")
        else:
            logger.error(f"{CliColors.ERROR}❌ Nuclei scan failed for {target}{CliColors.RESET}")

        return result
