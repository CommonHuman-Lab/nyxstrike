from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_credential_harvest_vaultrip_bp = Blueprint("api_credential_harvest_vaultrip", __name__)


def _bool(val) -> bool:
    """Coerce UI values to bool. Handles True/False, 'true'/'false', 1/0."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() == "true"
    return bool(val)


@api_credential_harvest_vaultrip_bp.route("/api/tools/vaultrip", methods=["POST"])
def vaultrip():
    """Execute VaultRip credential harvesting sweep."""
    try:
        params = request.json or {}
        target = params.get("target", "~")

        command = f"vaultrip {target}"

        if not _bool(params.get("local", True)):
            command += " --no-local"

        if not _bool(params.get("memory", True)):
            command += " --no-memory"

        if not _bool(params.get("browser", True)):
            command += " --no-browser"

        if not _bool(params.get("system", True)):
            command += " --no-system"

        if not _bool(params.get("kerberos", True)):
            command += " --no-kerberos"

        dump_path = params.get("dump_path", "")
        if dump_path:
            command += f" --dumps {dump_path}"

        target_user = params.get("target_user", "")
        if target_user:
            command += f" --user {target_user}"

        target_pid = params.get("target_pid")
        if target_pid:
            command += f" --pid {int(target_pid)}"

        if _bool(params.get("remote")):
            ssh_host = params.get("ssh_host", "")
            if ssh_host:
                command += f" --remote {ssh_host}"

            ssh_user = params.get("ssh_user", "")
            if ssh_user:
                command += f" --ssh-user {ssh_user}"

            ssh_key = params.get("ssh_key", "")
            if ssh_key:
                command += f" --ssh-key {ssh_key}"

            ssh_password = params.get("ssh_password", "")
            if ssh_password:
                command += f" --ssh-pass {ssh_password!r}"

            ssh_port = params.get("ssh_port", 22)
            if ssh_port and int(ssh_port) != 22:
                command += f" --ssh-port {int(ssh_port)}"

        if _bool(params.get("verbose")):
            command += " -v"

        timeout = params.get("timeout", 30)
        if timeout and int(timeout) != 30:
            command += f" --timeout {int(timeout)}"

        # Active attack modules — explicit opt-in
        if _bool(params.get("dcsync")):
            command += " --dcsync"

        if _bool(params.get("pth")):
            command += " --pth"

        if _bool(params.get("ptt")):
            ptt_ticket = params.get("ptt_ticket", "")
            if ptt_ticket:
                command += f" --ptt --ptt-ticket {ptt_ticket}"

        if _bool(params.get("forge_golden")):
            command += " --forge-golden"

        if _bool(params.get("forge_silver")):
            spn = params.get("forge_silver_spn", "")
            if spn:
                command += f" --forge-silver --forge-silver-spn {spn}"

        dc_host = params.get("dc_host", "")
        if dc_host:
            command += f" --dc {dc_host}"

        ad_domain = params.get("ad_domain", "")
        if ad_domain:
            command += f" --domain {ad_domain}"

        domain_sid = params.get("domain_sid", "")
        if domain_sid:
            command += f" --domain-sid {domain_sid}"

        krbtgt_hash = params.get("krbtgt_hash", "")
        if krbtgt_hash:
            command += f" --krbtgt-hash {krbtgt_hash}"

        attack_user = params.get("attack_user", "")
        if attack_user:
            command += f" --attack-user {attack_user}"

        attack_hash = params.get("attack_hash", "")
        if attack_hash:
            command += f" --attack-hash {attack_hash}"

        attack_cmd = params.get("attack_cmd", "")
        if attack_cmd and attack_cmd != "whoami":
            command += f" --attack-cmd {attack_cmd!r}"

        additional_args = params.get("additional_args", "")
        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting VaultRip sweep: {target}")
        result = execute_command(command)
        # Exit code 1 = findings found (not an error) — treat as success
        if result.get("return_code") == 1:
            result["success"] = True
        logger.info(f"VaultRip sweep completed for {target}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in vaultrip endpoint: {e}")
        return jsonify({"error": f"Server error: {e}"}), 500
