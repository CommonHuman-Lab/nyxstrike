from typing import Dict, Any
import asyncio

def register_web_scan_interactsh_tool(mcp, api_client, logger):
    @mcp.tool()
    async def interactsh_client(
        server: str = "",
        token: str = "",
        n: int = 1,
        poll_interval: int = 5,
        timeout: int = 60,
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Run interactsh-client to generate OOB interaction URLs and capture
        out-of-band interactions (blind SSRF, blind XSS, DNS exfiltration, etc.).

        Args:
            server: Custom interactsh server URL (default: uses public ProjectDiscovery servers)
            token: Authentication token for private server
            n: Number of interaction payload URLs to generate (default: 1)
            poll_interval: Polling interval in seconds between interaction checks (default: 5)
            timeout: Total time in seconds to listen for interactions before exiting (default: 60)
            additional_args: Additional interactsh-client flags

        Returns:
            Captured OOB interactions and generated payload URLs
        """
        data = {
            "server": server,
            "token": token,
            "n": n,
            "poll_interval": poll_interval,
            "timeout": timeout,
            "additional_args": additional_args,
        }
        logger.info(f"🔗 Starting interactsh-client (n={n}, poll_interval={poll_interval}s, timeout={timeout}s)")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/web_scan/interactsh", data)
        )
        if result.get("success"):
            logger.info("✅ interactsh-client completed")
        else:
            logger.error("❌ interactsh-client failed")
        return result
