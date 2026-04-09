# mcp_tools/container_scan/docker_bench.py

from typing import Dict, Any
import asyncio

def register_docker_bench_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def docker_bench_security_scan(checks: str = "", exclude: str = "",
                                  output_file: str = "/tmp/docker-bench-results.json",
                                  additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Docker Bench for Security for Docker security assessment.

        Args:
            checks: Specific checks to run
            exclude: Checks to exclude
            output_file: Output file path
            additional_args: Additional Docker Bench arguments

        Returns:
            Docker security assessment results
        """
        data = {
            "checks": checks,
            "exclude": exclude,
            "output_file": output_file,
            "additional_args": additional_args
        }
        logger.info(f"🐳 Starting Docker Bench Security assessment")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/docker-bench-security", data)
        )
        if result.get("success"):
            logger.info(f"✅ Docker Bench Security completed")
        else:
            logger.error(f"❌ Docker Bench Security failed")
        return result
