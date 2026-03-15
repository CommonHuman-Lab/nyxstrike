import argparse
from mcp_core.hexstrike_client import DEFAULT_HEXSTRIKE_SERVER, DEFAULT_REQUEST_TIMEOUT

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the HexStrike AI MCP Client")
    parser.add_argument("--server", type=str, default=DEFAULT_HEXSTRIKE_SERVER,
                      help=f"HexStrike AI API server URL (default: {DEFAULT_HEXSTRIKE_SERVER})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_REQUEST_TIMEOUT,
                      help=f"Request timeout in seconds (default: {DEFAULT_REQUEST_TIMEOUT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--compact", action="store_true", help="Compact mode: register only classify_task and run_tool for small LLM clients")
    parser.add_argument("--profile", nargs="+", type=str, default=[], help="Tool profile(s) to load (e.g., web_crawl, exploit_framework, recon or default/full)")
    parser.add_argument("--auth-token", type=str, default="",
                        help="Bearer token for authentication with HexStrike AI server")
    parser.add_argument("--disable-ssl-verify", action="store_true", help="Disable SSL certificate verification when connecting to the HexStrike AI server in front of reverse proxies")
    return parser.parse_args()
