# mcp_tools/db_query/sqlite.py

from typing import Any, Dict
import asyncio

def register_sqlite_tools(mcp, api_client, logger):
    @mcp.tool()
    async def sqlite_query(db_path: str, query: str) -> Dict[str, Any]:
        """
        Query a SQLite database using the API server endpoint.

        Args:
            db_path: Path to the SQLite database file
            query: SQL query to execute

        Returns:
            Query results as JSON

        Example:
            sqlite_query(
                db_path="/path/to/database.db",
                query="SELECT * FROM users;"
            )

        Usage:
            - Use for executing SELECT, INSERT, UPDATE, or DELETE statements on a local SQLite database file.
            - Returns JSON with query results or error details.
        """
        data = {
            "db_path": db_path,
            "query": query
        }
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, lambda: api_client.safe_post("api/tools/sqlite", data)
            )
            return result
        except Exception as e:
            logger.error(f"SQLite query failed: {e}")
            return {"error": str(e)}
    