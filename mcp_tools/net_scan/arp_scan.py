# mcp_tools/net_scan/arp_scan.py

from typing import Dict, Any
import asyncio

def register_arp_scan_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def arp_scan_discovery(target: str = "", interface: str = "", local_network: bool = False,
                          timeout: int = 500, retry: int = 3, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute arp-scan for network discovery with enhanced logging.

        Args:
            target: The target IP range (if not using local_network)
            interface: Network interface to use
            local_network: Scan local network
            timeout: Timeout in milliseconds
            retry: Number of retries
            additional_args: Additional arp-scan arguments

        Returns:
            Network discovery results via ARP scanning
        """
        data = {
            "target": target,
            "interface": interface,
            "local_network": local_network,
            "timeout": timeout,
            "retry": retry,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting arp-scan: {target if target else 'local network'}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/arp-scan", data)
        )
        if result.get("success"):
            logger.info(f"✅ arp-scan completed")
        else:
            logger.error(f"❌ arp-scan failed")
        return result