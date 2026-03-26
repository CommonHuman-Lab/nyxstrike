from flask import Blueprint, request, jsonify
import logging
import re
import shlex
import subprocess
from functools import lru_cache

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_tools_impacket_bp = Blueprint("api_tools_impacket", __name__)

# Kali impacket-scripts binaries from the package page
IMPACKET_SCRIPTS = {
    "DumpNTLMInfo",
    "Get-GPPPassword",
    "GetADComputers",
    "GetADUsers",
    "GetLAPSPassword",
    "GetNPUsers",
    "GetUserSPNs",
    "addcomputer",
    "atexec",
    "changepasswd",
    "dacledit",
    "dcomexec",
    "describeTicket",
    "dpapi",
    "esentutl",
    "exchanger",
    "findDelegation",
    "getArch",
    "getPac",
    "getST",
    "getTGT",
    "goldenPac",
    "karmaSMB",
    "keylistattack",
    "lookupsid",
    "machine_role",
    "mimikatz",
    "mqtt_check",
    "mssqlclient",
    "mssqlinstance",
    "net",
    "ntfs-read",
    "ntlmrelayx",
    "owneredit",
    "ping",
    "ping6",
    "psexec",
    "raiseChild",
    "rbcd",
    "rdp_check",
    "reg",
    "registry-read",
    "rpcmap",
    "sambaPipe",
    "services",
    "smbclient",
    "smbexec",
    "smbserver",
    "sniff",
    "sniffer",
    "split",
    "ticketConverter",
    "ticketer",
    "tstool",
    "wmipersist",
    "wmiquery",
}


def _script_binary(script_name: str) -> str:
    return f"impacket-{script_name}"


def _binary_exists(binary_name: str) -> bool:
    return subprocess.call(
        ["bash", "-lc", f"command -v {shlex.quote(binary_name)} >/dev/null 2>&1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0


def _normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _extract_usage_block(help_text: str) -> str:
    lines = help_text.splitlines()
    usage_lines = []
    capture = False

    for line in lines:
        stripped = line.rstrip()

        if stripped.lower().startswith("usage:"):
            capture = True
            usage_lines.append(stripped)
            continue

        if capture:
            if not stripped:
                break
            # continuation lines in argparse help are typically indented
            if line.startswith(" ") or line.startswith("\t"):
                usage_lines.append(stripped)
            else:
                break

    return " ".join(usage_lines)


def _tokenize_usage(usage: str):
    """
    Tokenize usage while preserving [...] groups enough to detect required
    vs optional chunks. This is intentionally simple and robust rather than perfect.
    """
    if not usage:
        return []

    # remove leading "usage:"
    usage = re.sub(r"^\s*usage:\s*", "", usage, flags=re.IGNORECASE).strip()

    tokens = []
    current = []
    bracket_depth = 0

    for ch in usage:
        if ch == "[":
            bracket_depth += 1
            current.append(ch)
        elif ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
            current.append(ch)
        elif ch.isspace() and bracket_depth == 0:
            if current:
                tokens.append("".join(current).strip())
                current = []
        else:
            current.append(ch)

    if current:
        tokens.append("".join(current).strip())

    return tokens


def _extract_required_positionals(usage: str, binary_name: str):
    """
    Detect required positional args from usage.
    Anything outside [] that doesn't start with '-' and isn't the script name
    is treated as required positional.
    """
    tokens = _tokenize_usage(usage)
    required = []

    for token in tokens:
        clean = token.strip()

        if clean == binary_name or clean.endswith(f"/{binary_name}"):
            continue

        if clean.startswith("[") and clean.endswith("]"):
            continue

        if clean.startswith("-"):
            continue

        # skip obvious argparse metavariable groupings if wrapped strangely
        if "[" in clean or "]" in clean:
            continue

        required.append(clean)

    return required


def _parse_option_line(option_line: str):
    """
    Parse lines like:
      -k                    Use Kerberos authentication
      -dc-ip ip address     IP Address of the domain controller
      -outputfile, -o OUTPUTFILE
    Returns a list of option names and whether a value is expected.
    """
    left = re.split(r"\s{2,}", option_line.strip(), maxsplit=1)[0]
    parts = [p.strip() for p in left.split(",")]

    names = []
    takes_value = False

    for part in parts:
        if not part:
            continue

        match = re.match(r"^(-{1,2}[A-Za-z0-9][A-Za-z0-9_-]*)(?:\s+(.+))?$", part)
        if match:
            name = match.group(1)
            metavar = match.group(2)
            names.append(name.lstrip("-"))
            if metavar and not metavar.startswith("-"):
                takes_value = True

    return names, takes_value


def _extract_options(help_text: str):
    """
    Parse argparse-style option lines.
    """
    options = {}
    lines = help_text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue

        names, takes_value = _parse_option_line(stripped)
        for name in names:
            options[name] = {
                "takes_value": takes_value
            }

    return options


@lru_cache(maxsize=256)
def get_impacket_script_spec(script_name: str):
    if script_name not in IMPACKET_SCRIPTS:
        raise ValueError(f"Unsupported Impacket script: {script_name}")

    binary_name = _script_binary(script_name)

    if not _binary_exists(binary_name):
        raise FileNotFoundError(f"{binary_name} is not installed or not in PATH")

    proc = subprocess.run(
        [binary_name, "-h"],
        capture_output=True,
        text=True,
        timeout=15
    )

    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    help_text = help_text.strip()

    if not help_text:
        raise RuntimeError(f"Could not read help output from {binary_name}")

    usage = _extract_usage_block(help_text)
    required_positionals = _extract_required_positionals(usage, binary_name)
    options = _extract_options(help_text)

    return {
        "script": script_name,
        "binary": binary_name,
        "usage": usage,
        "required_positionals": required_positionals,
        "options": options,
        "raw_help": help_text,
    }


def _append_option(argv: list[str], key: str, value, spec_options: dict):
    if key not in spec_options:
        raise ValueError(f"Unsupported option for this script: {key}")

    option_meta = spec_options[key]
    flag = f"-{key}" if len(key) == 1 else f"-{key}"

    if option_meta["takes_value"]:
        if value is None or value == "":
            raise ValueError(f"Option '{key}' requires a value")
        if isinstance(value, list):
            for item in value:
                argv.extend([flag, str(item)])
        else:
            argv.extend([flag, str(value)])
    else:
        if _normalize_bool(value):
            argv.append(flag)


def _build_impacket_command(script_name: str, payload: dict):
    spec = get_impacket_script_spec(script_name)
    argv = [spec["binary"]]

    # Accept either:
    # 1. target at top-level
    # 2. positional list
    # 3. positional_map for named positionals
    target = payload.get("target")
    positional = payload.get("positional", [])
    positional_map = payload.get("positional_map", {})
    options = payload.get("options", {})
    extra_args = payload.get("extra_args", "")

    required_positionals = spec["required_positionals"][:]

    # Convenience: if script requires target and top-level target is supplied
    built_positionals = []

    for pos_name in required_positionals:
        if pos_name == "target":
            if target:
                built_positionals.append(str(target))
            elif pos_name in positional_map:
                built_positionals.append(str(positional_map[pos_name]))
            else:
                raise ValueError("Missing required positional argument: target")
        else:
            if pos_name in positional_map:
                built_positionals.append(str(positional_map[pos_name]))
            elif positional:
                built_positionals.append(str(positional.pop(0)))
            else:
                raise ValueError(f"Missing required positional argument: {pos_name}")

    # options first, then positionals is okay for argparse in most cases,
    # but keep positionals last to match common CLI expectations
    for key, value in options.items():
        _append_option(argv, key, value, spec["options"])

    argv.extend(built_positionals)

    if extra_args:
        argv.extend(shlex.split(extra_args))

    return argv, spec


@api_tools_impacket_bp.route("/api/tool/active_directory/impacket", methods=["POST"])
def run_impacket():
    """
    Generic Impacket wrapper with per-script validation.

    Example:
    {
      "script": "GetADUsers",
      "target": "corp.local/user:pass",
      "options": {
        "dc-ip": "10.10.10.1",
        "all": true,
        "debug": true
      }
    }
    """
    try:
        payload = request.get_json(silent=True) or {}
        script_name = payload.get("script", "").strip()

        if not script_name:
            return jsonify({"error": "script parameter is required"}), 400

        if script_name not in IMPACKET_SCRIPTS:
            return jsonify({
                "error": f"Unsupported Impacket script: {script_name}",
                "supported_scripts": sorted(IMPACKET_SCRIPTS),
            }), 400

        argv, spec = _build_impacket_command(script_name, payload)
        command = shlex.join(argv)

        logger.info("Starting Impacket script %s", script_name)
        logger.debug("Impacket command: %s", command)

        result = execute_command(command)

        logger.info("Completed Impacket script %s", script_name)

        # Helpful metadata for frontend / debugging
        if isinstance(result, dict):
            result.setdefault("meta", {})
            result["meta"]["script"] = script_name
            result["meta"]["binary"] = spec["binary"]
            result["meta"]["usage"] = spec["usage"]
            result["meta"]["required_positionals"] = spec["required_positionals"]

        return jsonify(result)

    except FileNotFoundError as e:
        logger.error("Impacket binary missing: %s", str(e))
        return jsonify({"error": str(e)}), 500

    except ValueError as e:
        logger.warning("Impacket validation error: %s", str(e))
        return jsonify({"error": str(e)}), 400

    except subprocess.TimeoutExpired:
        logger.error("Timed out while introspecting Impacket help output")
        return jsonify({"error": "Timed out while reading Impacket script help output"}), 500

    except Exception as e:
        logger.exception("Error in Impacket endpoint")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_tools_impacket_bp.route("/api/tool/active_directory/impacket/spec", methods=["POST"])
def get_impacket_spec():
    """
    Helper endpoint so UI/agent can discover required args for a script.
    """
    try:
        payload = request.get_json(silent=True) or {}
        script_name = payload.get("script", "").strip()

        spec = get_impacket_script_spec(script_name)
        return jsonify({
            "script": spec["script"],
            "binary": spec["binary"],
            "usage": spec["usage"],
            "required_positionals": spec["required_positionals"],
            "options": spec["options"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400