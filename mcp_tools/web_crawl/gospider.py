from typing import Dict, Any, List
import asyncio


def register_gospider_tool(mcp, api_client, logger):
    @mcp.tool()
    async def gospider_crawl(
        site: str = "",
        sites: str = "",
        proxy: str = "",
        output: str = "",
        user_agent: str = "web",
        cookie: str = "",
        headers: List[str] = [],
        burp: str = "",
        blacklist: str = "",
        threads: int = 1,
        concurrent: int = 5,
        depth: int = 1,
        delay: int = 0,
        random_delay: int = 0,
        timeout: int = 10,
        sitemap: bool = False,
        robots: bool = True,
        other_source: bool = False,
        include_subs: bool = False,
        include_other_source: bool = False,
        debug: bool = False,
        verbose: bool = False,
        no_redirect: bool = False,
        version: bool = False,
        additional_args: str = "",
    ) -> Dict[str, Any]:
        """
        Execute GoSpider web crawler.

        Args:
            site: Single site to crawl
            sites: File path containing sites to crawl
            proxy: HTTP proxy URL
            output: Output folder path
            user_agent: web, mobi, or custom UA string
            cookie: Cookie string
            headers: Repeated request headers
            burp: Burp raw HTTP request file
            blacklist: URL blacklist regex
            threads: Number of site threads
            concurrent: Max concurrent requests per matching domain
            depth: Max crawl depth (0 = infinite)
            delay: Fixed delay between requests in seconds
            random_delay: Extra randomized delay in seconds
            timeout: Request timeout in seconds
            sitemap: Crawl sitemap.xml
            robots: Crawl robots.txt
            other_source: Include 3rd-party URL sources
            include_subs: Include subdomains from 3rd-party sources
            include_other_source: Include and crawl other-source URLs
            debug: Enable debug mode
            verbose: Enable verbose output
            no_redirect: Disable redirects
            version: Show version and exit
            additional_args: Additional GoSpider arguments

        Returns:
            GoSpider execution results
        """
        data: Dict[str, Any] = {
            "site": site,
            "sites": sites,
            "proxy": proxy,
            "output": output,
            "user_agent": user_agent,
            "cookie": cookie,
            "headers": headers,
            "burp": burp,
            "blacklist": blacklist,
            "threads": threads,
            "concurrent": concurrent,
            "depth": depth,
            "delay": delay,
            "random_delay": random_delay,
            "timeout": timeout,
            "sitemap": sitemap,
            "robots": robots,
            "other_source": other_source,
            "include_subs": include_subs,
            "include_other_source": include_other_source,
            "debug": debug,
            "verbose": verbose,
            "no_redirect": no_redirect,
            "version": version,
            "additional_args": additional_args,
        }
        logger.info("🕷️ Starting GoSpider crawling")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/gospider", data)
        )
        if result.get("success"):
            logger.info("✅ GoSpider crawling completed")
        else:
            logger.error("❌ GoSpider crawling failed")
        return result
