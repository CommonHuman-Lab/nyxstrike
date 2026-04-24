import asyncio
# mcp_tools/wordlist.py

def register_wordlist_tools(mcp, api_client):
    @mcp.tool()
    async def wordlist_get(wordlist_id: str) -> dict:
        """
        Retrieve a specific wordlist entry by its ID.

        Args:
            wordlist_id (str): The unique identifier of the wordlist.

        Returns:
            dict: Wordlist information if found, or error message with 404 status.
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get(f"api/wordlists/{wordlist_id}")
        )
        return result

    @mcp.tool()
    async def wordlist_get_all() -> dict:
        """
        Retrieve all wordlist entries.

        Returns:
            dict: JSON array containing all wordlist entries.
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get("api/wordlists")
        )
        return result

    @mcp.tool()
    async def wordlist_get_path(wordlist_id: str) -> dict:
        """
        Retrieve the file path for a specific wordlist by its ID.

        Args:
            wordlist_id (str): The unique identifier of the wordlist.

        Returns:
            dict: File path if found, or error message with 404 status.
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_get(f"api/wordlists/{wordlist_id}/path")
        )
        return result

    @mcp.tool()
    async def wordlist_find_best(criteria: dict) -> dict:
        """
        Find the best matching wordlist based on provided criteria.

        Args:
            criteria (dict): Search criteria for the wordlist.
                Common fields:
                    type (str): Type of wordlist (e.g., 'password', 'directory').
                    speed (str): Speed category ('fast', 'medium', 'slow').
                    tool (str or list): Tool(s) that use the wordlist.
                    language (str): Language of the wordlist.
                    coverage (str): Coverage type ('broad', 'focused', etc.).
                    format (str): File format (e.g., 'txt', 'lst').
                At least one field should be provided.

        Returns:
            dict: Best matching wordlist entry if found, or an error message with 404 status.
                Example success:
                    {
                        "success": True,
                        "wordlist": {
                            "id": "rockyou",
                            "path": "/usr/share/wordlists/rockyou.txt",
                            "type": "password",
                            ...
                        }
                    }
                Example error:
                    {
                        "success": False,
                        "error": "No matching wordlist found"
                    }

        Example:
            wordlist_find_best({
                "type": "password",
                "speed": "fast"
            })
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/wordlists/bestmatch", criteria)
        )
        return result

    @mcp.tool()
    async def wordlist_save(wordlist_id: str, wordlist_info: dict) -> dict:
        """
        Save or update a wordlist entry.

        Args:
            wordlist_id (str): Unique identifier for the wordlist.
            wordlist_info (dict): Metadata about the wordlist.
                Required fields:
                    path (str): Absolute path to the wordlist file.
                    type (str): Type of wordlist (e.g., 'password', 'directory').
                    recommended_for (list of str): Recommended use cases.
                Optional fields:
                    description (str): Description of the wordlist.
                    size (int): Number of entries in the wordlist.
                    tool (list of str): Tools that use this wordlist.
                    speed (str): Speed category ('fast', 'medium', 'slow').
                    language (str): Language of the wordlist.
                    coverage (str): Coverage type ('broad', 'focused', etc.).
                    format (str): File format (e.g., 'txt', 'lst').

        Returns:
            Status message indicating success or failure.

        Example:
            wordlist_save(
                "rockyou",
                {
                    "path": "/usr/share/wordlists/rockyou.txt",
                    "type": "password",
                    "recommended_for": ["password cracking"],
                    "description": "Common passwords",
                    "size": 14344392,
                    "tool": ["john", "hydra"],
                    "speed": "medium",
                    "language": "en",
                    "coverage": "broad",
                    "format": "txt"
                }
            )
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post(f"api/wordlists/{wordlist_id}", wordlist_info)
        )
        return result

    @mcp.tool()
    async def wordlist_delete(wordlist_id: str) -> dict:
        """
        Delete a specific wordlist entry by its ID.

        Args:
            wordlist_id (str): The unique identifier of the wordlist.

        Returns:
            dict: Status message indicating success or failure.
        """
        import requests
        url = f"{api_client.server_url}/api/wordlists/{wordlist_id}"
        try:
            response = api_client.session.delete(url, timeout=api_client.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}