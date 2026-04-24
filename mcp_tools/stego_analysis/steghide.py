# mcp_tools/stego_analysis/steghide.py

from typing import Dict, Any
import asyncio

def register_steghide_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def steghide_analysis(action: str, cover_file: str, embed_file: str = "", passphrase: str = "", output_file: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Steghide for steganography analysis with enhanced logging.

        Args:
            action: Action to perform (extract, embed, info)
            cover_file: Cover file for steganography
            embed_file: File to embed (for embed action)
            passphrase: Passphrase for steganography
            output_file: Output file path
            additional_args: Additional Steghide arguments

        Returns:
            Steganography analysis results
        """
        data = {
            "action": action,
            "cover_file": cover_file,
            "embed_file": embed_file,
            "passphrase": passphrase,
            "output_file": output_file,
            "additional_args": additional_args
        }
        logger.info(f"🖼️ Starting Steghide {action}: {cover_file}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/steghide", data)
        )
        if result.get("success"):
            logger.info(f"✅ Steghide {action} completed")
        else:
            logger.error(f"❌ Steghide {action} failed")
        return result
