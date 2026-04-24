# mcp_tools/ad/impacket.py
import asyncio
from typing import Dict, Any, Optional

def register_impacket(mcp, api_client, logger, CliColors):
    """
    Register MCP tools for generic Impacket script execution.

    Expected backend endpoints:
      - POST /api/tool/active_directory/impacket
      - GET  /api/tool/active_directory/impacket/spec/<script_name>
    """

    async def _run_post(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: api_client.safe_post(endpoint, data)
        )

    async def _run_get(endpoint: str) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: api_client.safe_get(endpoint)
        )

    @mcp.tool()
    async def impacket_run(
        script: str,
        target: str = "",
        options: Optional[Dict[str, Any]] = None,
        positional: Optional[list[str]] = None,
        positional_map: Optional[Dict[str, Any]] = None,
        extra_args: str = "",
        use_recovery: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute any supported Impacket script through the generic backend wrapper.

        Args:
            script: Impacket script name without the 'impacket-' prefix
                    (e.g. GetADUsers, GetNPUsers, psexec, smbclient)
            target: Primary target/credential string for scripts that require it
            options: Dictionary of script flags/options, e.g.
                     {"dc-ip": "10.10.10.10", "all": True, "debug": True}
            positional: Extra positional arguments as a list, e.g.
                        ["input.kirbi", "output.ccache"]
            positional_map: Named positional arguments if backend supports them
            extra_args: Raw extra CLI args for edge cases
            use_recovery: Whether backend should use enhanced recovery logic

        Returns:
            Execution result from the API backend
        """
        data: Dict[str, Any] = {
            "script": script,
            "target": target,
            "options": options or {},
            "positional": positional or [],
            "positional_map": positional_map or {},
            "extra_args": extra_args,
            "use_recovery": use_recovery,
        }

        logger.info(
            f"{CliColors.FIRE_RED}🧨 Starting Impacket script: {script}"
            f"{f' against {target}' if target else ''}{CliColors.RESET}"
        )

        result = await _run_post("api/tools/impacket", data)

        if result.get("success"):
            logger.info(
                f"{CliColors.SUCCESS}✅ Impacket script completed: {script}{CliColors.RESET}"
            )

            if result.get("recovery_info", {}).get("recovery_applied"):
                recovery_info = result["recovery_info"]
                attempts = recovery_info.get("attempts_made", 1)
                logger.info(
                    f"{CliColors.HIGHLIGHT_YELLOW}Recovery applied for {script}: "
                    f"{attempts} attempts made{CliColors.RESET}"
                )
        else:
            logger.error(
                f"{CliColors.ERROR}❌ Impacket script failed: {script}{CliColors.RESET}"
            )

            if result.get("human_escalation"):
                logger.error(
                    f"{CliColors.CRITICAL}HUMAN ESCALATION REQUIRED{CliColors.RESET}"
                )

        return result

    @mcp.tool()
    async def impacket_get_spec(script: str) -> Dict[str, Any]:
        """
        Fetch the backend-discovered specification for an Impacket script.

        Useful for agents/UI logic to discover:
          - required positional arguments
          - supported options
          - usage string

        Args:
            script: Impacket script name without the 'impacket-' prefix

        Returns:
            Script specification from the backend
        """
        logger.info(
            f"{CliColors.FIRE_RED}📚 Fetching Impacket spec for: {script}{CliColors.RESET}"
        )

        result = await _run_get(f"api/tools/impacket/spec/{script}")

        if result.get("error"):
            logger.error(
                f"{CliColors.ERROR}❌ Failed to fetch Impacket spec for {script}{CliColors.RESET}"
            )
        else:
            logger.info(
                f"{CliColors.SUCCESS}✅ Loaded Impacket spec for {script}{CliColors.RESET}"
            )

        return result

    @mcp.tool()
    async def impacket_ad_enum(
        script: str,
        target: str,
        dc_ip: str = "",
        username: str = "",
        password: str = "",
        hashes: str = "",
        kerberos: bool = False,
        no_pass: bool = False,
        aes_key: str = "",
        debug: bool = False,
        extra_options: Optional[Dict[str, Any]] = None,
        extra_args: str = "",
    ) -> Dict[str, Any]:
        """
        Convenience wrapper for common AD enumeration Impacket scripts such as:
          - GetADUsers
          - GetADComputers
          - GetNPUsers
          - GetUserSPNs
          - GetLAPSPassword
          - findDelegation
          - lookupsid

        Args:
            script: Script name without 'impacket-' prefix
            target: Target string expected by the script
            dc_ip: Domain controller IP
            username: Optional username for scripts/agent formatting
            password: Optional password for scripts/agent formatting
            hashes: LM:NT hashes
            kerberos: Enable -k
            no_pass: Enable -no-pass
            aes_key: AES key for Kerberos auth
            debug: Enable -debug
            extra_options: Extra options dict merged into generated options
            extra_args: Raw extra CLI args for edge cases

        Returns:
            Execution result from backend
        """
        options: Dict[str, Any] = extra_options.copy() if extra_options else {}

        if dc_ip:
            options["dc-ip"] = dc_ip
        if hashes:
            options["hashes"] = hashes
        if kerberos:
            options["k"] = True
        if no_pass:
            options["no-pass"] = True
        if aes_key:
            options["aesKey"] = aes_key
        if debug:
            options["debug"] = True

        # username/password are not forced into options because most Impacket tools
        # usually expect them embedded in target; still passed through for agent context
        if username:
            options.setdefault("username", username)
        if password:
            options.setdefault("password", password)

        data: Dict[str, Any] = {
            "script": script,
            "target": target,
            "options": options,
            "extra_args": extra_args,
            "use_recovery": True,
        }

        logger.info(
            f"{CliColors.FIRE_RED}🕵️ Starting AD Impacket enumeration with {script} "
            f"against {target}{CliColors.RESET}"
        )

        result = await _run_post("api/tools/impacket", data)

        if result.get("success"):
            logger.info(
                f"{CliColors.SUCCESS}✅ AD Impacket enumeration completed: {script}{CliColors.RESET}"
            )
        else:
            logger.error(
                f"{CliColors.ERROR}❌ AD Impacket enumeration failed: {script}{CliColors.RESET}"
            )

        return result

    @mcp.tool()
    async def impacket_remote_exec(
        script: str,
        target: str,
        command: str = "",
        hashes: str = "",
        kerberos: bool = False,
        no_pass: bool = False,
        aes_key: str = "",
        share: str = "",
        shell_type: str = "",
        debug: bool = False,
        extra_options: Optional[Dict[str, Any]] = None,
        extra_args: str = "",
    ) -> Dict[str, Any]:
        """
        Convenience wrapper for remote execution / interaction style scripts such as:
          - psexec
          - smbexec
          - wmiexec / wmiquery if added later
          - dcomexec
          - atexec
          - smbclient

        Args:
            script: Script name without 'impacket-' prefix
            target: Full target string
            command: Optional command to execute if supported by the script
            hashes: LM:NT hashes
            kerberos: Enable -k
            no_pass: Enable -no-pass
            aes_key: AES key for Kerberos auth
            share: SMB share if supported
            shell_type: Shell type if supported
            debug: Enable -debug
            extra_options: Additional options
            extra_args: Raw fallback args

        Returns:
            Execution result from backend
        """
        options: Dict[str, Any] = extra_options.copy() if extra_options else {}

        if hashes:
            options["hashes"] = hashes
        if kerberos:
            options["k"] = True
        if no_pass:
            options["no-pass"] = True
        if aes_key:
            options["aesKey"] = aes_key
        if share:
            options["share"] = share
        if shell_type:
            options["shell-type"] = shell_type
        if debug:
            options["debug"] = True

        if command:
            options["command"] = command

        data: Dict[str, Any] = {
            "script": script,
            "target": target,
            "options": options,
            "extra_args": extra_args,
            "use_recovery": True,
        }

        logger.info(
            f"{CliColors.FIRE_RED}⚔️ Starting remote Impacket action with {script} "
            f"against {target}{CliColors.RESET}"
        )

        result = await _run_post("api/tools/impacket", data)

        if result.get("success"):
            logger.info(
                f"{CliColors.SUCCESS}✅ Remote Impacket action completed: {script}{CliColors.RESET}"
            )
        else:
            logger.error(
                f"{CliColors.ERROR}❌ Remote Impacket action failed: {script}{CliColors.RESET}"
            )

        return result