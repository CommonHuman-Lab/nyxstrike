# mcp_tools/smb_enum/enum4linux.py

from typing import Dict, Any
import asyncio

def register_enum4linux_tool(mcp, api_client, logger):
    @mcp.tool()
    async def enum4linux_scan(target: str, additional_args: str = "-a") -> Dict[str, Any]:
        """
        Execute Enum4linux for SMB enumeration with enhanced logging.

        Args:
            target: The target IP address
            additional_args: Additional Enum4linux arguments

        Returns:
            SMB enumeration results
        """
        data = {
            "target": target,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Enum4linux: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/enum4linux", data)
        )
        if result.get("success"):
            logger.info(f"✅ Enum4linux completed for {target}")
        else:
            logger.error(f"❌ Enum4linux failed for {target}")
        return result
    
    @mcp.tool()
    async def enum4linux_ng_advanced(target: str, username: str = "", password: str = "",
                               domain: str = "", shares: bool = True, users: bool = True,
                               groups: bool = True, policy: bool = True,
                               additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Enum4linux-ng for advanced SMB enumeration with enhanced logging.

        Args:
            target: The target IP address
            username: Username for authentication
            password: Password for authentication
            domain: Domain for authentication
            shares: Enumerate shares
            users: Enumerate users
            groups: Enumerate groups
            policy: Enumerate policies
            additional_args: Additional Enum4linux-ng arguments

        Returns:
            Advanced SMB enumeration results
        """
        data = {
            "target": target,
            "username": username,
            "password": password,
            "domain": domain,
            "shares": shares,
            "users": users,
            "groups": groups,
            "policy": policy,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Enum4linux-ng: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/enum4linux-ng", data)
        )
        if result.get("success"):
            logger.info(f"✅ Enum4linux-ng completed for {target}")
        else:
            logger.error(f"❌ Enum4linux-ng failed for {target}")
        return result
