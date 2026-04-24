# mcp_tools/web_framework/http_framework.py

from typing import Dict, Any, Optional
import asyncio

def register_http_framework_tool(mcp, api_client, logger, CliColors):

    @mcp.tool()
    async def http_framework_test(url: str, method: str = "GET", data: dict = {},
                           headers: dict = {}, cookies: dict = {}, action: str = "request") -> Dict[str, Any]:
        """
        Enhanced HTTP testing framework (Burp Suite alternative) for comprehensive web security testing.

        Args:
            url: Target URL to test
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            data: Request data/parameters
            headers: Custom headers
            cookies: Custom cookies
            action: Action to perform (request, spider, proxy_history, set_rules, set_scope, repeater, intruder)

        Returns:
            HTTP testing results with vulnerability analysis
        """
        data_payload = {
            "url": url,
            "method": method,
            "data": data,
            "headers": headers,
            "cookies": cookies,
            "action": action
        }

        logger.info(f"{CliColors.FIRE_RED}🔥 Starting HTTP Framework {action}: {url}{CliColors.RESET}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/http-framework", data_payload)
        )

        if result.get("success"):
            logger.info(f"{CliColors.SUCCESS}✅ HTTP Framework {action} completed for {url}{CliColors.RESET}")

            # Enhanced logging for vulnerabilities found
            if result.get("result", {}).get("vulnerabilities"):
                vuln_count = len(result["result"]["vulnerabilities"])
                logger.info(f"{CliColors.HIGHLIGHT_RED} Found {vuln_count} potential vulnerabilities {CliColors.RESET}")
        else:
            logger.error(f"{CliColors.ERROR}❌ HTTP Framework {action} failed for {url}{CliColors.RESET}")

        return result

    @mcp.tool()
    async def http_set_rules(rules: list) -> Dict[str, Any]:
        """Set match/replace rules used to rewrite parts of URL/query/headers/body before sending.
        Rule format: {'where':'url|query|headers|body','pattern':'regex','replacement':'string'}"""
        payload = {"action": "set_rules", "rules": rules}
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/http-framework", payload)
        )
        return result

    @mcp.tool()
    async def http_set_scope(host: str, include_subdomains: bool = True) -> Dict[str, Any]:
        """Define in-scope host (and optionally subdomains) so out-of-scope requests are skipped."""
        payload = {"action": "set_scope", "host": host, "include_subdomains": include_subdomains}
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/http-framework", payload)
        )
        return result

    @mcp.tool()
    async def http_repeater(request_spec: dict) -> Dict[str, Any]:
        """Send a crafted request (Burp Repeater equivalent). request_spec keys: url, method, headers, cookies, data."""
        payload = {"action": "repeater", "request": request_spec}
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/http-framework", payload)
        )
        return result

    @mcp.tool()
    async def http_intruder(url: str, method: str = "GET", location: str = "query", params: Optional[list] = None,
                      payloads: Optional[list] = None, base_data: Optional[dict] = None, max_requests: int = 100) -> Dict[str, Any]:
        """Simple Intruder (sniper) fuzzing. Iterates payloads over each param individually.
        location: query|body|headers|cookie."""
        payload = {
            "action": "intruder",
            "url": url,
            "method": method,
            "location": location,
            "params": params or [],
            "payloads": payloads or [],
            "base_data": base_data or {},
            "max_requests": max_requests
        }
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/http-framework", payload)
        )
        return result
