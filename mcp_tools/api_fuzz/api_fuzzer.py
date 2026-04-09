# mcp_tools/api_fuzz/api_fuzzer.py

from typing import Dict, Any
import asyncio

def register_api_fuzzer_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def api_fuzzer(base_url: str, endpoints: str = "", methods: str = "GET,POST,PUT,DELETE", wordlist: str = "/usr/share/wordlists/api/api-endpoints.txt") -> Dict[str, Any]:
        """
        Advanced API endpoint fuzzing with intelligent parameter discovery.

        Args:
            base_url: Base URL of the API
            endpoints: Comma-separated list of specific endpoints to test
            methods: HTTP methods to test (comma-separated)
            wordlist: Wordlist for endpoint discovery

        Returns:
            API fuzzing results with endpoint discovery and vulnerability assessment
        """
        data = {
            "base_url": base_url,
            "endpoints": [e.strip() for e in endpoints.split(",") if e.strip()] if endpoints else [],
            "methods": [m.strip() for m in methods.split(",")],
            "wordlist": wordlist
        }

        logger.info(f"🔍 Starting API fuzzing: {base_url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/api_fuzzer", data)
        )

        if result.get("success"):
            fuzzing_type = result.get("fuzzing_type", "unknown")
            if fuzzing_type == "endpoint_testing":
                endpoint_count = len(result.get("results", []))
                logger.info(f"✅ API endpoint testing completed: {endpoint_count} endpoints tested")
            else:
                logger.info(f"✅ API endpoint discovery completed")
        else:
            logger.error("❌ API fuzzing failed")

        return result
