# mcp_tools/recon/autorecon.py

from typing import Dict, Any
import asyncio

def register_autorecon_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def autorecon_scan(
        target: str = "",
        target_file: str = "",
        ports: str = "",
        output_dir: str = "",
        max_scans: str = "",
        max_port_scans: str = "",
        heartbeat: str = "",
        timeout: str = "",
        target_timeout: str = "",
        config_file: str = "",
        global_file: str = "",
        plugins_dir: str = "",
        add_plugins_dir: str = "",
        tags: str = "",
        exclude_tags: str = "",
        port_scans: str = "",
        service_scans: str = "",
        reports: str = "",
        single_target: bool = False,
        only_scans_dir: bool = False,
        no_port_dirs: bool = False,
        nmap: str = "",
        nmap_append: str = "",
        proxychains: bool = False,
        disable_sanity_checks: bool = False,
        disable_keyboard_control: bool = False,
        force_services: str = "",
        accessible: bool = False,
        verbose: int = 0,
        curl_path: str = "",
        dirbuster_tool: str = "",
        dirbuster_wordlist: str = "",
        dirbuster_threads: str = "",
        dirbuster_ext: str = "",
        onesixtyone_community_strings: str = "",
        global_username_wordlist: str = "",
        global_password_wordlist: str = "",
        global_domain: str = "",
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute AutoRecon for comprehensive target enumeration with full parameter support.

        Args:
            target: Single target to scan
            target_file: File containing multiple targets
            ports: Specific ports to scan
            output_dir: Output directory
            max_scans: Maximum number of concurrent scans
            max_port_scans: Maximum number of concurrent port scans
            heartbeat: Heartbeat interval
            timeout: Global timeout
            target_timeout: Per-target timeout
            config_file: Configuration file path
            global_file: Global configuration file
            plugins_dir: Plugins directory
            add_plugins_dir: Additional plugins directory
            tags: Plugin tags to include
            exclude_tags: Plugin tags to exclude
            port_scans: Port scan plugins to run
            service_scans: Service scan plugins to run
            reports: Report plugins to run
            single_target: Use single target directory structure
            only_scans_dir: Only create scans directory
            no_port_dirs: Don't create port directories
            nmap: Custom nmap command
            nmap_append: Arguments to append to nmap
            proxychains: Use proxychains
            disable_sanity_checks: Disable sanity checks
            disable_keyboard_control: Disable keyboard control
            force_services: Force service detection
            accessible: Enable accessible output
            verbose: Verbosity level (0-3)
            curl_path: Custom curl path
            dirbuster_tool: Directory busting tool
            dirbuster_wordlist: Directory busting wordlist
            dirbuster_threads: Directory busting threads
            dirbuster_ext: Directory busting extensions
            onesixtyone_community_strings: SNMP community strings
            global_username_wordlist: Global username wordlist
            global_password_wordlist: Global password wordlist
            global_domain: Global domain
            additional_args: Additional AutoRecon arguments

        Returns:
            Comprehensive enumeration results with full configurability
        """
        data = {
            "target": target,
            "target_file": target_file,
            "ports": ports,
            "output_dir": output_dir,
            "max_scans": max_scans,
            "max_port_scans": max_port_scans,
            "heartbeat": heartbeat,
            "timeout": timeout,
            "target_timeout": target_timeout,
            "config_file": config_file,
            "global_file": global_file,
            "plugins_dir": plugins_dir,
            "add_plugins_dir": add_plugins_dir,
            "tags": tags,
            "exclude_tags": exclude_tags,
            "port_scans": port_scans,
            "service_scans": service_scans,
            "reports": reports,
            "single_target": single_target,
            "only_scans_dir": only_scans_dir,
            "no_port_dirs": no_port_dirs,
            "nmap": nmap,
            "nmap_append": nmap_append,
            "proxychains": proxychains,
            "disable_sanity_checks": disable_sanity_checks,
            "disable_keyboard_control": disable_keyboard_control,
            "force_services": force_services,
            "accessible": accessible,
            "verbose": verbose,
            "curl_path": curl_path,
            "dirbuster_tool": dirbuster_tool,
            "dirbuster_wordlist": dirbuster_wordlist,
            "dirbuster_threads": dirbuster_threads,
            "dirbuster_ext": dirbuster_ext,
            "onesixtyone_community_strings": onesixtyone_community_strings,
            "global_username_wordlist": global_username_wordlist,
            "global_password_wordlist": global_password_wordlist,
            "global_domain": global_domain,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting AutoRecon comprehensive enumeration: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/autorecon", data)
        )
        if result.get("success"):
            logger.info(f"✅ AutoRecon comprehensive enumeration completed for {target}")
        else:
            logger.error(f"❌ AutoRecon failed for {target}")
        return result
    
    @mcp.tool()
    async def autorecon_comprehensive(target: str, output_dir: str = "/tmp/autorecon",
                               port_scans: str = "top-100-ports", service_scans: str = "default",
                               heartbeat: int = 60, timeout: int = 300,
                               additional_args: str = "") -> Dict[str, Any]:
        """
        Execute AutoRecon for comprehensive automated reconnaissance.

        Args:
            target: The target IP address or hostname
            output_dir: Output directory for results
            port_scans: Port scan configuration
            service_scans: Service scan configuration
            heartbeat: Heartbeat interval in seconds
            timeout: Timeout for individual scans
            additional_args: Additional AutoRecon arguments

        Returns:
            Comprehensive automated reconnaissance results
        """
        data = {
            "target": target,
            "output_dir": output_dir,
            "port_scans": port_scans,
            "service_scans": service_scans,
            "heartbeat": heartbeat,
            "timeout": timeout,
            "additional_args": additional_args
        }
        logger.info(f"🔄 Starting AutoRecon: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/autorecon", data)
        )
        if result.get("success"):
            logger.info(f"✅ AutoRecon completed for {target}")
        else:
            logger.error(f"❌ AutoRecon failed for {target}")
        return result
