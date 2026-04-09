# mcp_tools/net_scan/nmap.py

import asyncio
from typing import Dict, Any

def register_nmap(mcp, api_client, logger, CliColors):

    @mcp.tool()
    async def nmap_scan(target: str, scan_type: str = "-sV", ports: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute an enhanced Nmap scan against a target with real-time logging.

        Args:
            target: The IP address or hostname to scan
            scan_type: Scan type (e.g., -sV for version detection, -sC for scripts)
            ports: Comma-separated list of ports or port ranges
            additional_args: Additional Nmap arguments

        Returns:
            Scan results with enhanced telemetry
        """
        data: Dict[str, Any] = {
            "target": target,
            "scan_type": scan_type,
            "ports": ports,
            "additional_args": additional_args
        }
        logger.info(f"{CliColors.FIRE_RED}🔍 Initiating Nmap scan: {target}{CliColors.RESET}")

        # Use enhanced error handling by default
        data["use_recovery"] = True

        # Offload the blocking HTTP+subprocess call to a thread pool so the
        # asyncio event loop remains responsive
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/nmap", data)
        )

        if result.get("success"):
            logger.info(f"{CliColors.SUCCESS}✅ Nmap scan completed successfully for {target}{CliColors.RESET}")

            # Check for recovery information
            if result.get("recovery_info", {}).get("recovery_applied"):
                recovery_info = result["recovery_info"]
                attempts = recovery_info.get("attempts_made", 1)
                logger.info(f"{CliColors.HIGHLIGHT_YELLOW} Recovery applied: {attempts} attempts made {CliColors.RESET}")
        else:
            logger.error(f"{CliColors.ERROR}❌ Nmap scan failed for {target}{CliColors.RESET}")

            # Check for human escalation
            if result.get("human_escalation"):
                logger.error(f"{CliColors.CRITICAL} HUMAN ESCALATION REQUIRED {CliColors.RESET}")

        return result

    @mcp.tool()
    async def nmap_advanced_scan(target: str, scan_type: str = "-sS", ports: str = "",
                                 timing: str = "T4", nse_scripts: str = "", os_detection: bool = False,
                                 version_detection: bool = False, aggressive: bool = False,
                                 stealth: bool = False, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute advanced Nmap scans with custom NSE scripts and optimized timing.

        Args:
            target: The target IP address or hostname
            scan_type: Nmap scan type (e.g., -sS, -sT, -sU)
            ports: Specific ports to scan
            timing: Timing template (T0-T5)
            nse_scripts: Custom NSE scripts to run
            os_detection: Enable OS detection
            version_detection: Enable version detection
            aggressive: Enable aggressive scanning
            stealth: Enable stealth mode
            additional_args: Additional Nmap arguments

        Returns:
            Advanced Nmap scanning results with custom NSE scripts
        """
        data = {
            "target": target,
            "scan_type": scan_type,
            "ports": ports,
            "timing": timing,
            "nse_scripts": nse_scripts,
            "os_detection": os_detection,
            "version_detection": version_detection,
            "aggressive": aggressive,
            "stealth": stealth,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Advanced Nmap: {target}")

        # Offload the blocking HTTP+subprocess call to a thread pool so the
        # asyncio event loop remains responsive
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/nmap-advanced", data)
        )

        if result.get("success"):
            logger.info(f"✅ Advanced Nmap completed for {target}")
        else:
            logger.error(f"❌ Advanced Nmap failed for {target}")
        return result
