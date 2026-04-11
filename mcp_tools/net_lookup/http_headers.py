# mcp_tools/net_lookup/http_headers.py

from typing import Dict, Any
import asyncio


def register_http_headers(mcp, api_client, logger):
    @mcp.tool()
    async def check_http_headers(
        target: str,
        https: bool = False,
        follow_redirects: bool = True,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """
        Fetch HTTP response headers for a target using curl -sI.

        Useful for quickly inspecting security headers (X-Frame-Options,
        Content-Security-Policy, Strict-Transport-Security, etc.) and
        determining server software, redirect chains, and status codes.

        Args:
            target:           Hostname, IP, or URL (scheme is added automatically).
            https:            If True, probe https:// instead of http://.
            follow_redirects: Follow HTTP redirects (default True).
            timeout:          curl --max-time in seconds (default 10).

        Returns:
            Dict with 'output' (raw headers), 'headers' (parsed dict),
            'status_line', and 'target' URL probed.
        """
        logger.info(f"[check_http_headers] target={target!r} https={https}")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: api_client.safe_post(
                "api/tools/http-headers",
                {
                    "target": target,
                    "https": https,
                    "follow_redirects": follow_redirects,
                    "timeout": timeout,
                },
            ),
        )

        if result.get("success"):
            status = result.get("status_line", "")
            hcount = len(result.get("headers", {}))
            logger.info(
                f"[check_http_headers] {target!r} — {status} ({hcount} headers)"
            )
        else:
            logger.error(
                f"[check_http_headers] failed for {target!r}: "
                f"{result.get('error', 'unknown error')}"
            )

        return result
