# mcp_tools/credential_harvest/vaultrip.py

from typing import Dict, Any, Optional
import asyncio


def register_vaultrip_tool(mcp, api_client, logger):

    @mcp.tool()
    async def vaultrip_sweep(
        target: str = "~",
        local: bool = True,
        memory: bool = True,
        browser: bool = True,
        system: bool = True,
        kerberos: bool = True,
        dump_path: str = "",
        remote: bool = False,
        ssh_host: str = "",
        ssh_user: str = "",
        ssh_key: str = "",
        ssh_password: str = "",
        ssh_port: int = 22,
        verbose: bool = False,
        timeout: int = 30,
        # Active attack modules — explicit opt-in
        dcsync: bool = False,
        pth: bool = False,
        ptt: bool = False,
        forge_golden: bool = False,
        forge_silver: bool = False,
        dc_host: str = "",
        ad_domain: str = "",
        domain_sid: str = "",
        krbtgt_hash: str = "",
        attack_user: str = "",
        attack_hash: str = "",
        attack_cmd: str = "whoami",
        ptt_ticket: str = "",
        forge_silver_spn: str = "",
    ) -> Dict[str, Any]:
        """
        Run VaultRip post-exploitation credential harvesting sweep.

        VaultRip sweeps six credential surfaces in one pass: filesystem credential files,
        process memory (/proc/*/mem), browser stores (Chrome/Firefox/Edge), system keyrings,
        Kerberos ccache/keytab files, and optional offline dump analysis (LSASS/SAM/NTDS).

        Active attack modules (DCSync, PTH, ticket forging) are disabled by default and
        require explicit flags — they perform live operations against Active Directory.

        Args:
            target: Root directory to sweep (default "~" = current user's home)
            local: Sweep filesystem for credential files (55 paths × 26 services)
            memory: Scan /proc/*/mem for credentials in process memory (Linux only)
            browser: Extract saved credentials from Chrome, Firefox, Edge, Brave
            system: Query GNOME keyring, kwallet, git-credentials, Docker, .pgpass
            kerberos: Extract ccache and keytab Kerberos tickets
            dump_path: Path to an offline dump file for analysis (LSASS/SAM/NTDS.dit)
            remote: Harvest credentials via SSH from a remote host
            ssh_host: Remote host IP or hostname (requires remote=True)
            ssh_user: SSH username
            ssh_key: Path to SSH private key file
            ssh_password: SSH password (prefer key-based auth)
            ssh_port: SSH port (default 22)
            verbose: Include extracted credential values in the output
            timeout: Per-module timeout in seconds
            dcsync: ⚠ Replicate all AD credentials via DRSUAPI (requires dc_host, ad_domain, attack_hash)
            pth: ⚠ Execute a command on a Windows host via Pass-the-Hash (requires dc_host, attack_hash)
            ptt: ⚠ Inject a ccache into the current session via Pass-the-Ticket (requires ptt_ticket)
            forge_golden: ⚠ Forge a Kerberos golden ticket (requires ad_domain, domain_sid, krbtgt_hash)
            forge_silver: ⚠ Forge a Kerberos silver ticket (requires ad_domain, domain_sid, attack_hash, forge_silver_spn)
            dc_host: Domain controller IP or hostname
            ad_domain: Active Directory domain name (e.g. corp.local)
            domain_sid: Domain SID (S-1-5-21-...)
            krbtgt_hash: NT hash of the krbtgt account (golden ticket forging)
            attack_user: Username to impersonate in forged tickets or PTH
            attack_hash: NT hash for PTH / silver ticket
            attack_cmd: Command to run after Pass-the-Hash (default: whoami)
            ptt_ticket: Path to .ccache or .kirbi file for Pass-the-Ticket injection
            forge_silver_spn: Service Principal Name for silver ticket (e.g. cifs/server.corp.local)

        Returns:
            VaultRip sweep results with all discovered credentials grouped by module
        """
        payload = {
            "target": target,
            "local": local,
            "memory": memory,
            "browser": browser,
            "system": system,
            "kerberos": kerberos,
            "dump_path": dump_path or None,
            "remote": remote,
            "ssh_host": ssh_host or None,
            "ssh_user": ssh_user or None,
            "ssh_key": ssh_key or None,
            "ssh_password": ssh_password or None,
            "ssh_port": ssh_port,
            "verbose": verbose,
            "timeout": timeout,
            "dcsync": dcsync,
            "pth": pth,
            "ptt": ptt,
            "forge_golden": forge_golden,
            "forge_silver": forge_silver,
            "dc_host": dc_host,
            "ad_domain": ad_domain,
            "domain_sid": domain_sid,
            "krbtgt_hash": krbtgt_hash,
            "attack_user": attack_user,
            "attack_hash": attack_hash,
            "attack_cmd": attack_cmd,
            "ptt_ticket": ptt_ticket,
            "forge_silver_spn": forge_silver_spn,
        }
        mode = f"remote ({ssh_host})" if remote and ssh_host else f"local ({target})"
        logger.info(f"Starting VaultRip sweep: {mode}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/vaultrip", payload)
        )
        if result.get("success"):
            findings = result.get("output", {}).get("total_findings", 0)
            logger.info(f"VaultRip sweep completed — {findings} credential(s) found")
        else:
            logger.error("VaultRip sweep failed")
        return result
