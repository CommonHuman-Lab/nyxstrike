from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from server_core import ModernVisualEngine
from server_api.web_framework.http_framework import http_framework
from server_api.web_framework.browser_agent import browser_agent

logger = logging.getLogger(__name__)

api_web_scan_burpsuite_bp = Blueprint("api_web_scan_burpsuite", __name__)


@api_web_scan_burpsuite_bp.route("/api/tools/burpsuite-alternative", methods=["POST"])
def burpsuite_alternative():
    """Comprehensive Burp Suite alternative combining HTTP framework and browser agent"""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "comprehensive")  # comprehensive, spider, passive, active
        headless = params.get("headless", True)
        max_depth = params.get("max_depth", 3)
        max_pages = params.get("max_pages", 50)

        if not target:
            return jsonify({"error": "Target parameter is required"}), 400

        logger.info(f"{ModernVisualEngine.create_section_header('BURP SUITE ALTERNATIVE', '🔥', 'BLOOD_RED')}")
        scan_message = f'Starting {scan_type} scan of {target}'
        logger.info(f"{ModernVisualEngine.format_highlighted_text(scan_message, 'RED')}")

        results = {
            'target': target,
            'scan_type': scan_type,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }

        # Phase 1: Browser-based reconnaissance
        if scan_type in ['comprehensive', 'spider']:
            logger.info(f"{ModernVisualEngine.format_tool_status('BrowserAgent', 'RUNNING', 'Reconnaissance Phase')}")

            if not browser_agent.driver:
                browser_agent.setup_browser(headless)

            browser_result = browser_agent.navigate_and_inspect(target)
            results['browser_analysis'] = browser_result

        # Phase 2: HTTP spidering
        if scan_type in ['comprehensive', 'spider']:
            logger.info(f"{ModernVisualEngine.format_tool_status('HTTP-Spider', 'RUNNING', 'Discovery Phase')}")

            spider_result = http_framework.spider_website(target, max_depth, max_pages)
            results['spider_analysis'] = spider_result

        # Phase 3: Vulnerability analysis
        if scan_type in ['comprehensive', 'active']:
            logger.info(f"{ModernVisualEngine.format_tool_status('VulnScanner', 'RUNNING', 'Analysis Phase')}")

            # Test discovered endpoints
            discovered_urls = results.get('spider_analysis', {}).get('discovered_urls', [target])
            vuln_results = []

            for url in discovered_urls[:20]:  # Limit to 20 URLs
                test_result = http_framework.intercept_request(url)
                if test_result.get('success'):
                    vuln_results.append(test_result)

            results['vulnerability_analysis'] = {
                'tested_urls': len(vuln_results),
                'total_vulnerabilities': len(http_framework.vulnerabilities),
                'recent_vulnerabilities': http_framework._get_recent_vulns(20)
            }

        # Generate summary
        total_vulns = len(http_framework.vulnerabilities)
        vuln_summary = {}
        for vuln in http_framework.vulnerabilities:
            severity = vuln.get('severity', 'unknown')
            vuln_summary[severity] = vuln_summary.get(severity, 0) + 1

        results['summary'] = {
            'total_vulnerabilities': total_vulns,
            'vulnerability_breakdown': vuln_summary,
            'pages_analyzed': len(results.get('spider_analysis', {}).get('discovered_urls', [])),
            'security_score': max(0, 100 - (total_vulns * 5))
        }

        # Display summary with enhanced colors
        logger.info(f"{ModernVisualEngine.create_section_header('SCAN COMPLETE', '✅', 'SUCCESS')}")
        vuln_message = f'Found {total_vulns} vulnerabilities'
        color_choice = 'YELLOW' if total_vulns > 0 else 'GREEN'
        logger.info(f"{ModernVisualEngine.format_highlighted_text(vuln_message, color_choice)}")

        for severity, count in vuln_summary.items():
            logger.info(f"  {ModernVisualEngine.format_vulnerability_severity(severity, count)}")

        return jsonify(results)

    except Exception as e:
        logger.error(f"{ModernVisualEngine.format_error_card('CRITICAL', 'BurpAlternative', str(e))}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
