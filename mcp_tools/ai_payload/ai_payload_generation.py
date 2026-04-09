# mcp_tools/ai_payload_generation.py

from typing import Dict, Any
import time
import asyncio

def register_ai_payload_generation_tools(mcp, api_client, logger):
    @mcp.tool()
    async def ai_generate_payload(attack_type: str, complexity: str = "basic", technology: str = "", url: str = "") -> Dict[str, Any]:
        """
        Generate AI-powered contextual payloads for security testing.

        Args:
            attack_type: Type of attack (xss, sqli, lfi, cmd_injection, ssti, xxe)
            complexity: Complexity level (basic, advanced, bypass)
            technology: Target technology (php, asp, jsp, python, nodejs)
            url: Target URL for context

        Returns:
            Contextual payloads with risk assessment and test cases
        """
        data = {
            "attack_type": attack_type,
            "complexity": complexity,
            "technology": technology,
            "url": url
        }
        logger.info(f"🤖 Generating AI payloads for {attack_type} attack")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/ai/generate_payload", data)
        )

        if result.get("success"):
            payload_data = result.get("ai_payload_generation", {})
            count = payload_data.get("payload_count", 0)
            logger.info(f"✅ Generated {count} contextual {attack_type} payloads")

            # Log some example payloads for user awareness
            payloads = payload_data.get("payloads", [])
            if payloads:
                logger.info("🎯 Sample payloads generated:")
                for i, payload_info in enumerate(payloads[:3]):  # Show first 3
                    risk = payload_info.get("risk_level", "UNKNOWN")
                    context = payload_info.get("context", "basic")
                    logger.info(f"   ├─ [{risk}] {context}: {payload_info['payload'][:50]}...")
        else:
            logger.error("❌ AI payload generation failed")

        return result

    @mcp.tool()
    async def ai_test_payload(payload: str, target_url: str, method: str = "GET") -> Dict[str, Any]:
        """
        Test generated payload against target with AI analysis.

        Args:
            payload: The payload to test
            target_url: Target URL to test against
            method: HTTP method (GET, POST)

        Returns:
            Test results with AI analysis and vulnerability assessment
        """
        data = {
            "payload": payload,
            "target_url": target_url,
            "method": method
        }
        logger.info(f"🧪 Testing AI payload against {target_url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/ai/test_payload", data)
        )

        if result.get("success"):
            analysis = result.get("ai_analysis", {})
            potential_vuln = analysis.get("potential_vulnerability", False)
            logger.info(f"🔍 Payload test completed | Vulnerability detected: {potential_vuln}")

            if potential_vuln:
                logger.warning("⚠️  Potential vulnerability found! Review the response carefully.")
            else:
                logger.info("✅ No obvious vulnerability indicators detected")
        else:
            logger.error("❌ Payload testing failed")

        return result

    @mcp.tool()
    async def ai_generate_attack_suite(target_url: str, attack_types: str = "xss,sqli,lfi") -> Dict[str, Any]:
        """
        Generate comprehensive attack suite with multiple payload types.

        Args:
            target_url: Target URL for testing
            attack_types: Comma-separated list of attack types

        Returns:
            Comprehensive attack suite with multiple payload types
        """
        attack_list = [attack.strip() for attack in attack_types.split(",")]
        results = {
            "target_url": target_url,
            "attack_types": attack_list,
            "payload_suites": {},
            "summary": {
                "total_payloads": 0,
                "high_risk_payloads": 0,
                "test_cases": 0
            }
        }

        logger.info(f"🚀 Generating comprehensive attack suite for {target_url}")
        logger.info(f"🎯 Attack types: {', '.join(attack_list)}")

        for attack_type in attack_list:
            logger.info(f"🤖 Generating {attack_type} payloads...")

            # Generate payloads for this attack type
            payload_result = ai_generate_payload(attack_type, "advanced", "", target_url)

            if payload_result.get("success"):
                payload_data = payload_result.get("ai_payload_generation", {})
                results["payload_suites"][attack_type] = payload_data

                # Update summary
                results["summary"]["total_payloads"] += payload_data.get("payload_count", 0)
                results["summary"]["test_cases"] += len(payload_data.get("test_cases", []))

                # Count high-risk payloads
                for payload_info in payload_data.get("payloads", []):
                    if payload_info.get("risk_level") == "HIGH":
                        results["summary"]["high_risk_payloads"] += 1

        logger.info(f"✅ Attack suite generated:")
        logger.info(f"   ├─ Total payloads: {results['summary']['total_payloads']}")
        logger.info(f"   ├─ High-risk payloads: {results['summary']['high_risk_payloads']}")
        logger.info(f"   └─ Test cases: {results['summary']['test_cases']}")

        return {
            "success": True,
            "attack_suite": results,
            "timestamp": time.time()
        }
