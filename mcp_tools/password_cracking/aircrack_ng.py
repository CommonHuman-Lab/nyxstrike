# mcp_tools/password_cracking/aircrack_ng.py

from typing import Dict, Any, Optional, List
import asyncio

def register_aircrack_ng_tools(mcp, api_client, logger):

    @mcp.tool()
    async def aircrack_ng_analysis(
        capture_files: List[str],
        wordlist: Optional[str] = None,
        bssid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute Aircrack-ng for Wi-Fi password cracking.

        Args:
            capture_files (List[str]): List of capture file paths (.cap, .ivs, etc.).
            wordlist (str): Path to a wordlist file.
            bssid (str, optional): Target BSSID (AP MAC address).

        Returns:
            dict: Results of the Aircrack-ng analysis or error information.
        """
        if not capture_files:
            return {"success": False, "error": "At least one capture file must be provided."}
        
        if not wordlist:
            return {"success": False, "error": "A wordlist file must be provided."}

        logger.info(f"🔍 Starting Aircrack-ng analysis on: {capture_files} with wordlist: {wordlist}")

        payload = {
            "capture_files": capture_files,
            "bssid": bssid,
            "wordlist": wordlist
        }

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/password_cracking/aircrack_ng", payload)
        )
        if result.get("success"):
            logger.info("✅ Aircrack-ng analysis completed")
        else:
            logger.error("❌ Aircrack-ng analysis failed")
        return result