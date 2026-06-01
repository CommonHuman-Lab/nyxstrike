# mcp_tools/web_scan/phaseaccess.py

from typing import Dict, Any, List, Optional
import asyncio


def register_phaseaccess_tool(mcp, api_client, logger):

    @mcp.tool()
    async def phaseaccess_scan(
        target: str,
        # Session A
        session_a_headers: Optional[Dict[str, str]] = None,
        session_a_cookies: str = "",
        session_a_label: str = "session_a",
        # Session B — leave session_b_label empty for single-session mode
        session_b_headers: Optional[Dict[str, str]] = None,
        session_b_cookies: str = "",
        session_b_label: str = "",
        # Request
        method: str = "GET",
        body: str = "",
        # Form login — session A
        login_url: str = "",
        login_user: str = "",
        login_pass: str = "",
        login_user_field: str = "",
        login_pass_field: str = "",
        # Form login — session B
        login_url_b: str = "",
        login_user_b: str = "",
        login_pass_b: str = "",
        # Crawl
        crawl: bool = False,
        crawl_depth: int = 3,
        crawl_pages: int = 100,
        browser_crawl: bool = False,
        auto_login: bool = False,
        # Spec / traffic import
        openapi: str = "",
        base_url: str = "",
        targets: str = "",
        # Stored IDOR chaining
        chain_create: str = "",
        chain_body: str = "",
        chain_read: str = "",
        # Network
        proxy: str = "",
        verify_ssl: bool = True,
        delay: float = 0.0,
        threads: int = 5,
        timeout: int = 15,
        user_agent: str = "",
        # Scan tuning
        max_candidates: int = 10,
        min_confidence: str = "",
        method_bypass: bool = True,
        param_pollution: bool = True,
        mass_assignment: bool = True,
        soft_delete: bool = True,
        blind_idor: bool = True,
        extra_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run PhaseAccess IDOR/BOLA scanner.

        Detects Insecure Direct Object References and Broken Object Level Authorization.
        In dual-session mode (session_b_label set) findings are CONFIRMED when user B's
        data appears in user A's response. Use auto_login + crawl to let PhaseAccess
        discover the login form and authenticate both sessions automatically.

        Args:
            target: Primary target URL (e.g. http://app.example.com/users/42)
            session_a_headers: Auth headers for session A (e.g. {"Authorization": "Bearer <token>"})
            session_a_cookies: Cookie string for session A
            session_a_label: Human label for session A shown in findings
            session_b_headers: Auth headers for session B — enables dual-session mode
            session_b_cookies: Cookie string for session B
            session_b_label: Label for session B (e.g. "attacker") — leave empty for single-session
            method: HTTP method for the primary target
            body: Request body for POST/PUT endpoints
            login_url: Login form URL to authenticate session A
            login_user: Username for session A form login
            login_pass: Password for session A form login
            login_user_field: Form field name for the username (default: username)
            login_pass_field: Form field name for the password (default: password)
            login_url_b: Login form URL for session B
            login_user_b: Username for session B form login
            login_pass_b: Password for session B form login
            crawl: Crawl target before scanning to auto-discover endpoints
            crawl_depth: Crawler max depth (default 3)
            crawl_pages: Crawler max pages (default 100)
            browser_crawl: Use headless Chromium for JS-rendered SPA discovery
            auto_login: Auto-discover login endpoints during crawl and authenticate both sessions
            openapi: OpenAPI/Swagger spec path or URL — imports all endpoints automatically
            base_url: Base URL override for OpenAPI spec
            targets: Import endpoints from a HAR file or Burp Suite XML export
            chain_create: Stored IDOR create endpoint, format METHOD:URL (e.g. POST:/api/docs)
            chain_body: Request body for --chain-create
            chain_read: Stored IDOR read URL template (e.g. /api/docs/{id})
            proxy: HTTP proxy URL
            verify_ssl: Verify TLS certificates
            delay: Seconds between requests
            threads: Concurrent request threads
            timeout: Request timeout in seconds
            user_agent: Override User-Agent (use 'random' to rotate)
            max_candidates: Max tamper candidates per discovered ID parameter
            min_confidence: Minimum confidence to report (confirmed|high|medium|low|info)
            method_bypass: Test HTTP method bypass variants
            param_pollution: Test HTTP parameter pollution
            mass_assignment: Test mass assignment on JSON body endpoints
            soft_delete: Test soft-delete bypass via hint parameters
            blind_idor: Flag blind IDOR via status-only signals
            extra_urls: Additional URLs to test alongside the primary target

        Returns:
            PhaseAccess scan results with IDOR findings, confidence levels, and curl reproductions
        """
        payload = {
            "target": target,
            "session_a_headers": session_a_headers or {},
            "session_a_cookies": session_a_cookies,
            "session_a_label": session_a_label,
            "session_b_headers": session_b_headers or {},
            "session_b_cookies": session_b_cookies,
            "session_b_label": session_b_label,
            "method": method,
            "body": body,
            "login_url": login_url,
            "login_user": login_user,
            "login_pass": login_pass,
            "login_user_field": login_user_field,
            "login_pass_field": login_pass_field,
            "login_url_b": login_url_b,
            "login_user_b": login_user_b,
            "login_pass_b": login_pass_b,
            "crawl": crawl,
            "crawl_depth": crawl_depth,
            "crawl_pages": crawl_pages,
            "browser_crawl": browser_crawl,
            "auto_login": auto_login,
            "openapi": openapi,
            "base_url": base_url,
            "targets": targets,
            "chain_create": chain_create,
            "chain_body": chain_body,
            "chain_read": chain_read,
            "proxy": proxy,
            "verify_ssl": verify_ssl,
            "delay": delay,
            "threads": threads,
            "timeout": timeout,
            "user_agent": user_agent,
            "max_candidates": max_candidates,
            "min_confidence": min_confidence,
            "method_bypass": method_bypass,
            "param_pollution": param_pollution,
            "mass_assignment": mass_assignment,
            "soft_delete": soft_delete,
            "blind_idor": blind_idor,
            "extra_urls": extra_urls or [],
        }
        mode = "dual-session" if session_b_label else "single-session"
        if auto_login:
            mode += " + auto-login"
        logger.info(f"Starting PhaseAccess IDOR scan ({mode}): {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/phaseaccess", payload)
        )
        if result.get("success"):
            logger.info("PhaseAccess scan completed")
        else:
            logger.error("PhaseAccess scan failed")
        return result
