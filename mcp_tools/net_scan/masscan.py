# mcp_tools/net_scan/masscan.py

from typing import Dict, Any
import asyncio

def register_masscan_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def masscan_high_speed(target: str, ports: str = "1-65535", rate: int = 1000,
                          interface: str = "", router_mac: str = "", source_ip: str = "",
                          banners: bool = False, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Masscan for high-speed Internet-scale port scanning with intelligent rate limiting.

        Args:
            target: The target IP address or CIDR range
            ports: Port range to scan
            rate: Packets per second rate
            interface: Network interface to use
            router_mac: Router MAC address
            source_ip: Source IP address
            banners: Enable banner grabbing
            additional_args: Additional Masscan arguments

        Returns:
            High-speed port scanning results with intelligent rate limiting
        """
        data = {
            "target": target,
            "ports": ports,
            "rate": rate,
            "interface": interface,
            "router_mac": router_mac,
            "source_ip": source_ip,
            "banners": banners,
            "additional_args": additional_args
        }
        logger.info(f"🚀 Starting Masscan: {target} at rate {rate}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/masscan", data)
        )
        if result.get("success"):
            logger.info(f"✅ Masscan completed for {target}")
        else:
            logger.error(f"❌ Masscan failed for {target}")
        return result


