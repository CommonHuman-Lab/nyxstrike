# mcp_tools/password_cracking/john.py

from typing import Dict, Any
import asyncio

def register_john_tool(mcp, api_client, logger):
    @mcp.tool()
    async def john_crack(
        hash_file: str,
        wordlist: str = "/usr/share/wordlists/rockyou.txt",
        format_type: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute John the Ripper for password cracking with enhanced logging.

        Args:
            hash_file: File containing password hashes
            wordlist: Wordlist file to use
            format_type: Hash format type
            additional_args: Additional John arguments

        Returns:
            Password cracking results
        """
        data = {
            "hash_file": hash_file,
            "wordlist": wordlist,
            "format": format_type,
            "additional_args": additional_args
        }
        logger.info(f"🔐 Starting John the Ripper: {hash_file}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/john", data)
        )
        if result.get("success"):
            logger.info(f"✅ John the Ripper completed")
        else:
            logger.error(f"❌ John the Ripper failed")
        return result
