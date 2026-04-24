# mcp_tools/bugbounty_workflow/bug_bounty_recon.py

from typing import Dict, Any
from datetime import datetime
import asyncio

def register_bug_bounty_recon_tools(mcp, api_client, logger):

    @mcp.tool()
    async def bugbounty_reconnaissance_workflow(domain: str, scope: str = "", out_of_scope: str = "",
                                        program_type: str = "web") -> Dict[str, Any]:
        """
        Create comprehensive reconnaissance workflow for bug bounty hunting.

        Args:
            domain: Target domain for bug bounty
            scope: Comma-separated list of in-scope domains/IPs
            out_of_scope: Comma-separated list of out-of-scope domains/IPs
            program_type: Type of program (web, api, mobile, iot)

        Returns:
            Comprehensive reconnaissance workflow with phases and tools
        """
        data = {
            "domain": domain,
            "scope": scope.split(",") if scope else [],
            "out_of_scope": out_of_scope.split(",") if out_of_scope else [],
            "program_type": program_type
        }

        logger.info(f"🎯 Creating reconnaissance workflow for {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/bugbounty/reconnaissance-workflow", data)
        )

        if result.get("success"):
            workflow = result.get("workflow", {})
            logger.info(f"✅ Reconnaissance workflow created - {workflow.get('tools_count', 0)} tools, ~{workflow.get('estimated_time', 0)}s")
        else:
            logger.error(f"❌ Failed to create reconnaissance workflow for {domain}")

        return result

    @mcp.tool()
    async def bugbounty_vulnerability_hunting(domain: str, priority_vulns: str = "rce,sqli,xss,idor,ssrf",
                                       bounty_range: str = "unknown") -> Dict[str, Any]:
        """
        Create vulnerability hunting workflow prioritized by impact and bounty potential.

        Args:
            domain: Target domain for bug bounty
            priority_vulns: Comma-separated list of priority vulnerability types
            bounty_range: Expected bounty range (low, medium, high, critical)

        Returns:
            Vulnerability hunting workflow prioritized by impact
        """
        data = {
            "domain": domain,
            "priority_vulns": priority_vulns.split(",") if priority_vulns else [],
            "bounty_range": bounty_range
        }

        logger.info(f"🎯 Creating vulnerability hunting workflow for {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/bugbounty/vulnerability-hunting-workflow", data)
        )

        if result.get("success"):
            workflow = result.get("workflow", {})
            logger.info(f"✅ Vulnerability hunting workflow created - Priority score: {workflow.get('priority_score', 0)}")
        else:
            logger.error(f"❌ Failed to create vulnerability hunting workflow for {domain}")

        return result

    @mcp.tool()
    async def bugbounty_business_logic_testing(domain: str, program_type: str = "web") -> Dict[str, Any]:
        """
        Create business logic testing workflow for advanced bug bounty hunting.

        Args:
            domain: Target domain for bug bounty
            program_type: Type of program (web, api, mobile)

        Returns:
            Business logic testing workflow with manual and automated tests
        """
        data = {
            "domain": domain,
            "program_type": program_type
        }

        logger.info(f"🎯 Creating business logic testing workflow for {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/bugbounty/business-logic-workflow", data)
        )

        if result.get("success"):
            workflow = result.get("workflow", {})
            test_count = sum(len(category["tests"]) for category in workflow.get("business_logic_tests", []))
            logger.info(f"✅ Business logic testing workflow created - {test_count} tests")
        else:
            logger.error(f"❌ Failed to create business logic testing workflow for {domain}")

        return result

    @mcp.tool()
    async def bugbounty_osint_gathering(domain: str) -> Dict[str, Any]:
        """
        Create OSINT (Open Source Intelligence) gathering workflow for bug bounty reconnaissance.

        Args:
            domain: Target domain for OSINT gathering

        Returns:
            OSINT gathering workflow with multiple intelligence phases
        """
        data = {"domain": domain}

        logger.info(f"🎯 Creating OSINT gathering workflow for {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/bugbounty/osint-workflow", data)
        )

        if result.get("success"):
            workflow = result.get("workflow", {})
            phases = len(workflow.get("osint_phases", []))
            logger.info(f"✅ OSINT workflow created - {phases} intelligence phases")
        else:
            logger.error(f"❌ Failed to create OSINT workflow for {domain}")

        return result

    @mcp.tool()
    async def bugbounty_file_upload_testing(target_url: str) -> Dict[str, Any]:
        """
        Create file upload vulnerability testing workflow with bypass techniques.

        Args:
            target_url: Target URL with file upload functionality

        Returns:
            File upload testing workflow with malicious files and bypass techniques
        """
        data = {"target_url": target_url}

        logger.info(f"🎯 Creating file upload testing workflow for {target_url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/bugbounty/file-upload-testing", data)
        )

        if result.get("success"):
            workflow = result.get("workflow", {})
            phases = len(workflow.get("test_phases", []))
            logger.info(f"✅ File upload testing workflow created - {phases} test phases")
        else:
            logger.error(f"❌ Failed to create file upload testing workflow for {target_url}")

        return result

    @mcp.tool()
    async def bugbounty_comprehensive_assessment(domain: str, scope: str = "",
                                         priority_vulns: str = "rce,sqli,xss,idor,ssrf",
                                         include_osint: bool = True,
                                         include_business_logic: bool = True) -> Dict[str, Any]:
        """
        Create comprehensive bug bounty assessment combining all specialized workflows.

        Args:
            domain: Target domain for bug bounty
            scope: Comma-separated list of in-scope domains/IPs
            priority_vulns: Comma-separated list of priority vulnerability types
            include_osint: Include OSINT gathering workflow
            include_business_logic: Include business logic testing workflow

        Returns:
            Comprehensive bug bounty assessment with all workflows and summary
        """
        data = {
            "domain": domain,
            "scope": scope.split(",") if scope else [],
            "priority_vulns": priority_vulns.split(",") if priority_vulns else [],
            "include_osint": include_osint,
            "include_business_logic": include_business_logic
        }

        logger.info(f"🎯 Creating comprehensive bug bounty assessment for {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/bugbounty/comprehensive-assessment", data)
        )

        if result.get("success"):
            assessment = result.get("assessment", {})
            summary = assessment.get("summary", {})
            logger.info(f"✅ Comprehensive assessment created - {summary.get('workflow_count', 0)} workflows, ~{summary.get('total_estimated_time', 0)}s")
        else:
            logger.error(f"❌ Failed to create comprehensive assessment for {domain}")

        return result

    @mcp.tool()
    async def bugbounty_authentication_bypass_testing(target_url: str, auth_type: str = "form") -> Dict[str, Any]:
        """
        Create authentication bypass testing workflow for bug bounty hunting.

        Args:
            target_url: Target URL with authentication
            auth_type: Type of authentication (form, jwt, oauth, saml)

        Returns:
            Authentication bypass testing strategies and techniques
        """
        bypass_techniques = {
            "form": [
                {"technique": "SQL Injection", "payloads": ["admin'--", "' OR '1'='1'--"]},
                {"technique": "Default Credentials", "payloads": ["admin:admin", "admin:password"]},
                {"technique": "Password Reset", "description": "Test password reset token reuse and manipulation"},
                {"technique": "Session Fixation", "description": "Test session ID prediction and fixation"}
            ],
            "jwt": [
                {"technique": "Algorithm Confusion", "description": "Change RS256 to HS256"},
                {"technique": "None Algorithm", "description": "Set algorithm to 'none'"},
                {"technique": "Key Confusion", "description": "Use public key as HMAC secret"},
                {"technique": "Token Manipulation", "description": "Modify claims and resign token"}
            ],
            "oauth": [
                {"technique": "Redirect URI Manipulation", "description": "Test open redirect in redirect_uri"},
                {"technique": "State Parameter", "description": "Test CSRF via missing/weak state parameter"},
                {"technique": "Code Reuse", "description": "Test authorization code reuse"},
                {"technique": "Client Secret", "description": "Test for exposed client secrets"}
            ],
            "saml": [
                {"technique": "XML Signature Wrapping", "description": "Manipulate SAML assertions"},
                {"technique": "XML External Entity", "description": "Test XXE in SAML requests"},
                {"technique": "Replay Attacks", "description": "Test assertion replay"},
                {"technique": "Signature Bypass", "description": "Test signature validation bypass"}
            ]
        }

        workflow = {
            "target": target_url,
            "auth_type": auth_type,
            "bypass_techniques": bypass_techniques.get(auth_type, []),
            "testing_phases": [
                {"phase": "reconnaissance", "description": "Identify authentication mechanisms"},
                {"phase": "baseline_testing", "description": "Test normal authentication flow"},
                {"phase": "bypass_testing", "description": "Apply bypass techniques"},
                {"phase": "privilege_escalation", "description": "Test for privilege escalation"}
            ],
            "estimated_time": 240,
            "manual_testing_required": True
        }

        logger.info(f"🎯 Created authentication bypass testing workflow for {target_url}")

        return {
            "success": True,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        }
