from typing import Dict, Any
from typing import Any, Dict
import asyncio

def register_ldapdomaindump_tool(mcp, api_client, logger):
    @mcp.tool()
    async def ldapdomaindump(hostname: str, username: str = "", password: str = "", authtype: str = "NTLM") -> Dict[str, Any]:
        """
         Run the ldapdomaindump tool with the provided parameters.

         Parameters:
           - hostname: The target hostname or IP address of the Active Directory domain.
           - username: (Optional) Username for authentication.
           - password: (Optional) Password for authentication.
           - authtype: (Optional) Authentication type (default: NTLM).

         Returns:
           - The output from running ldapdomaindump.
        """
        data = {
            "hostname": hostname,
            "username": username,
            "password": password,
            "authtype": authtype
        }
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, lambda: api_client.safe_post("api/tools/active_directory/ldapdomaindump", data)
            )
            return result
        except Exception as e:
            logger.error(f"Error running ldapdomaindump: {e}")
            return {"error": str(e)}