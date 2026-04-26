ssh_tool = {
    "name": "ssh",
    "description": "SSH client tool (metadata only)",
    "parameters": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "Target host to connect to"
            },
            "port": {
                "type": "integer",
                "description": "SSH port",
                "default": 22
            },
            "username": {
                "type": "string",
                "description": "SSH username"
            }
        },
        "required": ["host"]
    }
}

async def run(params):
    # MCP tools do NOT execute system commands.
    # This is a safe placeholder response.
    return {
        "status": "info",
        "message": (
            "SSH tool registered. "
            "Execution must be handled by an external safe backend or UI component."
        ),
        "received": params
    }
