# mcp_tools/visual_output_tools.py

from typing import Dict, Any
import asyncio

def register_visual_output_tools(mcp, api_client, logger):
    @mcp.tool()
    async def get_live_dashboard() -> Dict[str, Any]:
        """
        Get a beautiful live dashboard showing all active processes with enhanced visual formatting.

        Returns:
            Live dashboard with visual process monitoring and system metrics
        """
        logger.info("📊 Fetching live process dashboard")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get("api/processes/dashboard")
        )
        if result.get("success", True):
            logger.info("✅ Live dashboard retrieved successfully")
        else:
            logger.error("❌ Failed to retrieve live dashboard")
        return result

    @mcp.tool()
    async def create_vulnerability_report(vulnerabilities: str, target: str = "", scan_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Create a beautiful vulnerability report with severity-based styling and visual indicators.

        Args:
            vulnerabilities: JSON string containing vulnerability data
            target: Target that was scanned
            scan_type: Type of scan performed

        Returns:
            Formatted vulnerability report with visual enhancements
        """
        import json

        try:
            # Parse vulnerabilities if provided as JSON string
            if isinstance(vulnerabilities, str):
                vuln_data = json.loads(vulnerabilities)
            else:
                vuln_data = vulnerabilities

            logger.info(f"📋 Creating vulnerability report for {len(vuln_data)} findings")

            # Create individual vulnerability cards
            vulnerability_cards = []
            for vuln in vuln_data:
                loop = asyncio.get_running_loop()
                card_result = await loop.run_in_executor(
                    None, lambda: api_client.safe_post("api/visual/vulnerability-card", vuln)
                )
                if card_result.get("success"):
                    vulnerability_cards.append(card_result.get("vulnerability_card", ""))

            # Create summary report
            summary_data = {
                "target": target,
                "vulnerabilities": vuln_data,
                "tools_used": [scan_type],
                "execution_time": 0
            }

            loop = asyncio.get_running_loop()
            summary_result = await loop.run_in_executor(
                None, lambda: api_client.safe_post("api/visual/summary-report", summary_data)
            )

            logger.info("✅ Vulnerability report created successfully")
            return {
                "success": True,
                "vulnerability_cards": vulnerability_cards,
                "summary_report": summary_result.get("summary_report", ""),
                "total_vulnerabilities": len(vuln_data),
                "timestamp": summary_result.get("timestamp", "")
            }

        except Exception as e:
            logger.error(f"❌ Failed to create vulnerability report: {str(e)}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def format_tool_output_visual(tool_name: str, output: str, success: bool = True) -> Dict[str, Any]:
        """
        Format tool output with beautiful visual styling, syntax highlighting, and structure.

        Args:
            tool_name: Name of the security tool
            output: Raw output from the tool
            success: Whether the tool execution was successful

        Returns:
            Beautifully formatted tool output with visual enhancements
        """
        logger.info(f"🎨 Formatting output for {tool_name}")

        data = {
            "tool": tool_name,
            "output": output,
            "success": success
        }

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/visual/tool-output", data)
        )
        if result.get("success"):
            logger.info(f"✅ Tool output formatted successfully for {tool_name}")
        else:
            logger.error(f"❌ Failed to format tool output for {tool_name}")

        return result

    @mcp.tool()
    async def create_scan_summary(target: str, tools_used: str, vulnerabilities_found: int = 0,
                           execution_time: float = 0.0, findings: str = "") -> Dict[str, Any]:
        """
        Create a comprehensive scan summary report with beautiful visual formatting.

        Args:
            target: Target that was scanned
            tools_used: Comma-separated list of tools used
            vulnerabilities_found: Number of vulnerabilities discovered
            execution_time: Total execution time in seconds
            findings: Additional findings or notes

        Returns:
            Beautiful scan summary report with visual enhancements
        """
        logger.info(f"📊 Creating scan summary for {target}")

        tools_list = [tool.strip() for tool in tools_used.split(",")]

        summary_data = {
            "target": target,
            "tools_used": tools_list,
            "execution_time": execution_time,
            "vulnerabilities": [{"severity": "info"}] * vulnerabilities_found,  # Mock data for count
            "findings": findings
        }

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/visual/summary-report", summary_data)
        )
        if result.get("success"):
            logger.info("✅ Scan summary created successfully")
        else:
            logger.error("❌ Failed to create scan summary")

        return result

    @mcp.tool()
    async def display_system_metrics() -> Dict[str, Any]:
        """
        Display current system metrics and performance indicators with visual formatting.

        Returns:
            System metrics with beautiful visual presentation
        """
        logger.info("📈 Fetching system metrics")

        # Get telemetry data
        loop = asyncio.get_running_loop()
        telemetry_result = await loop.run_in_executor(
            None, lambda: api_client.safe_get("api/telemetry")
        )

        if telemetry_result.get("success", True):
            logger.info("✅ System metrics retrieved successfully")

            # Format the metrics for better display
            metrics = telemetry_result.get("system_metrics", {})
            stats = {
                "cpu_percent": metrics.get("cpu_percent", 0),
                "memory_percent": metrics.get("memory_percent", 0),
                "disk_usage": metrics.get("disk_usage", 0),
                "uptime_seconds": telemetry_result.get("uptime_seconds", 0),
                "commands_executed": telemetry_result.get("commands_executed", 0),
                "success_rate": telemetry_result.get("success_rate", "0%")
            }

            return {
                "success": True,
                "metrics": stats,
                "formatted_display": f"""
🖥️  System Performance Metrics:
├─ CPU Usage: {stats['cpu_percent']:.1f}%
├─ Memory Usage: {stats['memory_percent']:.1f}%
├─ Disk Usage: {stats['disk_usage']:.1f}%
├─ Uptime: {stats['uptime_seconds']:.0f}s
├─ Commands Executed: {stats['commands_executed']}
└─ Success Rate: {stats['success_rate']}
""",
                "timestamp": telemetry_result.get("timestamp", "")
            }
        else:
            logger.error("❌ Failed to retrieve system metrics")
            return telemetry_result
