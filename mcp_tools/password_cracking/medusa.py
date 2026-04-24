# mcp_tools/password_cracking/medusa.py

from typing import Dict, Any
import asyncio

def register_medusa_tool(mcp, api_client, logger):
    @mcp.tool()
    async def medusa_attack(
        target: str,
        module: str,
        username: str = "",
        username_file: str = "",
        password: str = "",
        password_file: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute Medusa for password brute forcing with enhanced logging.

        Description:
            This tool runs the Medusa password brute force utility against a specified target and module/service.
            Supports single username/password or files for bulk testing. Additional Medusa CLI options can be
            passed via 'additional_args'.

        Parameters:
            target (str): Target hostname or IP address (maps to Medusa -h)
            module (str): Medusa module/service to attack (maps to -M)
            username (str, optional): Single username to test (maps to -u)
            username_file (str, optional): File with usernames (maps to -U)
            password (str, optional): Single password to test (maps to -p)
            password_file (str, optional): File with passwords (maps to -P)
            additional_args (str, optional): Extra Medusa CLI flags

        Returns:
            Dict[str, Any]: Brute force attack results, including success/error and output.

        Example usage:
            medusa_attack(
                target="192.168.1.10",
                module="ssh",
                username="admin",
                password_file="/path/to/passwords.txt",
                additional_args="-t 10 -s"
            )
        """
        data = {
            "target": target,
            "module": module,
            "username": username,
            "username_file": username_file,
            "password": password,
            "password_file": password_file,
            "additional_args": additional_args
        }
        logger.info(f"🔑 Starting Medusa attack: {target}:{module}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/medusa", data)
        )
        if result.get("success"):
            logger.info(f"✅ Medusa attack completed for {target}")
        else:
            logger.error(f"❌ Medusa attack failed for {target}")
        return result