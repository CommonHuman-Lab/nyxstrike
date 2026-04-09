# mcp_tools/error_handling/test_error_recovery.py

from typing import Dict, Any
import asyncio

def register_test_error_recovery_tool(mcp, api_client, logger, CliColors):

    @mcp.tool()
    async def test_error_recovery(tool_name: str, error_type: str = "timeout",
                           target: str = "example.com") -> Dict[str, Any]:
        """
        Test the intelligent error recovery system with simulated failures.

        Args:
            tool_name: Name of tool to simulate error for
            error_type: Type of error to simulate (timeout, permission_denied, network_unreachable, etc.)
            target: Target for the simulated test

        Returns:
            Recovery strategy and system response
        """
        data_payload = {
            "tool_name": tool_name,
            "error_type": error_type,
            "target": target
        }

        logger.info(f"{CliColors.RUBY}🧪 Testing error recovery for {tool_name} with {error_type}{CliColors.RESET}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/error-handling/test-recovery", data_payload)
        )

        if result.get("success"):
            recovery_strategy = result.get("recovery_strategy", {})
            action = recovery_strategy.get("action", "unknown")
            success_prob = recovery_strategy.get("success_probability", 0)

            logger.info(f"{CliColors.SUCCESS}✅ Error recovery test completed{CliColors.RESET}")
            logger.info(f"  🔧 Recovery Action: {action}")
            logger.info(f"  📊 Success Probability: {success_prob:.2%}")

            # Log alternative tools if available
            alternatives = result.get("alternative_tools", [])
            if alternatives:
                logger.info(f"  🔄 Alternative Tools: {', '.join(alternatives)}")
        else:
            logger.error(f"{CliColors.ERROR}❌ Error recovery test failed{CliColors.RESET}")

        return result
