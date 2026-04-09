from typing import Dict, Any
import asyncio

def register_osint_sherlock_tool(mcp, api_client, logger):
    @mcp.tool()
    async def sherlock(username: str) -> Dict[str, Any]:
        """
        Execute Sherlock for username investigation across social networks.

        Args:
            username: The username to investigate

        Returns:
            Sherlock investigation results
        """
        data = {
            "username": username
        }
        logger.info(f"🔍 Starting Sherlock: {username}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/osint/sherlock", data)
        )
        if result.get("success"):
            logger.info(f"✅ Sherlock completed for {username}")
        else:
            logger.error(f"❌ Sherlock failed for {username}")
        return result