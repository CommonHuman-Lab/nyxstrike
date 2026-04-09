# mcp_tools/password_cracking/hydra.py

from typing import Dict, Any
import asyncio

def register_hydra_tool(mcp, api_client, logger):
    @mcp.tool()
    async def hydra_attack(
        target: str,
        service: str,
        username: str = "",
        username_file: str = "",
        password: str = "",
        password_file: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
       Execute Hydra for password brute forcing with enhanced logging.

        Args:
            target: The target IP or hostname.
            service: The service to attack (ssh, ftp, http, etc.).
            username: Single username to test. Either this or username_file must be provided.
            username_file: File containing usernames. Either this or username must be provided.
            password: Single password to test. Either this or password_file must be provided.
            password_file: File containing passwords. Either this or password must be provided.
            additional_args: Additional Hydra arguments.

        Returns:
            Brute force attack results.

        Note:
            You must provide at least one of username or username_file, and at least one of password or password_file.
        """
        data = {
            "target": target,
            "service": service,
            "username": username,
            "username_file": username_file,
            "password": password,
            "password_file": password_file,
            "additional_args": additional_args
        }
        logger.info(f"🔑 Starting Hydra attack: {target}:{service}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/hydra", data)
        )
        if result.get("success"):
            logger.info(f"✅ Hydra attack completed for {target}")
        else:
            logger.error(f"❌ Hydra attack failed for {target}")
        return result
