# mcp_tools/system_monitoring.py

from typing import Dict, Any
import asyncio

def register_system_monitoring_tools(mcp, api_client, logger):
    @mcp.tool()
    async def server_health() -> Dict[str, Any]:
        """
        Check the health status of the API server.

        Returns:
            Server health information with tool availability and telemetry
        """
        logger.info("🏥 Checking API server health")
        result = api_client.check_health()
        if result.get("status") == "healthy":
            logger.info(f"✅ Server is healthy - {result.get('total_tools_available', 0)} tools available")
        else:
            logger.warning(f"⚠️  Server health check returned: {result.get('status', 'unknown')}")
        return result

    @mcp.tool()
    async def get_cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics from the API server.

        Returns:
            Cache performance statistics
        """
        logger.info(f"💾 Getting cache statistics")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get("api/cache/stats")
        )
        if "hit_rate" in result:
            logger.info(f"📊 Cache hit rate: {result.get('hit_rate', 'unknown')}")
        return result

    @mcp.tool()
    async def clear_cache() -> Dict[str, Any]:
        """
        Clear the cache on the API server.

        Returns:
            Cache clear operation results
        """
        logger.info(f"🧹 Clearing server cache")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/cache/clear", {})
        )
        if result.get("success"):
            logger.info(f"✅ Cache cleared successfully")
        else:
            logger.error(f"❌ Failed to clear cache")
        return result

    @mcp.tool()
    async def get_telemetry() -> Dict[str, Any]:
        """
        Get system telemetry from the API server.

        Returns:
            System performance and usage telemetry
        """
        logger.info(f"📈 Getting system telemetry")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get("api/telemetry")
        )
        if "commands_executed" in result:
            logger.info(f"📊 Commands executed: {result.get('commands_executed', 0)}")
        return result
