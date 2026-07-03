# mcp_tools/web_scan/stingxss.py

from typing import Dict, Any, List, Optional
import asyncio


def register_stingxss_tool(mcp, api_client, logger):

    @mcp.tool()
    async def stingxss_scan(
        url: str,
        data: str = "",
        headers: Optional[Dict[str, str]] = None,
        cookies: str = "",
        proxy: str = "",
        threads: int = 5,
        timeout: int = 15,
        level: int = 1,
        crawl: bool = False,
        max_pages: int = 50,
        max_depth: int = 3,
        blind_callback: str = "",
        browser: bool = False,
        browser_headless: bool = True,
        test_stored: bool = False,
        poc: bool = False,
        inject_headers: Optional[List[str]] = None,
        custom_payloads: Optional[List[str]] = None,
        probe_filter: bool = True,
        evasion_chain: Optional[List[str]] = None,
        randomize_payloads: bool = False,
        graphql: bool = False,
        websocket: bool = False,
    ) -> Dict[str, Any]:
        """
        Run StingXSS context-aware XSS scanner.

        Args:
            url: Target URL
            data: POST body for form/API endpoints
            headers: Extra request headers
            cookies: Cookie header string
            proxy: HTTP proxy URL
            threads: Concurrent threads (1-20)
            timeout: Request timeout in seconds
            level: Scan depth (1=query params, 2=+headers, 3=+cookies)
            crawl: Crawl the site and test all discovered endpoints
            max_pages: Max pages to crawl
            max_depth: Crawl depth limit
            blind_callback: OOB callback URL for blind XSS (e.g. https://your.interactsh.io)
            browser: Confirm XSS execution via headless Chromium
            browser_headless: Run browser in headless mode
            test_stored: Attempt stored XSS detection
            poc: Generate ready-to-use PoC payloads for confirmed findings
            inject_headers: HTTP header names to inject into (e.g. ["Referer", "User-Agent"])
            custom_payloads: Additional payloads to include alongside curated list
            probe_filter: Pre-probe each parameter to filter unusable payloads (recommended)
            evasion_chain: WAF evasion transforms to apply (e.g. ["html_entity", "unicode"])
            randomize_payloads: Shuffle payload order per parameter
            graphql: Test GraphQL endpoints discovered or specified
            websocket: Test WebSocket endpoints

        Returns:
            StingXSS scan results with confirmed and potential XSS findings
        """
        payload = {
            "url": url,
            "data": data,
            "headers": headers or {},
            "cookies": cookies,
            "proxy": proxy,
            "threads": threads,
            "timeout": timeout,
            "level": level,
            "crawl": crawl,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "blind_callback": blind_callback,
            "browser": browser,
            "browser_headless": browser_headless,
            "test_stored": test_stored,
            "poc": poc,
            "inject_headers": inject_headers or [],
            "custom_payloads": custom_payloads or [],
            "probe_filter": probe_filter,
            "evasion_chain": evasion_chain or [],
            "randomize_payloads": randomize_payloads,
            "graphql": graphql,
            "websocket": websocket,
        }
        logger.info(f"Starting StingXSS scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/stingxss", payload)
        )
        if result.get("success"):
            findings = result.get("output", {}).get("total_findings", 0)
            logger.info(f"StingXSS scan completed — {findings} finding(s)")
        else:
            logger.error("StingXSS scan failed")
        return result
