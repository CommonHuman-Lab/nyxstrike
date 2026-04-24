import logging
import requests
import time
import threading
from typing import Dict, Any, Optional

import server_core.config_core as config_core

DEFAULT_API_SERVER_URL = config_core.get("DEFAULT_API_SERVER_URL", "http://127.0.0.1:8888")
DEFAULT_REQUEST_TIMEOUT = config_core.get("REQUEST_TIMEOUT", 0)
MAX_RETRIES = config_core.get("MAX_RETRIES", 3)

class ApiClient:
    """Enhanced client for communicating with the API server."""

    def __init__(self, server_url: str, auth_token: str = "", timeout: int = DEFAULT_REQUEST_TIMEOUT, verify_ssl: bool = True):
        self.server_url = server_url.rstrip("/")
        self.timeout = None if timeout is None or int(timeout) <= 0 else int(timeout)
        self.session = requests.Session()
        self._connected = False
        self._connect_lock = threading.Lock()

        if not verify_ssl:
            self.session.verify = False  # Disable SSL verification for self-signed certs

        if auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {auth_token}"
            })

        # Verify connectivity in a background thread so MCP server startup is non-blocking.
        threading.Thread(target=self._verify_connection, daemon=True).start()

    def _verify_connection(self) -> None:
        """Attempt to reach the Flask server; log the outcome but never block callers."""
        for i in range(MAX_RETRIES):
            try:
                logging.debug(f"Retrying connection to {self.server_url} (attempt {i+1}/{MAX_RETRIES})")
                test_response = self.session.get(f"{self.server_url}/ping", timeout=5)
                test_response.raise_for_status()
                with self._connect_lock:
                    self._connected = True
                logging.info(f"✅ Connected to API server at {self.server_url}")
                return
            except requests.exceptions.ConnectionError:
                logging.debug(f"Connection refused on attempt {i+1} to {self.server_url}")
            except Exception as e:
                logging.debug(f"Connection attempt {i+1} failed: {str(e)}")
            if i < MAX_RETRIES - 1:
                time.sleep(2)

        logging.critical("API server offline - tool execution will fail until it's reachable.")

    def safe_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        url = f"{self.server_url}/{endpoint}"
        try:
            logging.debug(f"📡 GET {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.debug(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logging.debug(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def safe_post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.server_url}/{endpoint}"
        try:
            logging.debug(f"📡 POST {url} with data: {json_data}")
            response = self.session.post(url, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.debug(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logging.debug(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def execute_command(self, command: str, use_cache: bool = True) -> Dict[str, Any]:
        return self.safe_post("api/command", {"command": command, "use_cache": use_cache})

    def check_health(self) -> Dict[str, Any]:
        return self.safe_get("health")
