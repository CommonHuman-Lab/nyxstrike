# mcp_tools/intelligent_decision_engine.py

from typing import Dict, Any
from datetime import datetime
import asyncio
import json

def register_intelligent_decision_engine_tools(mcp, api_client, logger, CliColors):
    @mcp.tool()
    async def analyze_target_intelligence(target: str) -> Dict[str, Any]:
        """
        Analyze target using AI-powered intelligence to create comprehensive profile.

        Args:
            target: Target URL, IP address, or domain to analyze

        Returns:
            Comprehensive target profile with technology detection, risk assessment, and recommendations
        """
        logger.info(f"🧠 Analyzing target intelligence for: {target}")

        data = {"target": target}
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/analyze-target", data)
        )

        if result.get("success"):
            profile = result.get("target_profile", {})
            logger.info(f"✅ Target analysis completed - Type: {profile.get('target_type')}, Risk: {profile.get('risk_level')}")
        else:
            logger.error(f"❌ Target analysis failed for {target}")

        return result

    @mcp.tool()
    async def select_optimal_tools_ai(target: str, objective: str = "comprehensive") -> Dict[str, Any]:
        """
        Use AI to select optimal security tools based on target analysis and testing objective.

        Args:
            target: Target to analyze
            objective: Testing objective - "comprehensive", "quick", or "stealth"

        Returns:
            AI-selected optimal tools with effectiveness ratings and target profile
        """
        logger.info(f"🎯 Selecting optimal tools for {target} with objective: {objective}")

        data = {
            "target": target,
            "objective": objective
        }
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/select-tools", data)
        )

        if result.get("success"):
            tools = result.get("selected_tools", [])
            logger.info(f"✅ AI selected {len(tools)} optimal tools: {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}")
        else:
            logger.error(f"❌ Tool selection failed for {target}")

        return result

    @mcp.tool()
    async def optimize_tool_parameters_ai(target: str, tool: str, context: str = "{}") -> Dict[str, Any]:
        """
        Use AI to optimize tool parameters based on target profile and context.

        Args:
            target: Target to test
            tool: Security tool to optimize
            context: JSON string with additional context (stealth, aggressive, etc.)

        Returns:
            AI-optimized parameters for maximum effectiveness
        """
        import json

        logger.info(f"⚙️  Optimizing parameters for {tool} against {target}")

        try:
            context_dict = json.loads(context) if context != "{}" else {}
        except (json.JSONDecodeError, ValueError):
            context_dict = {}

        data = {
            "target": target,
            "tool": tool,
            "context": context_dict
        }
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/optimize-parameters", data)
        )

        if result.get("success"):
            params = result.get("optimized_parameters", {})
            logger.info(f"✅ Parameters optimized for {tool} - {len(params)} parameters configured")
        else:
            logger.error(f"❌ Parameter optimization failed for {tool}")

        return result

    @mcp.tool()
    async def preview_attack_chain_ai(target: str, objective: str = "comprehensive") -> Dict[str, Any]:
        """
        Preview an intelligent attack chain without persisting a session.

        Args:
            target: Target for the attack chain
            objective: Attack objective - "comprehensive", "quick", or "stealth"

        Returns:
            AI-generated attack chain preview with success probability and time estimates
        """
        logger.info(f"🧪 Previewing AI-driven attack chain for {target}")

        data = {
            "target": target,
            "objective": objective,
        }
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/preview-attack-chain", data)
        )

        if result.get("success"):
            chain = result.get("attack_chain", {})
            steps = len(chain.get("steps", []))
            logger.info(f"✅ Attack chain preview generated - {steps} steps (not persisted)")
        else:
            logger.error(f"❌ Attack chain preview failed for {target}")

        return result

    @mcp.tool()
    async def create_attack_chain_ai(target: str, objective: str = "comprehensive") -> Dict[str, Any]:
        """
        Create an intelligent attack chain using AI-driven tool sequencing and optimization.

        Args:
            target: Target for the attack chain
            objective: Attack objective - "comprehensive", "quick", or "stealth"

        Returns:
            AI-generated attack chain with success probability and time estimates
        """
        logger.info(f"⚔️  Creating AI-driven attack chain for {target}")

        data = {
            "target": target,
            "objective": objective
        }
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/create-attack-chain", data)
        )

        if result.get("success"):
            chain = result.get("attack_chain", {})
            steps = len(chain.get("steps", []))
            success_prob = chain.get("success_probability", 0)
            estimated_time = chain.get("estimated_time", 0)
            session_id = result.get("session_id")

            logger.info(
                f"✅ Attack chain created - {steps} steps, {success_prob:.2f} success probability, ~{estimated_time}s, session={session_id}"
            )
        else:
            logger.error(f"❌ Attack chain creation failed for {target}")

        return result

    @mcp.tool()
    async def intelligent_smart_scan(target: str, objective: str = "comprehensive", max_tools: int = 5) -> Dict[str, Any]:
        """
        Execute an intelligent scan using AI-driven tool selection and parameter optimization.

        Args:
            target: Target to scan
            objective: Scanning objective - "comprehensive", "quick", or "stealth"
            max_tools: Maximum number of tools to use

        Returns:
            Results from AI-optimized scanning with tool execution summary
        """
        logger.info(f"{CliColors.FIRE_RED}🚀 Starting intelligent smart scan for {target}{CliColors.RESET}")

        data = {
            "target": target,
            "objective": objective,
            "max_tools": max_tools
        }
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/smart-scan", data)
        )

        if result.get("success"):
            scan_results = result.get("scan_results", {})
            tools_executed = scan_results.get("tools_executed", [])
            execution_summary = scan_results.get("execution_summary", {})

            # Enhanced logging with detailed results
            logger.info(f"{CliColors.SUCCESS}✅ Intelligent scan completed for {target}{CliColors.RESET}")
            logger.info(f"{CliColors.CYBER_ORANGE}📊 Execution Summary:{CliColors.RESET}")
            logger.info(f"   • Tools executed: {execution_summary.get('successful_tools', 0)}/{execution_summary.get('total_tools', 0)}")
            logger.info(f"   • Success rate: {execution_summary.get('success_rate', 0):.1f}%")
            logger.info(f"   • Total vulnerabilities: {scan_results.get('total_vulnerabilities', 0)}")
            logger.info(f"   • Execution time: {execution_summary.get('total_execution_time', 0):.2f}s")

            # Log successful tools
            successful_tools = [t['tool'] for t in tools_executed if t.get('success')]
            if successful_tools:
                logger.info(f"{CliColors.HIGHLIGHT_GREEN} Successful tools: {', '.join(successful_tools)} {CliColors.RESET}")

            # Log failed tools
            failed_tools = [t['tool'] for t in tools_executed if not t.get('success')]
            if failed_tools:
                logger.warning(f"{CliColors.HIGHLIGHT_RED} Failed tools: {', '.join(failed_tools)} {CliColors.RESET}")

            # Log vulnerabilities found
            if scan_results.get('total_vulnerabilities', 0) > 0:
                logger.warning(f"{CliColors.VULN_HIGH}🚨 {scan_results['total_vulnerabilities']} vulnerabilities detected!{CliColors.RESET}")
        else:
            logger.error(f"{CliColors.ERROR}❌ Intelligent scan failed for {target}: {result.get('error', 'Unknown error')}{CliColors.RESET}")

        return result

    @mcp.tool()
    async def detect_technologies_ai(target: str) -> Dict[str, Any]:
        """
        Use AI to detect technologies and provide technology-specific testing recommendations.

        Args:
            target: Target to analyze for technology detection

        Returns:
            Detected technologies with AI-generated testing recommendations
        """
        logger.info(f"🔍 Detecting technologies for {target}")

        data = {"target": target}
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/technology-detection", data)
        )

        if result.get("success"):
            technologies = result.get("detected_technologies", [])
            cms = result.get("cms_type")
            recommendations = result.get("technology_recommendations", {})

            tech_info = f"Technologies: {', '.join(technologies)}"
            if cms:
                tech_info += f", CMS: {cms}"

            logger.info(f"✅ Technology detection completed - {tech_info}")
            logger.info(f"📋 Generated {len(recommendations)} technology-specific recommendations")
        else:
            logger.error(f"❌ Technology detection failed for {target}")

        return result

    @mcp.tool()
    async def ai_reconnaissance_workflow(target: str, depth: str = "standard") -> Dict[str, Any]:
        """
        Execute AI-driven reconnaissance workflow with intelligent tool chaining.

        Args:
            target: Target for reconnaissance
            depth: Reconnaissance depth - "surface", "standard", or "deep"

        Returns:
            Comprehensive reconnaissance results with AI-driven insights
        """
        logger.info(f"🕵️  Starting AI reconnaissance workflow for {target} (depth: {depth})")

        # First analyze the target
        loop = asyncio.get_running_loop()
        analysis_result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/analyze-target", {"target": target})
        )

        if not analysis_result.get("success"):
            return analysis_result

        # Create attack chain for reconnaissance
        objective = "comprehensive" if depth == "deep" else "quick" if depth == "surface" else "comprehensive"
        loop = asyncio.get_running_loop()
        chain_result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/create-attack-chain", {
            "target": target,
            "objective": objective
        })
        )

        if not chain_result.get("success"):
            return chain_result

        # Execute the reconnaissance
        loop = asyncio.get_running_loop()
        scan_result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/smart-scan", {
            "target": target,
            "objective": objective,
            "max_tools": 8 if depth == "deep" else 3 if depth == "surface" else 5
        })
        )

        logger.info(f"✅ AI reconnaissance workflow completed for {target}")

        return {
            "success": True,
            "target": target,
            "depth": depth,
            "target_analysis": analysis_result.get("target_profile", {}),
            "attack_chain": chain_result.get("attack_chain", {}),
            "scan_results": scan_result.get("scan_results", {}),
            "timestamp": datetime.now().isoformat()
        }

    @mcp.tool()
    async def ai_vulnerability_assessment(target: str, focus_areas: str = "all") -> Dict[str, Any]:
        """
        Perform AI-driven vulnerability assessment with intelligent prioritization.

        Args:
            target: Target for vulnerability assessment
            focus_areas: Comma-separated focus areas - "web", "network", "api", "all"

        Returns:
            Prioritized vulnerability assessment results with AI insights
        """
        logger.info(f"🔬 Starting AI vulnerability assessment for {target}")

        # Analyze target first
        loop = asyncio.get_running_loop()
        analysis_result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/analyze-target", {"target": target})
        )

        if not analysis_result.get("success"):
            return analysis_result

        profile = analysis_result.get("target_profile", {})
        target_type = profile.get("target_type", "unknown")

        # Select tools based on focus areas and target type
        if focus_areas == "all":
            objective = "comprehensive"
        elif "web" in focus_areas and target_type == "web_application":
            objective = "comprehensive"
        elif "network" in focus_areas and target_type == "network_host":
            objective = "comprehensive"
        else:
            objective = "quick"

        # Execute vulnerability assessment
        loop = asyncio.get_running_loop()
        scan_result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/intelligence/smart-scan", {
            "target": target,
            "objective": objective,
            "max_tools": 6
        })
        )

        logger.info(f"✅ AI vulnerability assessment completed for {target}")

        return {
            "success": True,
            "target": target,
            "focus_areas": focus_areas,
            "target_analysis": profile,
            "vulnerability_scan": scan_result.get("scan_results", {}),
            "risk_assessment": {
                "risk_level": profile.get("risk_level", "unknown"),
                "attack_surface_score": profile.get("attack_surface_score", 0),
                "confidence_score": profile.get("confidence_score", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
