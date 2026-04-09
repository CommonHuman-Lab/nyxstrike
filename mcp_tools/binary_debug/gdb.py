# mcp_tools/binary_debug/gdb.py

from typing import Dict, Any
import asyncio

def register_gdb_tools(mcp, api_client, logger):
    
    @mcp.tool()
    async def gdb_analyze(binary: str, commands: str = "", script_file: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute GDB for binary analysis and debugging with enhanced logging.

        Args:
            binary: Path to the binary file
            commands: GDB commands to execute
            script_file: Path to GDB script file
            additional_args: Additional GDB arguments

        Returns:
            Binary analysis results
        """
        data = {
            "binary": binary,
            "commands": commands,
            "script_file": script_file,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting GDB analysis: {binary}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/gdb", data)
        )
        if result.get("success"):
            logger.info(f"✅ GDB analysis completed for {binary}")
        else:
            logger.error(f"❌ GDB analysis failed for {binary}")
        return result

    @mcp.tool()
    async def gdb_peda_debug(binary: str = "", commands: str = "", attach_pid: int = 0,
                      core_file: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute GDB with PEDA for enhanced debugging and exploitation.

        Args:
            binary: Binary to debug
            commands: GDB commands to execute
            attach_pid: Process ID to attach to
            core_file: Core dump file to analyze
            additional_args: Additional GDB arguments

        Returns:
            Enhanced debugging results with PEDA
        """
        data = {
            "binary": binary,
            "commands": commands,
            "attach_pid": attach_pid,
            "core_file": core_file,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting GDB-PEDA analysis: {binary or f'PID {attach_pid}' or core_file}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/gdb-peda", data)
        )
        if result.get("success"):
            logger.info(f"✅ GDB-PEDA analysis completed")
        else:
            logger.error(f"❌ GDB-PEDA analysis failed")
        return result