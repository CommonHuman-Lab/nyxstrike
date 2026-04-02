from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from server_core.workflows.bugbounty.target import BugBountyTarget
from server_core.singletons import bugbounty_manager, fileupload_framework
from server_core.session_flow import create_session, extract_workflow_steps

logger = logging.getLogger(__name__)

api_bugbounty_workflow_bug_bounty_recon_bp = Blueprint("api_bugbounty_workflow_bug_bounty_recon", __name__)


@api_bugbounty_workflow_bug_bounty_recon_bp.route("/api/bugbounty/reconnaissance-workflow", methods=["POST"])
def create_reconnaissance_workflow():
    """Create comprehensive reconnaissance workflow for bug bounty hunting"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        scope = data.get('scope', [])
        out_of_scope = data.get('out_of_scope', [])
        program_type = data.get('program_type', 'web')

        logger.info(f"Creating reconnaissance workflow for {domain}")

        target = BugBountyTarget(
            domain=domain,
            scope=scope,
            out_of_scope=out_of_scope,
            program_type=program_type
        )

        workflow = bugbounty_manager.create_reconnaissance_workflow(target)
        persisted = create_session(
            target=domain,
            steps=extract_workflow_steps(workflow, domain),
            source="mcp_bugbounty",
            objective="reconnaissance",
            metadata={"origin": "api/bugbounty/reconnaissance-workflow"},
        )

        logger.info(f"Reconnaissance workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating reconnaissance workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bugbounty_workflow_bug_bounty_recon_bp.route("/api/bugbounty/vulnerability-hunting-workflow", methods=["POST"])
def create_vulnerability_hunting_workflow():
    """Create vulnerability hunting workflow prioritized by impact"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        priority_vulns = data.get('priority_vulns', ["rce", "sqli", "xss", "idor", "ssrf"])
        bounty_range = data.get('bounty_range', 'unknown')

        logger.info(f"Creating vulnerability hunting workflow for {domain}")

        target = BugBountyTarget(
            domain=domain,
            priority_vulns=priority_vulns,
            bounty_range=bounty_range
        )

        workflow = bugbounty_manager.create_vulnerability_hunting_workflow(target)
        persisted = create_session(
            target=domain,
            steps=extract_workflow_steps(workflow, domain),
            source="mcp_bugbounty",
            objective="vulnerability_hunting",
            metadata={"origin": "api/bugbounty/vulnerability-hunting-workflow"},
        )

        logger.info(f"Vulnerability hunting workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating vulnerability hunting workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bugbounty_workflow_bug_bounty_recon_bp.route("/api/bugbounty/business-logic-workflow", methods=["POST"])
def create_business_logic_workflow():
    """Create business logic testing workflow"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        program_type = data.get('program_type', 'web')

        logger.info(f"Creating business logic testing workflow for {domain}")

        target = BugBountyTarget(domain=domain, program_type=program_type)

        workflow = bugbounty_manager.create_business_logic_testing_workflow(target)
        persisted = create_session(
            target=domain,
            steps=extract_workflow_steps(workflow, domain),
            source="mcp_bugbounty",
            objective="business_logic",
            metadata={"origin": "api/bugbounty/business-logic-workflow"},
        )

        logger.info(f"Business logic testing workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating business logic workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bugbounty_workflow_bug_bounty_recon_bp.route("/api/bugbounty/osint-workflow", methods=["POST"])
def create_osint_workflow():
    """Create OSINT gathering workflow"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']

        logger.info(f"Creating OSINT workflow for {domain}")

        target = BugBountyTarget(domain=domain)

        workflow = bugbounty_manager.create_osint_workflow(target)
        persisted = create_session(
            target=domain,
            steps=extract_workflow_steps(workflow, domain),
            source="mcp_bugbounty",
            objective="osint",
            metadata={"origin": "api/bugbounty/osint-workflow"},
        )

        logger.info(f"OSINT workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating OSINT workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bugbounty_workflow_bug_bounty_recon_bp.route("/api/bugbounty/file-upload-testing", methods=["POST"])
def create_file_upload_testing():
    """Create file upload vulnerability testing workflow"""
    try:
        data = request.get_json()
        if not data or 'target_url' not in data:
            return jsonify({"error": "Target URL is required"}), 400

        target_url = data['target_url']

        logger.info(f"Creating file upload testing workflow for {target_url}")

        workflow = fileupload_framework.create_upload_testing_workflow(target_url)
        test_files = fileupload_framework.generate_test_files()
        workflow["test_files"] = test_files
        persisted = create_session(
            target=target_url,
            steps=extract_workflow_steps(workflow, target_url),
            source="mcp_bugbounty",
            objective="file_upload_testing",
            metadata={"origin": "api/bugbounty/file-upload-testing"},
        )

        logger.info(f"File upload testing workflow created for {target_url}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating file upload testing workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bugbounty_workflow_bug_bounty_recon_bp.route("/api/bugbounty/comprehensive-assessment", methods=["POST"])
def create_comprehensive_bugbounty_assessment():
    """Create comprehensive bug bounty assessment combining all workflows"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        scope = data.get('scope', [])
        priority_vulns = data.get('priority_vulns', ["rce", "sqli", "xss", "idor", "ssrf"])
        include_osint = data.get('include_osint', True)
        include_business_logic = data.get('include_business_logic', True)

        logger.info(f"Creating comprehensive bug bounty assessment for {domain}")

        target = BugBountyTarget(
            domain=domain,
            scope=scope,
            priority_vulns=priority_vulns
        )

        assessment = {
            "target": domain,
            "reconnaissance": bugbounty_manager.create_reconnaissance_workflow(target),
            "vulnerability_hunting": bugbounty_manager.create_vulnerability_hunting_workflow(target)
        }

        if include_osint:
            assessment["osint"] = bugbounty_manager.create_osint_workflow(target)

        if include_business_logic:
            assessment["business_logic"] = bugbounty_manager.create_business_logic_testing_workflow(target)

        total_time = sum(workflow.get("estimated_time", 0) for workflow in assessment.values() if isinstance(workflow, dict))
        total_tools = sum(workflow.get("tools_count", 0) for workflow in assessment.values() if isinstance(workflow, dict))

        assessment["summary"] = {
            "total_estimated_time": total_time,
            "total_tools": total_tools,
            "workflow_count": len([k for k in assessment.keys() if k != "target"]),
            "priority_score": assessment["vulnerability_hunting"].get("priority_score", 0)
        }

        persisted = create_session(
            target=domain,
            steps=extract_workflow_steps(assessment, domain),
            source="mcp_bugbounty",
            objective="comprehensive_assessment",
            metadata={"origin": "api/bugbounty/comprehensive-assessment"},
        )

        logger.info(f"Comprehensive bug bounty assessment created for {domain}")

        return jsonify({
            "success": True,
            "assessment": assessment,
            "session_id": persisted.get("session_id"),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating comprehensive assessment: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
