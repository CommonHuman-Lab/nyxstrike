import os
import shlex
import shutil

from backend.server_core import config_core
from backend.server_core.tool_spec import ParamSpec, ToolSpec


def _nbtscan_command(p: dict) -> str:
    argv = ["nbtscan", "-t", str(p["timeout"])]
    if p["verbose"]:
        argv.append("-v")
    argv.append(p["target"])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _enum4linux_command(p: dict) -> str:
    argv = ["enum4linux"]
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    argv.append(p["target"])
    return shlex.join(argv)


def _enum4linux_ng_command(p: dict) -> str:
    override = config_core.get("BINARY_PATH_OVERRIDES", {}).get("enum4linux-ng", "")
    binary = "enum4linux-ng"
    if override:
        binary = os.path.expanduser(override.replace("{HOME}", os.path.expanduser("~")))
    elif not shutil.which(binary):
        candidate = os.path.expanduser("~/.local/bin/enum4linux-ng")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            binary = candidate
    argv = [binary, p["target"]]
    if p["username"]:
        argv.append("-u")
        argv.append(p["username"])
    if p["password"]:
        argv.append("-p")
        argv.append(p["password"])
    if p["domain"]:
        argv.append("-w")
        argv.append(p["domain"])

    enum_options = []
    if p["shares"]:
        enum_options.append("S")
    if p["users"]:
        enum_options.append("U")
    if p["groups"]:
        enum_options.append("G")
    if p["policy"]:
        enum_options.append("P")
    if len(enum_options) == 4:
        # -A is a switch, not an option accepting a comma-separated module list.
        argv.append("-A")
    else:
        argv.extend(f"-{option}" for option in enum_options)

    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _netexec_command(p: dict) -> str:
    argv = ["nxc", p["protocol"], p["target"]]
    if p["username"]:
        argv.append("-u")
        argv.append(p["username"])
    if p["password"]:
        argv.append("-p")
        argv.append(p["password"])
    if p["hash"]:
        argv.append("-H")
        argv.append(p["hash"])
    if p["module"]:
        argv.append("-M")
        argv.append(p["module"])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _smbmap_command(p: dict) -> str:
    argv = ["smbmap", "-H", p["target"]]
    if p["username"]:
        argv.append("-u")
        argv.append(p["username"])
    if p["password"]:
        argv.append("-p")
        argv.append(p["password"])
    if p["domain"]:
        argv.append("-d")
        argv.append(p["domain"])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _rpcclient_command(p: dict) -> str:
    rpc_argv = ["rpcclient"]
    if p["username"] and p["password"]:
        rpc_argv += ["-U", f"{p['username']}%{p['password']}"]
    elif p["username"]:
        rpc_argv += ["-U", p["username"]]
    else:
        rpc_argv += ["-U", ""]

    if p["domain"]:
        rpc_argv += ["-W", p["domain"]]

    rpc_argv.append(p["target"])
    if p["additional_args"]:
        rpc_argv += shlex.split(p["additional_args"])

    command_sequence = p["commands"].replace(";", "\n")
    echo_argv = ["echo", "-e", command_sequence]
    return shlex.join(echo_argv) + " | " + shlex.join(rpc_argv)


SPECS = [
    ToolSpec(
        name="nbtscan",
        mcp_tool_name="nbtscan_netbios",
        endpoint="/api/tools/nbtscan",
        category="smb_enum",
        description="Execute nbtscan for NetBIOS name scanning.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address or range"),
            ParamSpec("verbose", bool, default=False, help_text="Enable verbose output"),
            ParamSpec("timeout", int, default=2, help_text="Timeout in seconds"),
            ParamSpec("additional_args", str, default="", help_text="Additional nbtscan arguments"),
        ],
        build_command=_nbtscan_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="enum4linux",
        mcp_tool_name="enum4linux_scan",
        endpoint="/api/tools/enum4linux",
        category="smb_enum",
        description="Execute Enum4linux for SMB enumeration.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address"),
            ParamSpec("additional_args", str, default="-a", help_text="Additional Enum4linux arguments"),
        ],
        build_command=_enum4linux_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="enum4linux-ng",
        mcp_tool_name="enum4linux_ng_advanced",
        endpoint="/api/tools/enum4linux-ng",
        category="smb_enum",
        description="Execute Enum4linux-ng for advanced SMB enumeration.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address"),
            ParamSpec("username", str, default="", help_text="Username for authentication"),
            ParamSpec("password", str, default="", help_text="Password for authentication"),
            ParamSpec("domain", str, default="", help_text="Domain for authentication"),
            ParamSpec("shares", bool, default=True, help_text="Enumerate shares"),
            ParamSpec("users", bool, default=True, help_text="Enumerate users"),
            ParamSpec("groups", bool, default=True, help_text="Enumerate groups"),
            ParamSpec("policy", bool, default=True, help_text="Enumerate policies"),
            ParamSpec("additional_args", str, default="", help_text="Additional Enum4linux-ng arguments"),
        ],
        build_command=_enum4linux_ng_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="netexec",
        mcp_tool_name="netexec_scan",
        endpoint="/api/tools/netexec",
        category="smb_enum",
        description="Execute NetExec (formerly CrackMapExec) for network enumeration.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP or network"),
            ParamSpec("protocol", str, default="smb", help_text="Protocol to use (smb, ssh, winrm, etc.)"),
            ParamSpec("username", str, default="", help_text="Username for authentication"),
            ParamSpec("password", str, default="", help_text="Password for authentication"),
            ParamSpec("hash", str, default="", help_text="Hash for pass-the-hash attacks"),
            ParamSpec("module", str, default="", help_text="NetExec module to execute"),
            ParamSpec("additional_args", str, default="", help_text="Additional NetExec arguments"),
        ],
        build_command=_netexec_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="smbmap",
        mcp_tool_name="smbmap_scan",
        endpoint="/api/tools/smbmap",
        category="smb_enum",
        description="Execute SMBMap for SMB share enumeration.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address"),
            ParamSpec("username", str, default="", help_text="Username for authentication"),
            ParamSpec("password", str, default="", help_text="Password for authentication"),
            ParamSpec("domain", str, default="", help_text="Domain for authentication"),
            ParamSpec("additional_args", str, default="", help_text="Additional SMBMap arguments"),
        ],
        build_command=_smbmap_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="rpcclient",
        mcp_tool_name="rpcclient_enumeration",
        endpoint="/api/tools/rpcclient",
        category="smb_enum",
        description="Execute rpcclient for RPC enumeration.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address"),
            ParamSpec("username", str, default="", help_text="Username for authentication"),
            ParamSpec("password", str, default="", help_text="Password for authentication"),
            ParamSpec("domain", str, default="", help_text="Domain for authentication"),
            ParamSpec("commands", str, default="enumdomusers;enumdomgroups;querydominfo", help_text="Semicolon-separated RPC commands"),
            ParamSpec("additional_args", str, default="", help_text="Additional rpcclient arguments"),
        ],
        build_command=_rpcclient_command,
        use_recovery=True,
    ),
]
