# mcp_tools/password_cracking/hashid.py

from typing import Dict, Any
import asyncio

def register_hashid_tool(mcp, api_client, logger):
    @mcp.tool()
    async def hashid(
        hash_value: str,
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Identify the type of a given hash value.

        Description:
            This tool takes a hash value as input and attempts to identify its type using various algorithms.
            Additional arguments can be passed to refine the identification process.

        Parameters:
            hash_value (str): The hash string to be identified.
            additional_args (str, optional): Extra CLI flags for hashID (e.g., '-m', '-e').

        Returns:
            Dict[str, Any]: Identification results, including success/error and identified hash type.

        Example usage:
            hashid(
                hash_value="5f4dcc3b5aa765d61d8327deb882cf99",
                additional_args="-m"
            )
        """
        data = {
            "hash_value": hash_value,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting hash identification for: {hash_value}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/password_cracking/hashid", data)
        )
        if result.get("success"):
            logger.info(f"✅ Hash identification completed for {hash_value}")
        else:
            logger.error(f"❌ Hash identification failed for {hash_value}")
        return result