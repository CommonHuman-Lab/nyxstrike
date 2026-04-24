# mcp_tools/gateway.py

from typing import Dict, Any
import json
import asyncio

def register_gateway_tools(mcp, api_client):
    @mcp.tool()
    async def classify_task(description: str) -> Dict[str, Any]:
        """
        Classify a security task and return recommended tools.
        Call this FIRST before running security tools to discover which ones are relevant.

        Args:
            description: What you want to do (e.g., "scan for open ports", "test for SQL injection")

        Returns:
            Task category, recommended tools with parameters, and usage instructions
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/classify-task", {"description": description})
        )
        if result.get("success"):
            result["usage"] = "Use run_tool with a tool name and params from the recommended list"
        return result

    @mcp.tool()
    async def run_tool(
        tool_name: str,
        params: str,
    ) -> Dict[str, Any]:
        """
        Execute any security tool by name with parameters.
        Use classify_task first to discover available tools.

        Args:
            tool_name: Tool name from classify_task results (e.g., "nmap", "nuclei")
            params: JSON string of parameters (e.g., '{"target": "10.0.0.1"}')

        Returns:
            Tool execution results
        """
        from tool_registry import get_tool
        tool_def = get_tool(tool_name)
        if not tool_def:
            return {"error": f"Unknown tool: {tool_name}", "success": False}

        try:
            parsed_params = json.loads(params) if isinstance(params, str) else params
        except json.JSONDecodeError as e:
            return {"error": f"Invalid params JSON: {e}", "success": False}

        # Validate required params
        for pname, spec in tool_def["params"].items():
            if spec.get("required") and pname not in parsed_params:
                return {"error": f"Missing required param: {pname}", "success": False}

        # Fill defaults for optional params
        for k, v in tool_def.get("optional", {}).items():
            if k not in parsed_params:
                parsed_params[k] = v

        endpoint = tool_def["endpoint"].lstrip("/")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post(endpoint, parsed_params)
        )

        return result
