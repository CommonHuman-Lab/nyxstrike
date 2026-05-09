# mcp_tools/password_cracking/ophcrack.py

from typing import Dict, Any
import asyncio

def register_ophcrack_tool(mcp, api_client, logger):
    @mcp.tool()
    async def ophcrack_crack(
        hash_file: str = "",
        hash: str = "",
        tables_dir: str = "",
        tables: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute Ophcrack for Windows hash cracking.

        Description:
            This tool runs the Ophcrack utility to crack Windows password hashes. It accepts
            either a hash file (pwdump/session format) or an inline hash string. hash_file
            takes priority when both are provided. Optional rainbow tables directory and table
            set, and any additional command-line arguments for Ophcrack.

        Parameters:
            hash_file (str, optional): Path to the hash file (pwdump/session). Takes priority over hash.
            hash (str, optional): Inline hash string to crack (used when hash_file is not provided).
            tables_dir (str, optional): Path to rainbow tables directory.
            tables (str, optional): Table set string for -t option.
            additional_args (str, optional): Extra ophcrack CLI arguments.

        Returns:
            Dict[str, Any]: Result from Ophcrack execution, including success/error and output.

        Example usage:
            ophcrack_crack(
                hash_file="/path/to/hashes.txt",
                tables_dir="/path/to/tables",
                tables="VistaFree",
                additional_args="-v"
            )
            ophcrack_crack(
                hash="aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0",
                tables_dir="/path/to/tables"
            )
        """
        data = {
            "hash_file": hash_file,
            "hash": hash,
            "tables_dir": tables_dir,
            "tables": tables,
            "additional_args": additional_args
        }
        logger.info(f"Starting Ophcrack crack")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/password-cracking/ophcrack", data)
        )
        if result.get("success"):
            logger.info("Ophcrack crack completed successfully")
        else:
            logger.error("Ophcrack crack failed")
        return result