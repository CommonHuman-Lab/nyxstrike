# mcp_tools/param_discovery/paramspider.py

from typing import Dict, Any
import asyncio

def register_paramspider_tool(mcp, api_client, logger):
    @mcp.tool()
    async def paramspider_mining(domain: str, level: int = 2,
                          exclude: str = "png,jpg,gif,jpeg,swf,woff,svg,pdf,css,ico",
                          output: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute ParamSpider for parameter mining from web archives with enhanced logging.

        Args:
            domain: The target domain
            level: Mining level depth
            exclude: File extensions to exclude
            output: Output file path
            additional_args: Additional ParamSpider arguments

        Returns:
            Parameter mining results from web archives
        """
        data = {
            "domain": domain,
            "level": level,
            "exclude": exclude,
            "output": output,
            "additional_args": additional_args
        }
        logger.info(f"🕷️  Starting ParamSpider mining: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/paramspider", data)
        )
        if result.get("success"):
            logger.info(f"✅ ParamSpider mining completed for {domain}")
        else:
            logger.error(f"❌ ParamSpider mining failed for {domain}")
        return result
    
    @mcp.tool()
    async def paramspider_discovery(domain: str, exclude: str = "", output_file: str = "", level: int = 2, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute ParamSpider for parameter discovery with enhanced logging.

        Args:
            domain: Target domain
            exclude: Extensions to exclude
            output_file: Output file path
            level: Crawling level
            additional_args: Additional ParamSpider arguments

        Returns:
            Parameter discovery results
        """
        data = {
            "domain": domain,
            "exclude": exclude,
            "output_file": output_file,
            "level": level,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting ParamSpider discovery: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/paramspider", data)
        )
        if result.get("success"):
            logger.info(f"✅ ParamSpider discovery completed")
        else:
            logger.error(f"❌ ParamSpider discovery failed")
        return result