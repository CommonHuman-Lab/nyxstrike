from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from server_core.workflows.ctf.CTFChallenge import CTFChallenge
from server_core.singletons import ctf_coordinator

logger = logging.getLogger(__name__)

api_ctf_team_strategy_bp = Blueprint("api_ctf_team_strategy", __name__)


@api_ctf_team_strategy_bp.route("/api/ctf/team-strategy", methods=["POST"])
def create_ctf_team_strategy():
    """Create optimal team strategy for CTF competition"""
    try:
        params = request.json
        challenges_data = params.get("challenges", [])
        team_skills = params.get("team_skills", {})

        if not challenges_data:
            return jsonify({"error": "Challenges data is required"}), 400

        # Convert challenge data to CTFChallenge objects
        challenges = []
        for challenge_data in challenges_data:
            challenge = CTFChallenge(
                name=challenge_data.get("name", ""),
                category=challenge_data.get("category", "misc"),
                difficulty=challenge_data.get("difficulty", "unknown"),
                points=challenge_data.get("points", 100),
                description=challenge_data.get("description", ""),
                target=challenge_data.get("target", "")
            )
            challenges.append(challenge)

        # Generate team strategy
        strategy = ctf_coordinator.optimize_team_strategy(challenges, team_skills)

        logger.info(f"👥 CTF team strategy created | Challenges: {len(challenges)} | Team members: {len(team_skills)}")
        return jsonify({
            "success": True,
            "strategy": strategy,
            "challenges_count": len(challenges),
            "team_size": len(team_skills),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating CTF team strategy: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
