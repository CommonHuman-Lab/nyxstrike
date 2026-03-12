# mcp_tools/vuln_scan/nuclei.py

from typing import Dict, Any
import asyncio

def register_nuclei(mcp, hexstrike_client, logger, HexStrikeColors):
    
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
        logger.info(f"{HexStrikeColors.BLOOD_RED}🔬 Starting Nuclei vulnerability scan: {target}{HexStrikeColors.RESET}")

        # Use enhanced error handling by default
        data["use_recovery"] = True
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_post("api/tools/nuclei", data)
        )

        if result.get("success"):
            logger.info(f"{HexStrikeColors.SUCCESS}✅ Nuclei scan completed for {target}{HexStrikeColors.RESET}")

            # Enhanced vulnerability reporting
            if result.get("stdout") and "CRITICAL" in result["stdout"]:
                logger.warning(f"{HexStrikeColors.CRITICAL} CRITICAL vulnerabilities detected! {HexStrikeColors.RESET}")
            elif result.get("stdout") and "HIGH" in result["stdout"]:
                logger.warning(f"{HexStrikeColors.FIRE_RED} HIGH severity vulnerabilities found! {HexStrikeColors.RESET}")

            # Check for recovery information
            if result.get("recovery_info", {}).get("recovery_applied"):
                recovery_info = result["recovery_info"]
                attempts = recovery_info.get("attempts_made", 1)
                logger.info(f"{HexStrikeColors.HIGHLIGHT_YELLOW} Recovery applied: {attempts} attempts made {HexStrikeColors.RESET}")
        else:
            logger.error(f"{HexStrikeColors.ERROR}❌ Nuclei scan failed for {target}{HexStrikeColors.RESET}")

        return result
