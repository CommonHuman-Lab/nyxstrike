from flask import Blueprint, jsonify
import logging

from tool_registry import TOOLS
from server_core.singletons import tool_stats

logger = logging.getLogger(__name__)

api_tools_catalog_bp = Blueprint("api_tools_catalog", __name__)


@api_tools_catalog_bp.route("/api/tools", methods=["GET"])
def get_tools():
    """Return the full tool catalog with metadata."""
    tools = []
    for name, meta in TOOLS.items():
        baseline = meta.get("effectiveness", 0.0)
        stats = tool_stats.get_stats(name)
        effective = tool_stats.blended_effectiveness(name, baseline)
        tools.append({
            "name": name,
            "desc": meta.get("desc", ""),
            "category": meta.get("category", ""),
            "endpoint": meta.get("endpoint", ""),
            "method": meta.get("method", "POST"),
            "params": meta.get("params", {}),
            "optional": meta.get("optional", {}),
            "effectiveness": effective,
            "effectiveness_runs": stats["runs"],
            "effectiveness_live": stats["runs"] >= 5,
            "parent_tool": meta.get("parent_tool", None),
        })

    categories = sorted({t["category"] for t in tools})

    return jsonify({
        "success": True,
        "total": len(tools),
        "categories": categories,
        "tools": tools,
    })
