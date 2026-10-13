import os
import shlex

from backend.server_core.tool_spec import ParamSpec, ToolSpec, ToolValidationError


def _amass_command(p: dict) -> str:
    argv = ["amass", p["mode"], "-d", p["domain"]]
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _assetfinder_command(p: dict) -> str:
    argv = ["assetfinder"]
    if p["only_subdomains"]:
        argv.append("--subs-only")
    argv.append(p["domain"])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _autorecon_command(p: dict) -> str:
    # The installer uses Paul Schubert's PyPI package, whose CLI differs from Tib3rius'.
    argv = ["autorecon", p["target"], "-f", "-j"]
    if p.get("output_dir"):
        os.makedirs(p["output_dir"], exist_ok=True)
        argv.extend(["-o", p["output_dir"] + "/autorecon.json"])
    if p.get("additional_args"):
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _massdns_command(p: dict) -> str:
    if not p["domainlist"] and not p["resolvers"] and not p["additional_args"]:
        raise ToolValidationError("domainlist is required (path to input names file)")
    if p["status_format"] and p["status_format"] not in {"json", "ansi"}:
        raise ToolValidationError("status_format must be either 'json' or 'ansi'")

    argv = ["massdns"]
    if p["bindto"]:
        argv.extend(["-b", p["bindto"]])
    if p["busy_poll"]:
        argv.append("--busy-poll")
    if p["resolve_count"]:
        argv.extend(["-c", str(p["resolve_count"])])
    if p["drop_group"]:
        argv.extend(["--drop-group", p["drop_group"]])
    if p["drop_user"]:
        argv.extend(["--drop-user", p["drop_user"]])
    if p["extended_input"]:
        argv.append("--extended-input")
    if p["filter"]:
        argv.extend(["--filter", str(p["filter"])])
    if p["flush"]:
        argv.append("--flush")
    if p["ignore"]:
        argv.extend(["--ignore", str(p["ignore"])])
    if p["interval"]:
        argv.extend(["-i", str(p["interval"])])
    if p["error_log"]:
        argv.extend(["-l", p["error_log"]])
    if p["norecurse"]:
        argv.append("--norecurse")
    if p["output"]:
        argv.extend(["-o", p["output"]])
    if p["predictable"]:
        argv.append("--predictable")
    if p["processes"]:
        argv.extend(["--processes", str(p["processes"])])
    if p["quiet"]:
        argv.append("-q")
    if p["rand_src_ipv6"]:
        argv.extend(["--rand-src-ipv6", p["rand_src_ipv6"]])
    if p["rcvbuf"]:
        argv.extend(["--rcvbuf", str(p["rcvbuf"])])
    if p["retry"]:
        argv.extend(["--retry", str(p["retry"])])
    if p["resolvers"]:
        argv.extend(["-r", p["resolvers"]])
    if p["root"]:
        argv.append("--root")
    if p["hashmap_size"]:
        argv.extend(["-s", str(p["hashmap_size"])])
    if p["sndbuf"]:
        argv.extend(["--sndbuf", str(p["sndbuf"])])
    if p["status_format"]:
        argv.extend(["--status-format", p["status_format"]])
    if p["sticky"]:
        argv.append("--sticky")
    if p["socket_count"]:
        argv.extend(["--socket-count", str(p["socket_count"])])
    if p["record_type"]:
        argv.extend(["-t", p["record_type"]])
    if p["verify_ip"]:
        argv.append("--verify-ip")
    if p["outfile"]:
        argv.extend(["-w", p["outfile"]])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    if p["domainlist"]:
        argv.append(p["domainlist"])
    return shlex.join(argv)


def _shuffledns_command(p: dict) -> str:
    domain = p["domain"]
    domains = p["domains"]
    if isinstance(domains, str):
        domains = [domains]
    elif not isinstance(domains, list):
        domains = []

    normalized_domains = []
    if isinstance(domain, str) and domain.strip():
        normalized_domains.append(domain.strip())
    for d in domains:
        if isinstance(d, str) and d.strip():
            normalized_domains.append(d.strip())

    mode = p["mode"]
    valid_modes = {"", "bruteforce", "resolve", "filter"}
    if mode not in valid_modes:
        raise ToolValidationError("Invalid mode. Use one of: bruteforce, resolve, filter")

    if not p["update"] and not p["version"]:
        if not normalized_domains and not p["list"] and not p["raw_input"]:
            raise ToolValidationError("Provide at least one input: domain/domains, list, or raw_input")
        if mode == "bruteforce" and not p["wordlist"]:
            raise ToolValidationError("wordlist is required when mode is bruteforce")

    argv = ["shuffledns"]
    for d in normalized_domains:
        argv.extend(["-d", d])
    if p["auto_domain"]:
        argv.append("-ad")
    if p["list"]:
        argv.extend(["-l", p["list"]])
    if p["wordlist"]:
        argv.extend(["-w", p["wordlist"]])
    if p["resolver"]:
        argv.extend(["-r", p["resolver"]])
    if p["trusted_resolver"]:
        argv.extend(["-tr", p["trusted_resolver"]])
    if p["raw_input"]:
        argv.extend(["-ri", p["raw_input"]])
    if mode:
        argv.extend(["-mode", mode])
    if p["threads"]:
        argv.extend(["-t", str(p["threads"])])
    if p["output"]:
        argv.extend(["-o", p["output"]])
    if p["json"]:
        argv.append("-j")
    if p["wildcard_output"]:
        argv.extend(["-wo", p["wildcard_output"]])
    if p["massdns"]:
        argv.extend(["-m", p["massdns"]])
    if p["massdns_cmd"]:
        argv.extend(["-mcmd", p["massdns_cmd"]])
    if p["directory"]:
        argv.extend(["-directory", p["directory"]])
    if p["retries"]:
        argv.extend(["-retries", str(p["retries"])])
    if p["strict_wildcard"]:
        argv.append("-sw")
    if p["wildcard_threads"]:
        argv.extend(["-wt", str(p["wildcard_threads"])])
    if p["silent"]:
        argv.append("-silent")
    if p["version"]:
        argv.append("-version")
    if p["verbose"]:
        argv.append("-v")
    if p["no_color"]:
        argv.append("-nc")
    if p["update"]:
        argv.append("-up")
    if p["disable_update_check"]:
        argv.append("-duc")
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _subfinder_command(p: dict) -> str:
    argv = ["subfinder", "-d", p["domain"]]
    if p["silent"]:
        argv.append("-silent")
    if p["all_sources"]:
        argv.append("-all")
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _theharvester_command(p: dict) -> str:
    argv = ["theHarvester", "-d", p["domain"]]
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


SPECS = [
    ToolSpec(
        name="amass",
        mcp_tool_name="amass_scan",
        endpoint="/api/tools/amass",
        category="recon",
        description="Execute Amass for subdomain enumeration.",
        params=[
            ParamSpec("domain", str, required=True, help_text="The target domain"),
            ParamSpec("mode", str, default="enum", help_text="Amass mode (enum, intel, viz)"),
            ParamSpec("additional_args", str, default="", help_text="Additional Amass arguments"),
        ],
        build_command=_amass_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="assetfinder",
        mcp_tool_name="assetfinder_scan",
        endpoint="/api/tools/assetfinder",
        category="recon",
        description="Execute Assetfinder for passive subdomain enumeration.",
        params=[
            ParamSpec("domain", str, required=True, help_text="The target domain"),
            ParamSpec("only_subdomains", bool, default=True, help_text="Use --subs-only output mode"),
            ParamSpec("additional_args", str, default="", help_text="Additional Assetfinder arguments"),
        ],
        build_command=_assetfinder_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="autorecon",
        mcp_tool_name="autorecon_scan",
        endpoint="/api/tools/autorecon",
        category="recon",
        description="Execute AutoRecon for comprehensive automated reconnaissance.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address or hostname"),
            ParamSpec("output_dir", str, default="/tmp/autorecon", help_text="Output directory for results"),
            ParamSpec("port_scans", str, default="top-100-ports", help_text="Port scan configuration"),
            ParamSpec("service_scans", str, default="default", help_text="Service scan configuration"),
            ParamSpec("heartbeat", int, default=60, help_text="Heartbeat interval in seconds"),
            ParamSpec("timeout", int, default=300, help_text="Timeout for individual scans"),
            ParamSpec("additional_args", str, default="", help_text="Additional AutoRecon arguments"),
        ],
        build_command=_autorecon_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="massdns",
        mcp_tool_name="massdns_scan",
        endpoint="/api/tools/massdns",
        category="recon",
        description="Execute massdns with full CLI flag support for high-performance DNS resolution/bruteforce.",
        params=[
            ParamSpec("domainlist", str, default="", help_text="Path to file containing names to resolve"),
            ParamSpec("bindto", str, default="", help_text="Bind address and port (IP:PORT)"),
            ParamSpec("busy_poll", bool, default=False, help_text="Use busy-wait polling"),
            ParamSpec("resolve_count", int, default=50, help_text="Number of resolves before giving up"),
            ParamSpec("drop_group", str, default="", help_text="Group to drop privileges to"),
            ParamSpec("drop_user", str, default="", help_text="User to drop privileges to"),
            ParamSpec("extended_input", bool, default=False, help_text="Input names include resolver list"),
            ParamSpec("filter", str, default="", help_text="Output only specified response code"),
            ParamSpec("flush", bool, default=False, help_text="Flush output file on each response"),
            ParamSpec("ignore", str, default="", help_text="Exclude specified response code"),
            ParamSpec("interval", int, default=500, help_text="Interval in ms between resolves of same domain"),
            ParamSpec("error_log", str, default="", help_text="Error log path"),
            ParamSpec("norecurse", bool, default=False, help_text="Use non-recursive queries"),
            ParamSpec("output", str, default="", help_text="Output format flags (L,S,F,B,J)"),
            ParamSpec("predictable", bool, default=False, help_text="Use resolvers incrementally"),
            ParamSpec("processes", int, default=1, help_text="Number of resolver processes"),
            ParamSpec("quiet", bool, default=False, help_text="Quiet mode"),
            ParamSpec("rand_src_ipv6", str, default="", help_text="Random IPv6 source subnet"),
            ParamSpec("rcvbuf", int, default=0, help_text="Receive buffer size in bytes"),
            ParamSpec("retry", str, default="", help_text="Unacceptable DNS response codes"),
            ParamSpec("resolvers", str, default="", help_text="Resolver file path"),
            ParamSpec("root", bool, default=False, help_text="Do not drop privileges when running as root"),
            ParamSpec("hashmap_size", int, default=10000, help_text="Number of concurrent lookups"),
            ParamSpec("sndbuf", int, default=0, help_text="Send buffer size in bytes"),
            ParamSpec("status_format", str, default="", help_text="Real-time status format (json, ansi)"),
            ParamSpec("sticky", bool, default=False, help_text="Keep resolver on retry"),
            ParamSpec("socket_count", int, default=1, help_text="Socket count per process"),
            ParamSpec("record_type", str, default="A", help_text="DNS record type (A, AAAA, CNAME, etc.)"),
            ParamSpec("verify_ip", bool, default=False, help_text="Verify IP addresses in incoming replies"),
            ParamSpec("outfile", str, default="", help_text="Output file path"),
            ParamSpec("additional_args", str, default="", help_text="Additional massdns flags"),
        ],
        build_command=_massdns_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="shuffledns",
        mcp_tool_name="shuffledns_scan",
        endpoint="/api/tools/shuffledns",
        category="recon",
        description="Execute shuffleDNS for subdomain bruteforce/resolve/filter with wildcard handling.",
        params=[
            ParamSpec("domain", str, default="", help_text="Single domain target"),
            ParamSpec("domains", list, default=[], help_text="Multiple domain targets"),
            ParamSpec("auto_domain", bool, default=False, help_text="Automatically extract root domains"),
            ParamSpec("list", str, default="", help_text="File containing subdomains to resolve"),
            ParamSpec("wordlist", str, default="", help_text="Wordlist file for bruteforce mode"),
            ParamSpec("resolver", str, default="", help_text="Resolver list file"),
            ParamSpec("trusted_resolver", str, default="", help_text="Trusted resolver list file"),
            ParamSpec("raw_input", str, default="", help_text="Raw massdns output input file"),
            ParamSpec("mode", str, default="", help_text="Execution mode (bruteforce, resolve, filter)"),
            ParamSpec("threads", int, default=10000, help_text="Concurrent massdns resolves"),
            ParamSpec("output", str, default="", help_text="Output file path"),
            ParamSpec("json", bool, default=False, help_text="Output as ndjson"),
            ParamSpec("wildcard_output", str, default="", help_text="Wildcard IP output file"),
            ParamSpec("massdns", str, default="", help_text="Path to massdns binary"),
            ParamSpec("massdns_cmd", str, default="", help_text="Extra massdns commands"),
            ParamSpec("directory", str, default="", help_text="Temporary directory for enumeration"),
            ParamSpec("retries", int, default=5, help_text="Number of retries for DNS enumeration"),
            ParamSpec("strict_wildcard", bool, default=False, help_text="Perform wildcard checks on all found subdomains"),
            ParamSpec("wildcard_threads", int, default=250, help_text="Concurrent wildcard checks"),
            ParamSpec("silent", bool, default=False, help_text="Show only subdomains"),
            ParamSpec("version", bool, default=False, help_text="Show shuffledns version"),
            ParamSpec("verbose", bool, default=False, help_text="Show verbose output"),
            ParamSpec("no_color", bool, default=False, help_text="Disable color output"),
            ParamSpec("update", bool, default=False, help_text="Update shuffledns binary"),
            ParamSpec("disable_update_check", bool, default=False, help_text="Disable auto update check"),
            ParamSpec("additional_args", str, default="", help_text="Additional shuffledns arguments"),
        ],
        build_command=_shuffledns_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="subfinder",
        mcp_tool_name="subfinder_scan",
        endpoint="/api/tools/subfinder",
        category="recon",
        description="Execute Subfinder for passive subdomain enumeration.",
        params=[
            ParamSpec("domain", str, required=True, help_text="The target domain"),
            ParamSpec("silent", bool, default=True, help_text="Run in silent mode"),
            ParamSpec("all_sources", bool, default=False, help_text="Use all sources"),
            ParamSpec("additional_args", str, default="", help_text="Additional Subfinder arguments"),
        ],
        build_command=_subfinder_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="theharvester",
        mcp_tool_name="theharvester_scan",
        endpoint="/api/tools/recon/theharvester",
        category="recon",
        description="Execute TheHarvester for passive information gathering.",
        params=[
            ParamSpec("domain", str, required=True, help_text="The target domain"),
            ParamSpec("additional_args", str, default="", help_text="Additional TheHarvester arguments"),
        ],
        build_command=_theharvester_command,
        use_recovery=True,
    ),
]
