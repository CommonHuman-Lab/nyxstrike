"""
Shared Flask route decorators for API blueprints.
"""

import functools
from flask import request, jsonify


def require_json(f):
    """
    Decorator that returns HTTP 400 when the request body is missing or
    not valid JSON (e.g. wrong Content-Type or empty body), instead of
    letting ``request.json`` return ``None`` and causing an AttributeError.

    Usage::

        from server_core.decorators import require_json

        @bp.route("/api/tools/mytool", methods=["POST"])
        @require_json
        def mytool():
            params = request.json
            ...
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if request.json is None:
            return jsonify({
                "error": "Request body must be valid JSON with Content-Type: application/json",
                "success": False,
            }), 400
        return f(*args, **kwargs)
    return wrapper
