# mcp_tools/python_env.py

from typing import Any, Dict
import asyncio

def register_python_env_tools(mcp, api_client, logger):
    @mcp.tool()
    async def install_python_package(package: str, env_name: str = "default") -> Dict[str, Any]:
        """
        Install a Python package in a virtual environment on the API server.

        Args:
            package: Name of the Python package to install
            env_name: Name of the virtual environment

        Returns:
            Package installation results
        """
        data = {
            "package": package,
            "env_name": env_name
        }
        logger.info(f"📦 Installing Python package: {package} in env {env_name}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/python/install", data)
        )
        if result.get("success"):
            logger.info(f"✅ Package {package} installed successfully")
        else:
            logger.error(f"❌ Failed to install package {package}")
        return result

    @mcp.tool()
    async def execute_python_script(script: str, env_name: str = "default", filename: str = "") -> Dict[str, Any]:
        """
        Execute a Python script in a virtual environment on the API server.

        Args:
            script: Python script content to execute
            env_name: Name of the virtual environment
            filename: Custom script filename (auto-generated if empty)

        Returns:
            Script execution results
        """
        data = {
            "script": script,
            "env_name": env_name
        }
        if filename:
            data["filename"] = filename

        logger.info(f"🐍 Executing Python script in env {env_name}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/python/execute", data)
        )
        if result.get("success"):
            logger.info(f"✅ Python script executed successfully")
        else:
            logger.error(f"❌ Python script execution failed")
        return result
