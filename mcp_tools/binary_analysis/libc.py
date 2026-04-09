# mcp_tools/binary_analysis/libc.py

from typing import Dict, Any
import asyncio

def register_libc_tools(mcp, api_client, logger):
    
    @mcp.tool()
    async def libc_database_lookup(action: str = "find", symbols: str = "",
                            libc_id: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute libc-database for libc identification and offset lookup.

        Args:
            action: Action to perform (find, dump, download)
            symbols: Symbols with offsets for find action (format: "symbol1:offset1 symbol2:offset2")
            libc_id: Libc ID for dump/download actions
            additional_args: Additional arguments

        Returns:
            Libc database lookup results
        """
        data = {
            "action": action,
            "symbols": symbols,
            "libc_id": libc_id,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting libc-database {action}: {symbols or libc_id}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/libc-database", data)
        )
        if result.get("success"):
            logger.info(f"✅ libc-database {action} completed")
        else:
            logger.error(f"❌ libc-database {action} failed")
        return result
