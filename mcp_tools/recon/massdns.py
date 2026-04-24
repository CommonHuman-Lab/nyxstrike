from typing import Dict, Any
import asyncio


def register_massdns_tool(mcp, api_client, logger):
    @mcp.tool()
    async def massdns_scan(
        domainlist: str,
        bindto: str = "",
        busy_poll: bool = False,
        resolve_count: int = 50,
        drop_group: str = "",
        drop_user: str = "",
        extended_input: bool = False,
        filter_code: str = "",
        flush: bool = False,
        ignore_code: str = "",
        interval: int = 500,
        error_log: str = "",
        norecurse: bool = False,
        output: str = "",
        predictable: bool = False,
        processes: int = 1,
        quiet: bool = False,
        rand_src_ipv6: str = "",
        rcvbuf: int = 0,
        retry: str = "",
        resolvers: str = "",
        root: bool = False,
        hashmap_size: int = 10000,
        sndbuf: int = 0,
        status_format: str = "",
        sticky: bool = False,
        socket_count: int = 1,
        record_type: str = "A",
        verify_ip: bool = False,
        outfile: str = "",
        additional_args: str = "",
    ) -> Dict[str, Any]:
        """
        Execute massdns with full CLI flag support.

        Args:
            domainlist: Path to file containing names to resolve
            bindto: Bind address and port (IP:PORT)
            busy_poll: Use busy-wait polling
            resolve_count: Number of resolves before giving up
            drop_group: Group to drop privileges to
            drop_user: User to drop privileges to
            extended_input: Input names include resolver list
            filter_code: Output only specified response code
            flush: Flush output file on each response
            ignore_code: Exclude specified response code
            interval: Interval in ms between resolves of same domain
            error_log: Error log path
            norecurse: Use non-recursive queries
            output: Output format flags (L,S,F,B,J)
            predictable: Use resolvers incrementally
            processes: Number of resolver processes
            quiet: Quiet mode
            rand_src_ipv6: Random IPv6 source subnet
            rcvbuf: Receive buffer size in bytes
            retry: Unacceptable DNS response codes
            resolvers: Resolver file path
            root: Do not drop privileges when running as root
            hashmap_size: Number of concurrent lookups
            sndbuf: Send buffer size in bytes
            status_format: Real-time status format (json, ansi)
            sticky: Keep resolver on retry
            socket_count: Socket count per process
            record_type: DNS record type (A, AAAA, CNAME, etc.)
            verify_ip: Verify IP addresses in incoming replies
            outfile: Output file path
            additional_args: Additional massdns flags

        Returns:
            massdns execution results
        """
        data: Dict[str, Any] = {
            "domainlist": domainlist,
            "bindto": bindto,
            "busy_poll": busy_poll,
            "resolve_count": resolve_count,
            "drop_group": drop_group,
            "drop_user": drop_user,
            "extended_input": extended_input,
            "filter": filter_code,
            "flush": flush,
            "ignore": ignore_code,
            "interval": interval,
            "error_log": error_log,
            "norecurse": norecurse,
            "output": output,
            "predictable": predictable,
            "processes": processes,
            "quiet": quiet,
            "rand_src_ipv6": rand_src_ipv6,
            "rcvbuf": rcvbuf,
            "retry": retry,
            "resolvers": resolvers,
            "root": root,
            "hashmap_size": hashmap_size,
            "sndbuf": sndbuf,
            "status_format": status_format,
            "sticky": sticky,
            "socket_count": socket_count,
            "record_type": record_type,
            "verify_ip": verify_ip,
            "outfile": outfile,
            "additional_args": additional_args,
        }

        logger.info("🔍 Starting massdns scan")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/massdns", data)
        )
        if result.get("success"):
            logger.info("✅ massdns completed")
        else:
            logger.error("❌ massdns failed")
        return result
