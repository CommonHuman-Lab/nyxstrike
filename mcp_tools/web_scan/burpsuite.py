# mcp_tools/web_scan/burpsuite.py

from typing import Dict, Any
import asyncio


def register_burpsuite_tool(mcp, hexstrike_client, logger, HexStrikeColors):

    @mcp.tool()
    async def burpsuite_scan(project_file: str = "", config_file: str = "", target: str = "", headless: bool = False, scan_type: str = "", scan_config: str = "", output_file: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Burp Suite with enhanced logging.

        Args:
            project_file: Burp project file path
            config_file: Burp configuration file path
            target: Target URL
            headless: Run in headless mode
            scan_type: Type of scan to perform
            scan_config: Scan configuration
            output_file: Output file path
            additional_args: Additional Burp Suite arguments

        Returns:
            Burp Suite scan results
        """
        data = {
            "project_file": project_file,
            "config_file": config_file,
            "target": target,
            "headless": headless,
            "scan_type": scan_type,
            "scan_config": scan_config,
            "output_file": output_file,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Burp Suite scan")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_post("api/tools/burpsuite", data)
        )
        if result.get("success"):
            logger.info(f"✅ Burp Suite scan completed")
        else:
            logger.error(f"❌ Burp Suite scan failed")
        return result
    
    @mcp.tool()
    async def burpsuite_alternative_scan(target: str, scan_type: str = "comprehensive",
                                  headless: bool = True, max_depth: int = 3,
                                  max_pages: int = 50) -> Dict[str, Any]:
        """
        Comprehensive Burp Suite alternative combining HTTP framework and browser agent for complete web security testing.

        Args:
            target: Target URL or domain to scan
            scan_type: Type of scan (comprehensive, spider, passive, active)
            headless: Run browser in headless mode
            max_depth: Maximum crawling depth
            max_pages: Maximum pages to analyze

        Returns:
            Comprehensive security assessment results
        """
        data_payload = {
            "target": target,
            "scan_type": scan_type,
            "headless": headless,
            "max_depth": max_depth,
            "max_pages": max_pages
        }

        logger.info(f"{HexStrikeColors.BLOOD_RED}🔥 Starting Burp Suite Alternative {scan_type} scan: {target}{HexStrikeColors.RESET}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_post("api/tools/burpsuite-alternative", data_payload)
        )

        if result.get("success"):
            logger.info(f"{HexStrikeColors.SUCCESS}✅ Burp Suite Alternative scan completed for {target}{HexStrikeColors.RESET}")

            # Enhanced logging for comprehensive results
            if result.get("result", {}).get("summary"):
                summary = result["result"]["summary"]
                total_vulns = summary.get("total_vulnerabilities", 0)
                pages_analyzed = summary.get("pages_analyzed", 0)
                security_score = summary.get("security_score", 0)

                logger.info(f"{HexStrikeColors.HIGHLIGHT_BLUE} SCAN SUMMARY {HexStrikeColors.RESET}")
                logger.info(f"  📊 Pages Analyzed: {pages_analyzed}")
                logger.info(f"  🚨 Vulnerabilities: {total_vulns}")
                logger.info(f"  🛡️  Security Score: {security_score}/100")

                # Log vulnerability breakdown
                vuln_breakdown = summary.get("vulnerability_breakdown", {})
                for severity, count in vuln_breakdown.items():
                    if count > 0:
                        color = {
                                    'critical': HexStrikeColors.CRITICAL,
        'high': HexStrikeColors.FIRE_RED,
        'medium': HexStrikeColors.CYBER_ORANGE,
        'low': HexStrikeColors.YELLOW,
        'info': HexStrikeColors.INFO
    }.get(severity.lower(), HexStrikeColors.WHITE)

                        logger.info(f"  {color}{severity.upper()}: {count}{HexStrikeColors.RESET}")
        else:
            logger.error(f"{HexStrikeColors.ERROR}❌ Burp Suite Alternative scan failed for {target}{HexStrikeColors.RESET}")

        return result
