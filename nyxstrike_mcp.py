#!/usr/bin/env python3
"""
NyxStrike MCP Client - Enhanced AI Agent Communication Interface

Enhanced with AI-Powered Intelligence & Automation
🚀 Bug Bounty | CTF | Red Team | Security Research

Architecture: MCP Client for AI agent communication with NyxStrike server
Framework: FastMCP integration for tool orchestration
"""

import sys
import logging
from shared.colored_formatter import ColoredFormatter
from mcp_core.mcp_entry import run_mcp
from mcp_core.args import parse_args

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

# Suppress low-level MCP protocol noise (e.g. "Processing request of type ...")
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
# Suppress FastMCP's own "Starting MCP server" banner (redundant with our own startup logs)
logging.getLogger("fastmcp").setLevel(logging.WARNING)

# Apply colored formatter
for handler in logging.getLogger().handlers:
    fmt = ColoredFormatter(
        "[%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fmt._stream = getattr(handler, 'stream', None)
    handler.setFormatter(fmt)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the MCP server."""
    args = parse_args()
    run_mcp(args, logger)

if __name__ == "__main__":
    main()