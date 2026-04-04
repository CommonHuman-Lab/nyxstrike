from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from server_core.workflows.ctf.CTFChallenge import CTFChallenge
from server_core.singletons import ctf_manager
from server_core.session_flow import create_session, extract_workflow_steps

logger = logging.getLogger(__name__)

api_ctf_create_challenge_workflow_bp = Blueprint("api_ctf_create_challenge_workflow", __name__)


@api_ctf_create_challenge_workflow_bp.route("/api/ctf/create-challenge-workflow", methods=["POST"])
def create_ctf_challenge_workflow():
    """Create specialized workflow for CTF challenge"""
    try:
        params = request.json
        challenge_name = params.get("name", "")
        category = params.get("category", "misc")
        difficulty = params.get("difficulty", "unknown")
        points = params.get("points", 100)
        description = params.get("description", "")
        target = params.get("target", "")

        if not challenge_name:
            return jsonify({"error": "Challenge name is required"}), 400

        # Create CTF challenge object
        challenge = CTFChallenge(
            name=challenge_name,
            category=category,
            difficulty=difficulty,
            points=points,
            description=description,
            target=target
        )

        # Generate workflow
        workflow = ctf_manager.create_ctf_challenge_workflow(challenge)
        persisted = create_session(
            target=target or challenge_name,
            steps=extract_workflow_steps(workflow, target or challenge_name),
            source="mcp_ctf",
            objective="ctf",
            metadata={
                "origin": "api/ctf/create-challenge-workflow",
                "challenge": challenge_name,
                "category": category,
                "difficulty": difficulty,
            },
        )

        logger.info(f"🎯 CTF workflow created for {challenge_name} | Category: {category} | Difficulty: {difficulty}")
        return jsonify({
            "success": True,
            "workflow": workflow,
            "challenge": vars(challenge),
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating CTF workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
