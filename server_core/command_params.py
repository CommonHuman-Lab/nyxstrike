from typing import Any, Dict

def rebuild_command_with_params(tool_name: str, original_command: str, new_params: Dict[str, Any]) -> str:
    """Rebuild command with new parameters"""
    # This is a simplified implementation - in practice, you'd need tool-specific logic
    # For now, we'll just append new parameters
    additional_args = []

    for key, value in new_params.items():
        if key == "timeout" and tool_name in ["nmap", "gobuster", "nuclei"]:
            additional_args.append(f"--timeout {value}")
        elif key == "threads" and tool_name in ["gobuster", "feroxbuster", "ffuf"]:
            additional_args.append(f"-t {value}")
        elif key == "delay" and tool_name in ["gobuster", "feroxbuster"]:
            additional_args.append(f"--delay {value}")
        elif key == "timing" and tool_name == "nmap":
            additional_args.append(f"{value}")
        elif key == "concurrency" and tool_name == "nuclei":
            additional_args.append(f"-c {value}")
        elif key == "rate-limit" and tool_name == "nuclei":
            additional_args.append(f"-rl {value}")

    if additional_args:
        return f"{original_command} {' '.join(additional_args)}"

    return original_command