# mcp_tools/param_discovery/arjun.py

from typing import Dict, Any
import asyncio

def register_arjun_tool(mcp, api_client, logger):
    @mcp.tool()
    async def arjun_parameter_discovery(url: str, method: str = "GET", wordlist: str = "",
                                 delay: int = 0, threads: int = 25, stable: bool = False,
                                 additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Arjun for HTTP parameter discovery with enhanced logging.

        Args:
            url: The target URL
            method: HTTP method to use
            wordlist: Custom wordlist file
            delay: Delay between requests
            threads: Number of threads
            stable: Use stable mode
            additional_args: Additional Arjun arguments

        Returns:
            HTTP parameter discovery results
        """
        data = {
            "url": url,
            "method": method,
            "wordlist": wordlist,
            "delay": delay,
            "threads": threads,
            "stable": stable,
            "additional_args": additional_args
        }
        logger.info(f"🎯 Starting Arjun parameter discovery: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/arjun", data)
        )
        if result.get("success"):
            logger.info(f"✅ Arjun parameter discovery completed for {url}")
        else:
            logger.error(f"❌ Arjun parameter discovery failed for {url}")
        return result
    
    @mcp.tool()
    async def arjun_scan(url: str, method: str = "GET", data: str = "", headers: str = "", timeout: str = "", output_file: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Arjun for parameter discovery with enhanced logging.

        Args:
            url: Target URL
            method: HTTP method (GET, POST, etc.)
            data: POST data for testing
            headers: Custom headers
            timeout: Request timeout
            output_file: Output file path
            additional_args: Additional Arjun arguments

        Returns:
            Parameter discovery results
        """
        payload = {
            "url": url,
            "method": method,
            "data": data,
            "headers": headers,
            "timeout": timeout,
            "output_file": output_file,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Arjun parameter discovery: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/arjun", payload)
        )
        if result.get("success"):
            logger.info(f"✅ Arjun completed for {url}")
        else:
            logger.error(f"❌ Arjun failed for {url}")
        return result

