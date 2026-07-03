# mcp_tools/web_scan/breachsql.py

from typing import Dict, Any, List, Optional
import asyncio


def register_breachsql_tool(mcp, api_client, logger):

    @mcp.tool()
    async def breachsql_scan(
        url: str,
        data: str = "",
        headers: Optional[Dict[str, str]] = None,
        cookies: str = "",
        proxy: str = "",
        threads: int = 5,
        timeout: int = 15,
        level: int = 1,
        dbms: str = "auto",
        technique: str = "EBTUO",
        time_threshold: int = 4,
        risk: int = 1,
        path_params: Optional[List[str]] = None,
        cookie_params: Optional[List[str]] = None,
        header_params: Optional[List[str]] = None,
        exploit: bool = False,
        dump: str = "",
        dump_all: bool = False,
        crawl: bool = False,
        max_pages: int = 100,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Run BreachSQL SQL injection detection and exploitation.

        Args:
            url: Target URL (include the vulnerable parameter, e.g. /item?id=1)
            data: POST body (URL-encoded or JSON string)
            headers: Extra request headers as a dict
            cookies: Cookie header string
            proxy: HTTP proxy URL
            threads: Concurrent threads (1-20)
            timeout: Request timeout in seconds
            level: Scan depth (1=params only, 2=+headers, 3=+cookies)
            dbms: Force backend (auto|mysql|mssql|postgres|sqlite|oracle)
            technique: Detection techniques (letters: E=error B=boolean T=time U=union O=oob)
            time_threshold: Seconds before a time-based injection is flagged
            risk: Payload risk level (1-3)
            path_params: Path segment names to inject (e.g. ["id"])
            cookie_params: Cookie names to inject into
            header_params: HTTP header names to inject into
            exploit: After detection, dump version/user/db/tables automatically
            dump: Table name to dump rows from
            dump_all: Dump every discovered table
            crawl: Crawl the site and test discovered endpoints
            max_pages: Max pages to crawl
            max_depth: Crawl depth limit

        Returns:
            BreachSQL scan results with findings, injected parameters, and extracted data
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
            "dbms": dbms,
            "technique": technique,
            "time_threshold": time_threshold,
            "risk": risk,
            "path_params": path_params or [],
            "cookie_params": cookie_params or [],
            "header_params": header_params or [],
            "exploit": exploit,
            "dump": dump,
            "dump_all": dump_all,
            "crawl": crawl,
            "max_pages": max_pages,
            "max_depth": max_depth,
        }
        logger.info(f"Starting BreachSQL scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/breachsql", payload)
        )
        if result.get("success"):
            findings = result.get("output", {}).get("total_findings", 0)
            logger.info(f"BreachSQL scan completed — {findings} finding(s)")
        else:
            logger.error("BreachSQL scan failed")
        return result
