# mcp_tools/db_query/postgresql.py

from typing import Dict, Any
import asyncio

def register_postgresql_tools(mcp, api_client, logger):
    
    @mcp.tool()
    async def postgresql_query(host: str, user: str, password: str = "", database: str = "", query: str = "") -> Dict[str, Any]:
        """
        Query a PostgreSQL database using the API server endpoint.

        Args:
            host: PostgreSQL server address
            user: Username
            password: Password (optional)
            database: Database name
            query: SQL query to execute

        Returns:
            Query results as JSON

        Example:
            postgresql_query(
                host="localhost",
                user="admin",
                password="secret",
                database="mydb",
                query="SELECT * FROM employees;"
            )

        Usage:
            - Use for executing SQL statements on a remote or local PostgreSQL database.
            - Returns JSON with query results or error details.
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
                None, lambda: api_client.safe_post("api/tools/postgresql", data)    
            )
            return result
        except Exception as e:
            logger.error(f"PostgreSQL query failed: {e}")
            return {"error": str(e)}
