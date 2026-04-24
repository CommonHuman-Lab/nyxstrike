from typing import Dict, Any, List
import asyncio


def register_shuffledns_tool(mcp, api_client, logger):
    @mcp.tool()
    async def shuffledns_scan(
        domain: str = "",
        domains: List[str] = [],
        auto_domain: bool = False,
        list_file: str = "",
        wordlist: str = "",
        resolver: str = "",
        trusted_resolver: str = "",
        raw_input: str = "",
        mode: str = "",
        threads: int = 10000,
        output: str = "",
        json_output: bool = False,
        wildcard_output: str = "",
        massdns: str = "",
        massdns_cmd: str = "",
        directory: str = "",
        retries: int = 5,
        strict_wildcard: bool = False,
        wildcard_threads: int = 250,
        silent: bool = False,
        version: bool = False,
        verbose: bool = False,
        no_color: bool = False,
        update: bool = False,
        disable_update_check: bool = False,
        additional_args: str = "",
    ) -> Dict[str, Any]:
        """
        Execute shuffleDNS for subdomain bruteforce/resolve/filter with wildcard handling.

        Args:
            domain: Single domain target
            domains: Multiple domain targets
            auto_domain: Automatically extract root domains
            list_file: File containing subdomains to resolve
            wordlist: Wordlist file for bruteforce mode
            resolver: Resolver list file
            trusted_resolver: Trusted resolver list file
            raw_input: Raw massdns output input file
            mode: Execution mode (bruteforce, resolve, filter)
            threads: Concurrent massdns resolves
            output: Output file path
            json_output: Output as ndjson
            wildcard_output: Wildcard IP output file
            massdns: Path to massdns binary
            massdns_cmd: Extra massdns commands
            directory: Temporary directory for enumeration
            retries: Number of retries for DNS enumeration
            strict_wildcard: Perform wildcard checks on all found subdomains
            wildcard_threads: Concurrent wildcard checks
            silent: Show only subdomains
            version: Show shuffledns version
            verbose: Show verbose output
            no_color: Disable color output
            update: Update shuffledns binary
            disable_update_check: Disable auto update check
            additional_args: Additional shuffledns arguments

        Returns:
            shuffleDNS execution results
        """
        data: Dict[str, Any] = {
            "domain": domain,
            "domains": domains,
            "auto_domain": auto_domain,
            "list": list_file,
            "wordlist": wordlist,
            "resolver": resolver,
            "trusted_resolver": trusted_resolver,
            "raw_input": raw_input,
            "mode": mode,
            "threads": threads,
            "output": output,
            "json": json_output,
            "wildcard_output": wildcard_output,
            "massdns": massdns,
            "massdns_cmd": massdns_cmd,
            "directory": directory,
            "retries": retries,
            "strict_wildcard": strict_wildcard,
            "wildcard_threads": wildcard_threads,
            "silent": silent,
            "version": version,
            "verbose": verbose,
            "no_color": no_color,
            "update": update,
            "disable_update_check": disable_update_check,
            "additional_args": additional_args,
        }

        logger.info("🔍 Starting shuffleDNS scan")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/shuffledns", data)
        )
        if result.get("success"):
            logger.info("✅ shuffleDNS completed")
        else:
            logger.error("❌ shuffleDNS failed")
        return result
