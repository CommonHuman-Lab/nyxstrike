# mcp_tools/db_query/mysql.py

from typing import Any, Dict
import asyncio

def register_mysql_tools(mcp, api_client, logger):
    @mcp.tool()
    async def mysql_query(
        host: str,
        user: str,
        password: str = "",
        database: str = "",
        query: str = ""
    ) -> Dict[str, Any]:
        """
        Query a MySQL database using the API server endpoint.

        Args:
            host: MySQL server address
            user: Username
            password: Password (optional)
            database: Database name
            query: SQL query

        Returns:
            Query results as JSON
        """
        data = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "query": query
        }
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, lambda: api_client.safe_post("api/tools/mysql", data)
            )
            return result
        except Exception as e:
            logger.error(f"MySQL query failed: {e}")
            return {"error": str(e)}