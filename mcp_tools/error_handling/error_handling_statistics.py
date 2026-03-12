# mcp_tools/error_handling/error_handling_statistics.py

from typing import Dict, Any
import asyncio

def register_error_handling_statistics_tool(mcp, hexstrike_client, logger, HexStrikeColors):
    @mcp.tool()
    async def error_handling_statistics() -> Dict[str, Any]:
        """
        Get intelligent error handling system statistics and recent error patterns.

        Returns:
            Error handling statistics and patterns
        """
        logger.info(f"{HexStrikeColors.ELECTRIC_PURPLE}📊 Retrieving error handling statistics{HexStrikeColors.RESET}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: hexstrike_client.safe_get("api/error-handling/statistics")
        )

        if result.get("success"):
            stats = result.get("statistics", {})
            total_errors = stats.get("total_errors", 0)
            recent_errors = stats.get("recent_errors_count", 0)

            logger.info(f"{HexStrikeColors.SUCCESS}✅ Error statistics retrieved{HexStrikeColors.RESET}")
            logger.info(f"  📈 Total Errors: {total_errors}")
            logger.info(f"  🕒 Recent Errors: {recent_errors}")

            # Log error breakdown by type
            error_counts = stats.get("error_counts_by_type", {})
            if error_counts:
                logger.info(f"{HexStrikeColors.HIGHLIGHT_BLUE} ERROR BREAKDOWN {HexStrikeColors.RESET}")
                for error_type, count in error_counts.items():
                                          logger.info(f"  {HexStrikeColors.FIRE_RED}{error_type}: {count}{HexStrikeColors.RESET}")
        else:
            logger.error(f"{HexStrikeColors.ERROR}❌ Failed to retrieve error statistics{HexStrikeColors.RESET}")

        return result
