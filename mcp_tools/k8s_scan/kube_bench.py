# mcp_tools/k8s_scan/kube_bench.py

from typing import Dict, Any
import asyncio

def register_kube_bench_tool(mcp, api_client, logger):

    @mcp.tool()
    async def kube_bench_cis(targets: str = "", version: str = "", config_dir: str = "",
                      output_format: str = "json", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute kube-bench for CIS Kubernetes benchmark checks.

        Args:
            targets: Targets to check (master, node, etcd, policies)
            version: Kubernetes version
            config_dir: Configuration directory
            output_format: Output format (json, yaml)
            additional_args: Additional kube-bench arguments

        Returns:
            CIS Kubernetes benchmark results
        """
        data = {
            "targets": targets,
            "version": version,
            "config_dir": config_dir,
            "output_format": output_format,
            "additional_args": additional_args
        }
        logger.info(f"☁️  Starting kube-bench CIS benchmark")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/kube-bench", data)
        )
        if result.get("success"):
            logger.info(f"✅ kube-bench benchmark completed")
        else:
            logger.error(f"❌ kube-bench benchmark failed")
        return result
