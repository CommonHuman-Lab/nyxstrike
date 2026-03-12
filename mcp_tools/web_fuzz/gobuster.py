# mcp_tools/web_fuzz/gobuster.py

from typing import Dict, Any
import asyncio

def register_gobuster(mcp, hexstrike_client, logger, HexStrikeColors):

    @mcp.tool()
    async def gobuster_scan(url: str, mode: str = "dir", wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Gobuster to find directories, DNS subdomains, or virtual hosts with enhanced logging.

        Args:
            url: The target URL
            mode: Scan mode (dir, dns, fuzz, vhost)
            wordlist: Path to wordlist file
            additional_args: Additional Gobuster arguments

        Returns:
            Scan results with enhanced telemetry
        """
        data: Dict[str, Any] = {
            "url": url,
            "mode": mode,
            "wordlist": wordlist,
            "additional_args": additional_args
        }
        logger.info(f"{HexStrikeColors.CRIMSON}📁 Starting Gobuster {mode} scan: {url}{HexStrikeColors.RESET}")

        # Use enhanced error handling by default
        data["use_recovery"] = True
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_post("api/tools/gobuster", data)
        )

        if result.get("success"):
            logger.info(f"{HexStrikeColors.SUCCESS}✅ Gobuster scan completed for {url}{HexStrikeColors.RESET}")

            # Check for recovery information
            if result.get("recovery_info", {}).get("recovery_applied"):
                recovery_info = result["recovery_info"]
                attempts = recovery_info.get("attempts_made", 1)
                logger.info(f"{HexStrikeColors.HIGHLIGHT_YELLOW} Recovery applied: {attempts} attempts made {HexStrikeColors.RESET}")
        else:
            logger.error(f"{HexStrikeColors.ERROR}❌ Gobuster scan failed for {url}{HexStrikeColors.RESET}")

            # Check for alternative tool suggestion
            if result.get("alternative_tool_suggested"):
                alt_tool = result["alternative_tool_suggested"]
                logger.info(f"{HexStrikeColors.HIGHLIGHT_BLUE} Alternative tool suggested: {alt_tool} {HexStrikeColors.RESET}")

        return result
