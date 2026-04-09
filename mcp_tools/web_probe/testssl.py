# mcp_tools/web_probe/testssl.py

from typing import Dict, Any
import asyncio


def register_testssl_tool(mcp, api_client, logger):
    @mcp.tool()
    async def testssl_analyze(
        target: str = "",
        help_mode: bool = False,
        banner: bool = False,
        version: bool = False,
        local_mode: bool = False,
        local_pattern: str = "",
        starttls: str = "",
        xmpphost: str = "",
        mx: str = "",
        file_input: str = "",
        mode: str = "serial",
        warnings: str = "",
        socket_timeout: int = 0,
        openssl_timeout: int = 0,
        each_cipher: bool = False,
        cipher_per_proto: bool = False,
        categories: bool = False,
        forward_secrecy: bool = False,
        protocols: bool = True,
        grease: bool = False,
        server_defaults: bool = True,
        server_preference: bool = False,
        single_cipher: str = "",
        client_simulation: bool = False,
        headers: bool = False,
        vulnerable: bool = False,
        full: bool = False,
        bugs: bool = False,
        assume_http: bool = False,
        ssl_native: bool = False,
        openssl_path: str = "",
        proxy: str = "",
        ipv4_only: bool = False,
        ipv6_only: bool = False,
        ip: str = "",
        nodns: str = "",
        sneaky: bool = False,
        user_agent: str = "",
        ids_friendly: bool = False,
        phone_out: bool = False,
        add_ca: str = "",
        mtls: str = "",
        basicauth: str = "",
        reqheader: str = "",
        rating_only: bool = False,
        quiet: bool = True,
        wide: bool = False,
        show_each: bool = False,
        mapping: str = "",
        color: int = 0,
        colorblind: bool = False,
        debug: int = 0,
        disable_rating: bool = False,
        logfile: str = "",
        json_output: bool = False,
        jsonfile: str = "",
        json_pretty: bool = False,
        jsonfile_pretty: str = "",
        csv_output: bool = False,
        csvfile: str = "",
        html_output: bool = False,
        htmlfile: str = "",
        outfile: str = "",
        hints: bool = False,
        severity: str = "",
        append: bool = False,
        overwrite: bool = False,
        outprefix: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute testssl.sh for TLS/SSL analysis.

        Args:
            target: host|host:port|URL|URL:port. Required unless using a standalone mode
            additional_args: Additional raw testssl.sh arguments

        Returns:
            TLS/SSL analysis results

        Examples:
            - Basic protocol and server-default checks:
              testssl_analyze(target="https://example.com", protocols=True, server_defaults=True)
            - Standalone version mode:
              testssl_analyze(version=True)
            - Header-focused run with JSON output:
              testssl_analyze(target="example.com", headers=True, json_output=True)
            - STARTTLS SMTP check:
              testssl_analyze(target="mail.example.com:25", starttls="smtp", protocols=True)
        """
        data = {
            "target": target,
            "help_mode": help_mode,
            "banner": banner,
            "version": version,
            "local_mode": local_mode,
            "local_pattern": local_pattern,
            "starttls": starttls,
            "xmpphost": xmpphost,
            "mx": mx,
            "file_input": file_input,
            "mode": mode,
            "warnings": warnings,
            "socket_timeout": socket_timeout,
            "openssl_timeout": openssl_timeout,
            "each_cipher": each_cipher,
            "cipher_per_proto": cipher_per_proto,
            "categories": categories,
            "forward_secrecy": forward_secrecy,
            "protocols": protocols,
            "grease": grease,
            "server_defaults": server_defaults,
            "server_preference": server_preference,
            "single_cipher": single_cipher,
            "client_simulation": client_simulation,
            "headers": headers,
            "vulnerable": vulnerable,
            "full": full,
            "bugs": bugs,
            "assume_http": assume_http,
            "ssl_native": ssl_native,
            "openssl_path": openssl_path,
            "proxy": proxy,
            "ipv4_only": ipv4_only,
            "ipv6_only": ipv6_only,
            "ip": ip,
            "nodns": nodns,
            "sneaky": sneaky,
            "user_agent": user_agent,
            "ids_friendly": ids_friendly,
            "phone_out": phone_out,
            "add_ca": add_ca,
            "mtls": mtls,
            "basicauth": basicauth,
            "reqheader": reqheader,
            "rating_only": rating_only,
            "quiet": quiet,
            "wide": wide,
            "show_each": show_each,
            "mapping": mapping,
            "color": color,
            "colorblind": colorblind,
            "debug": debug,
            "disable_rating": disable_rating,
            "logfile": logfile,
            "json_output": json_output,
            "jsonfile": jsonfile,
            "json_pretty": json_pretty,
            "jsonfile_pretty": jsonfile_pretty,
            "csv_output": csv_output,
            "csvfile": csvfile,
            "html_output": html_output,
            "htmlfile": htmlfile,
            "outfile": outfile,
            "hints": hints,
            "severity": severity,
            "append": append,
            "overwrite": overwrite,
            "outprefix": outprefix,
            "additional_args": additional_args,
        }
        logger.info(f"🔐 Starting testssl.sh analysis: {target or 'standalone mode'}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/testssl", data)
        )
        if result.get("success"):
            logger.info(f"✅ testssl.sh analysis completed for {target or 'standalone mode'}")
        else:
            logger.error(f"❌ testssl.sh analysis failed for {target or 'standalone mode'}")
        return result
