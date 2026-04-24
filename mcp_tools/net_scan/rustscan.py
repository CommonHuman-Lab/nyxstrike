# mcp_tools/net_scan/rustscan.py

from typing import Dict, Any
import asyncio

def register_rustscan_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def rustscan_fast_scan(target: str, ports: str = "", ulimit: int = 5000,
                          batch_size: int = 4500, timeout: int = 1500,
                          scripts: bool = False, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Rustscan for ultra-fast port scanning with enhanced logging.

        Args:
            target: The target IP address or hostname
            ports: Specific ports to scan (e.g., "22,80,443")
            ulimit: File descriptor limit
            batch_size: Batch size for scanning
            timeout: Timeout in milliseconds
            scripts: Run Nmap scripts on discovered ports
            additional_args: Additional Rustscan arguments

        Returns:
            Ultra-fast port scanning results
        """
        data = {
            "target": target,
            "ports": ports,
            "ulimit": ulimit,
            "batch_size": batch_size,
            "timeout": timeout,
            "scripts": scripts,
            "additional_args": additional_args
        }
        logger.info(f"⚡ Starting Rustscan: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/rustscan", data)
        )
        if result.get("success"):
            logger.info(f"✅ Rustscan completed for {target}")
        else:
            logger.error(f"❌ Rustscan failed for {target}")
        return result

