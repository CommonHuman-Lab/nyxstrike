import logging
import shlex

from flask import jsonify
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

# Explicit allowlist of additional parameters accepted from callers.
# Maps kwarg name → (cli_flag, is_boolean)
_ALLOWED_EXTRA_FLAGS = {
    "limit":   ("-l",    False),
    "timeout": ("-t",    False),
    "verbose": ("-v",    True),
    "no_subs": ("-subs", True),
}


_VALID_MODES = {"U", "R", "B"}


def run_waymore(input, mode='U', output_urls=None, output_responses=None, **kwargs):
    """
    Run the waymore tool with given parameters.
    """
    if mode not in _VALID_MODES:
        return {"success": False, "error": f"Invalid mode: must be one of {sorted(_VALID_MODES)}"}

    try:
        cmd = ["waymore", "-i", input, "-mode", mode]

        if output_urls:
            cmd.extend(["-oU", output_urls])
        if output_responses:
            cmd.extend(["-oR", output_responses])

        for key, value in kwargs.items():
            if key not in _ALLOWED_EXTRA_FLAGS:
                logger.warning(f"Ignoring unsupported waymore parameter: {key!r}")
                continue
            flag, is_bool = _ALLOWED_EXTRA_FLAGS[key]
            if is_bool:
                if value:
                    cmd.append(flag)
            elif value:
                cmd.extend([flag, str(value)])

        logger.info(f"Executing Waymore: {' '.join(shlex.quote(arg) for arg in cmd)}")

        command = " ".join(shlex.quote(arg) for arg in cmd)
        result = execute_command(command)
        logger.info(f"✅ Waymore execution completed for input: {input}")
        return jsonify(result)
 
    except Exception as e:
        logger.error(f"Error running Waymore: {str(e)}")
        return {"error": str(e)}
