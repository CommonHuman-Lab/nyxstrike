# mcp_tools/password_cracking/patator.py


from typing import Dict, Any
import asyncio

def register_patator_tool(mcp, api_client, logger):
    @mcp.tool()
    async def patator_attack(
        module: str,
        target: str,
        username: str = "",
        username_file: str = "",
        password: str = "",
        password_file: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        API endpoint to execute Patator for password brute forcing.

        This tool allows clients to initiate a password brute force attack using the Patator tool.
        It supports multiple modules (e.g., ssh, ftp, http) and flexible input for usernames and passwords,
        including single values or files containing lists. Enhanced logging is provided for audit and debugging.

        Parameters:
          - module (str): Patator module to use (e.g., 'ssh_login', 'ftp_login'). Required.
          - target (str): Target host or address for the attack. Required.
          - username (str): Single username to test (optional).
          - username_file (str): Path to file containing usernames (optional, mutually exclusive with 'username').
          - password (str): Single password to test (optional).
          - password_file (str): Path to file containing passwords (optional, mutually exclusive with 'password').
          - additional_args (str): Extra Patator command-line arguments (optional).

        Returns:
          - Dict[str, Any]: Result from Patator execution, including success/error and output.
        """
        data = {
            "module": module,
            "target": target,
            "username": username,
            "username_file": username_file,
            "password": password,
            "password_file": password_file,
            "additional_args": additional_args
        }
        logger.info(f"🔑 Starting Patator attack: {target}:{module}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/patator", data)
        )
        if result.get("success"):
            logger.info(f"✅ Patator attack completed for {target}")
        else:
            logger.error(f"❌ Patator attack failed for {target}")
        return result