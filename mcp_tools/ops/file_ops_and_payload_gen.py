# mcp_tools/file_ops_and_payload_gen.py

from typing import Dict, Any
import asyncio

def register_file_ops_and_payload_gen_tools(mcp, api_client, logger):
    @mcp.tool()
    async def create_file(filename: str, content: str, binary: bool = False) -> Dict[str, Any]:
        """
        Create a file with specified content on the API server.

        Args:
            filename: Name of the file to create
            content: Content to write to the file
            binary: Whether the content is binary data

        Returns:
            File creation results
        """
        data = {
            "filename": filename,
            "content": content,
            "binary": binary
        }
        logger.info(f"📄 Creating file: {filename}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/files/create", data)
        )
        if result.get("success"):
            logger.info(f"✅ File created successfully: {filename}")
        else:
            logger.error(f"❌ Failed to create file: {filename}")
        return result

    @mcp.tool()
    async def modify_file(filename: str, content: str, append: bool = False) -> Dict[str, Any]:
        """
        Modify an existing file on the API server.

        Args:
            filename: Name of the file to modify
            content: Content to write or append
            append: Whether to append to the file (True) or overwrite (False)

        Returns:
            File modification results
        """
        data = {
            "filename": filename,
            "content": content,
            "append": append
        }
        logger.info(f"✏️  Modifying file: {filename}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/files/modify", data)
        )
        if result.get("success"):
            logger.info(f"✅ File modified successfully: {filename}")
        else:
            logger.error(f"❌ Failed to modify file: {filename}")
        return result

    @mcp.tool()
    async def delete_file(filename: str) -> Dict[str, Any]:
        """
        Delete a file or directory on the API server.

        Args:
            filename: Name of the file or directory to delete

        Returns:
            File deletion results
        """
        data = {
            "filename": filename
        }
        logger.info(f"🗑️  Deleting file: {filename}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/files/delete", data)
        )
        if result.get("success"):
            logger.info(f"✅ File deleted successfully: {filename}")
        else:
            logger.error(f"❌ Failed to delete file: {filename}")
        return result

    @mcp.tool()
    async def list_files(directory: str = ".") -> Dict[str, Any]:
        """
        List files in a directory on the API server.

        Args:
            directory: Directory to list (relative to server's base directory)

        Returns:
            Directory listing results
        """
        logger.info(f"📂 Listing files in directory: {directory}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get("api/files/list", {"directory": directory})
        )
        if result.get("success"):
            file_count = len(result.get("files", []))
            logger.info(f"✅ Listed {file_count} files in {directory}")
        else:
            logger.error(f"❌ Failed to list files in {directory}")
        return result

    @mcp.tool()
    async def generate_payload(payload_type: str = "buffer", size: int = 1024, pattern: str = "A", filename: str = "") -> Dict[str, Any]:
        """
        Generate large payloads for testing and exploitation.

        Args:
            payload_type: Type of payload (buffer, cyclic, random)
            size: Size of the payload in bytes
            pattern: Pattern to use for buffer payloads
            filename: Custom filename (auto-generated if empty)

        Returns:
            Payload generation results
        """
        data = {
            "type": payload_type,
            "size": size,
            "pattern": pattern
        }
        if filename:
            data["filename"] = filename

        logger.info(f"🎯 Generating {payload_type} payload: {size} bytes")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/payloads/generate", data)
        )
        if result.get("success"):
            logger.info(f"✅ Payload generated successfully")
        else:
            logger.error(f"❌ Failed to generate payload")
        return result
