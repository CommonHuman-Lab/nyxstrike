# mcp_tools/net_lookup/dig.py

from typing import Any, Dict, List
import asyncio


def register_dig(mcp, api_client, logger):
    @mcp.tool()
    async def dig_dns(
        target: str,
        record_types: List[str] = ["A", "MX", "NS", "TXT"],
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """
        DNS record lookup using dig +short.

        Queries A, MX, NS, and TXT records for the target domain.
        Useful for mapping subdomains, mail servers, name servers,
        and SPF/DKIM/DMARC policy records.

        Args:
            target:       Domain name to query (e.g. "example.com").
            record_types: List of record types to query. Allowed values:
                          "A", "MX", "NS", "TXT". Defaults to all four.
            timeout:      Per-query timeout in seconds (default 15).

        Returns:
            Dict with 'records' (dict per type), 'output' (formatted
            multi-section string), and 'target'.
        """
        logger.info(f"[dig_dns] target={target!r} types={record_types}")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: api_client.safe_post(
                "api/tools/dig",
                {
                    "target": target,
                    "record_types": record_types,
                    "timeout": timeout,
                },
            ),
        )

        if result.get("success"):
            records = result.get("records", {})
            for rtype, val in records.items():
                preview = val[:80].replace("\n", " ") if val else "(empty)"
                logger.info(f"[dig_dns] {rtype}: {preview}")
        else:
            logger.error(
                f"[dig_dns] failed for {target!r}: "
                f"{result.get('error', 'unknown error')}"
            )

        return result
