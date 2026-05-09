import asyncio
from typing import Any, Dict


def register(mcp, api_client, logger):

  @mcp.tool()
  async def nyxstrike_h2csmuggler(
    proxy: str,
    target_url: str = "",
    scan_list: str = "",
    threads: int = 5,
    request: str = "GET",
    data: str = "",
    headers: str = "",
    wordlist: str = "",
    max_time: float = 10,
    upgrade_only: bool = False,
    test: bool = False,
    verbose: bool = False,
    additional_args: str = "",
  ) -> Dict[str, Any]:
    """
    Detect and exploit insecure forwarding of h2c upgrades.

    Args:
      proxy: Proxy URL to try to bypass (required)
      target_url: Smuggled target URL in exploit mode
      scan_list: File path containing URLs for scan mode
      threads: Thread count for scan mode
      request: Smuggled HTTP method
      data: Smuggled request body
      headers: Semicolon-delimited smuggled headers
      wordlist: Optional path list for smuggled path brute-force
      max_time: Socket timeout in seconds
      upgrade_only: Drop HTTP2-Settings from Connection header
      test: Test only mode
      verbose: Enable verbose output
      additional_args: Extra raw CLI args

    Returns:
      h2csmuggler execution results
    """
    payload = {
      "proxy": proxy,
      "target_url": target_url,
      "scan_list": scan_list,
      "threads": threads,
      "request": request,
      "data": data,
      "headers": headers,
      "wordlist": wordlist,
      "max_time": max_time,
      "upgrade_only": upgrade_only,
      "test": test,
      "verbose": verbose,
      "additional_args": additional_args,
    }

    try:
      loop = asyncio.get_running_loop()
      result = await loop.run_in_executor(
        None,
        lambda: api_client.safe_post("api/plugins/h2csmuggler", payload),
      )
      return result
    except Exception as exc:
      logger.error("nyxstrike_h2csmuggler failed: %s", exc)
      return {"success": False, "error": str(exc)}
