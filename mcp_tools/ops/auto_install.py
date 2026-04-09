import asyncio
def register_auto_install_tools(mcp, api_client, logger):
    @mcp.tool()
    async def auto_install_missing_apt_tools() -> dict:
        """
        Detect and install missing apt-installable tools on the API server.

        Returns:
            Dictionary with attempted tools and installation results.
        """
        logger.info("🔧 Triggering auto-install of missing apt tools via API")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/auto-install-missing-apt", {})
        )
        if result.get("success"):
            logger.info(f"✅ Auto-install attempted for: {result.get('attempted_tools', [])}")
        else:
            logger.error("❌ Auto-install failed")
        return result