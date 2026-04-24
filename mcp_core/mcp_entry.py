import sys
import logging
import server_core.config_core as config_core
from mcp_core.server_setup import setup_mcp_server
from mcp_core.api_client import ApiClient

def run_mcp(args, logger):
    """Run the main MCP server logic."""
    # Configure logging based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🔍 Debug logging enabled")

    logger.info("🚀 Starting MCP client")
    logger.info(f"🔗 Connecting to: {args.server}")

    auth_token = args.auth_token if args.auth_token else ""

    try:
        # Initialize the API client
        verify_ssl = True
        if args.disable_ssl_verify:
            verify_ssl = False
            logger.warning("SSL certificate verification is disabled. This is insecure and should only be used for testing.")

        api_client = ApiClient(args.server, auth_token=auth_token, timeout=args.timeout, verify_ssl=verify_ssl)
        # Check server health and log the result
        health = api_client.check_health()
        if "error" not in health:    
            logger.info(f"🏥 Server health status: {health['status']}")
            logger.info(f"📊 Version: {config_core.get('VERSION', 'unknown')}")
            if not health.get("all_essential_tools_available", False):
                logger.warning("Not all essential tools are available on the API server")
                missing_tools = [tool for tool, available in health.get("tools_status", {}).items() if not available]
                if missing_tools:
                    logger.warning(f"Missing tools: {', '.join(missing_tools[:5])}{'...' if len(missing_tools) > 5 else ''}")

        # Set up and run the MCP server
        mcp = setup_mcp_server(api_client, logger, compact=args.compact, profiles=args.profile)
        logger.info("🚀 MCP server ready")

        # stdio fallback for MCP clients that don't support the run() method
        try:
            mcp.run(show_banner=False)
        except AttributeError:
            import asyncio
            if hasattr(mcp, "run_stdio"):
                asyncio.run(mcp.run_stdio_async())
            else:
                raise

    except Exception as e:
        logger.error(f"💥 Error starting MCP server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
