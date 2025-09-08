"""
Comprehensive Security Vulnerability Test Suite
Tests for common security vulnerabilities across all MCP servers
"""

import base64
import json
import os
import socket
import ssl

# Security testing utilities
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import jwt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@dataclass
class SecurityTestResult:
    """Security test result"""

    test_name: str
    vulnerability_type: str
    status: str  # 'passed', 'failed', 'vulnerable'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class VulnerabilityReport:
    """Vulnerability assessment report"""

    component: str
    total_tests: int
    vulnerabilities_found: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    test_results: List[SecurityTestResult]


class SecurityTester:
    """Core security testing functionality"""

    def __init__(self):
        self.session = None
        self.test_results = []
        self.base_urls = {
            "unified_mcp": "${SOPHIA_API_ENDPOINT}",
            "artemis": "http://localhost:8081",
            "bi_server": "http://localhost:8082",
            "mem0": "http://localhost:8083",
            "base_mcp": "http://localhost:8084",
        }

    async def setup(self):
        """Setup security tester"""
        # Disable SSL verification for testing (controlled environment)
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(
            connector=connector, timeout=aiohttp.ClientTimeout(total=30)
        )

    async def teardown(self):
        """Cleanup security tester"""
        if self.session:
            await self.session.close()

    def record_result(self, result: SecurityTestResult):
        """Record security test result"""
        self.test_results.append(result)

        if result.status == "vulnerable":
            severity_symbol = {
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "critical": "🚨",
            }.get(result.severity, "❓")

            print(
                f"{severity_symbol} {result.vulnerability_type}: {result.description}"
            )

    def generate_report(self, component: str) -> VulnerabilityReport:
        """Generate vulnerability assessment report"""
        component_results = [
            r for r in self.test_results if component in r.test_name.lower()
        ]

        severity_counts = {
            "critical": len([r for r in component_results if r.severity == "critical"]),
            "high": len([r for r in component_results if r.severity == "high"]),
            "medium": len([r for r in component_results if r.severity == "medium"]),
            "low": len([r for r in component_results if r.severity == "low"]),
        }

        vulnerabilities_found = len(
            [r for r in component_results if r.status == "vulnerable"]
        )

        return VulnerabilityReport(
            component=component,
            total_tests=len(component_results),
            vulnerabilities_found=vulnerabilities_found,
            critical_issues=severity_counts["critical"],
            high_issues=severity_counts["high"],
            medium_issues=severity_counts["medium"],
            low_issues=severity_counts["low"],
            test_results=component_results,
        )


class TestAuthenticationSecurity:
    """Authentication and authorization security tests"""

    @pytest.fixture
    async def security_tester(self):
        """Security tester fixture"""
        tester = SecurityTester()
        await tester.setup()

        yield tester

        await tester.teardown()

    @pytest.mark.asyncio
    async def test_jwt_token_security(self, security_tester):
        """Test JWT token security vulnerabilities"""

        # Test 1: JWT None Algorithm Attack
        print("🔐 Testing JWT None Algorithm vulnerability...")

        # Create JWT with 'none' algorithm
        none_payload = {
            "sub": "admin",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        none_header = {"alg": "none", "typ": "JWT"}

        none_token = (
            base64.urlsafe_b64encode(json.dumps(none_header).encode())
            .decode()
            .rstrip("=")
            + "."
        )
        none_token += (
            base64.urlsafe_b64encode(json.dumps(none_payload).encode())
            .decode()
            .rstrip("=")
            + "."
        )

        for service_name, base_url in security_tester.base_urls.items():
            try:
                async with security_tester.session.get(
                    f"{base_url}/protected-endpoint",
                    headers={"Authorization": f"Bearer {none_token}"},
                ) as response:
                    if response.status == 200:
                        security_tester.record_result(
                            SecurityTestResult(
                                test_name=f"{service_name}_jwt_none_algorithm",
                                vulnerability_type="JWT None Algorithm",
                                status="vulnerable",
                                severity="high",
                                description=f"{service_name} accepts JWT tokens with 'none' algorithm",
                                details={
                                    "token": none_token,
                                    "response_status": response.status,
                                },
                                timestamp=datetime.now(),
                            )
                        )
                    else:
                        security_tester.record_result(
                            SecurityTestResult(
                                test_name=f"{service_name}_jwt_none_algorithm",
                                vulnerability_type="JWT None Algorithm",
                                status="passed",
                                severity="high",
                                description=f"{service_name} properly rejects JWT 'none' algorithm",
                                details={"response_status": response.status},
                                timestamp=datetime.now(),
                            )
                        )
            except Exception:# Service might not have this endpoint, which is fine
                pass

        # Test 2: JWT Secret Brute Force
        print("🔐 Testing JWT secret strength...")

        weak_secrets = ["secret", "123456", "password", "admin", "jwt", "key"]
        test_payload = {"sub": "testuser", "iat": int(time.time())}

        for secret in weak_secrets:
            try:
                weak_token = jwt.encode(test_payload, secret, algorithm="HS256")

                # Try to use weak token
                for service_name, base_url in security_tester.base_urls.items():
                    try:
                        async with security_tester.session.get(
                            f"{base_url}/protected",
                            headers={"Authorization": f"Bearer {weak_token}"},
                        ) as response:
                            if response.status == 200:
                                security_tester.record_result(
                                    SecurityTestResult(
                                        test_name=f"{service_name}_jwt_weak_secret",
                                        vulnerability_type="JWT Weak Secret",
                                        status="vulnerable",
                                        severity="critical",
                                        description=f"{service_name} uses weak JWT secret: {secret}",
                                        details={"weak_secret": secret},
                                        timestamp=datetime.now(),
                                    )
                                )
                    except Exception:pass
            except Exception:pass  # JWT encoding might fail

    @pytest.mark.asyncio
    async def test_authentication_bypass(self, security_tester):
        """Test authentication bypass vulnerabilities"""

        print("🚪 Testing authentication bypass...")

        bypass_attempts = [
            # Header manipulation
            {"headers": {"X-Forwarded-For": "${LOCALHOST_IP}"}},
            {"headers": {"X-Real-IP": "localhost"}},
            {"headers": {"X-Originating-IP": "${LOCALHOST_IP}"}},
            {"headers": {"X-Remote-IP": "localhost"}},
            {"headers": {"X-Admin": "true"}},
            {"headers": {"X-User-Role": "admin"}},
            # Parameter pollution
            {"params": {"user": ["admin", "guest"]}},
            {"params": {"role": "admin"}},
            {"params": {"bypass": "true"}},
            # Path manipulation
            {"path_suffix": "/../admin"},
            {"path_suffix": "/./protected"},
            {"path_suffix": "/%2e%2e/admin"},
        ]

        for service_name, base_url in security_tester.base_urls.items():
            for attempt in bypass_attempts:
                try:
                    url = base_url + "/protected" + attempt.get("path_suffix", "")

                    async with security_tester.session.get(
                        url,
                        headers=attempt.get("headers", {}),
                        params=attempt.get("params", {}),
                    ) as response:
                        if response.status == 200:
                            security_tester.record_result(
                                SecurityTestResult(
                                    test_name=f"{service_name}_auth_bypass",
                                    vulnerability_type="Authentication Bypass",
                                    status="vulnerable",
                                    severity="high",
                                    description=f"{service_name} authentication bypassed",
                                    details={"bypass_method": attempt},
                                    timestamp=datetime.now(),
                                )
                            )
                except Exception:pass

    @pytest.mark.asyncio
    async def test_session_management(self, security_tester):
        """Test session management security"""

        print("🍪 Testing session management...")

        for service_name, base_url in security_tester.base_urls.items():
            try:
                # Test session fixation
                async with security_tester.session.get(
                    f"{base_url}/login", cookies={"SESSIONID": "fixed_session_id"}
                ) as response:
                    # Check if server accepts pre-set session ID
                    set_cookie = response.headers.get("Set-Cookie", "")
                    if "fixed_session_id" in set_cookie:
                        security_tester.record_result(
                            SecurityTestResult(
                                test_name=f"{service_name}_session_fixation",
                                vulnerability_type="Session Fixation",
                                status="vulnerable",
                                severity="medium",
                                description=f"{service_name} vulnerable to session fixation",
                                details={"set_cookie": set_cookie},
                                timestamp=datetime.now(),
                            )
                        )

                # Test secure cookie flags
                if "Set-Cookie" in response.headers:
                    cookie_header = response.headers["Set-Cookie"]

                    # Check for Secure flag
                    if "Secure" not in cookie_header:
                        security_tester.record_result(
                            SecurityTestResult(
                                test_name=f"{service_name}_cookie_secure_flag",
                                vulnerability_type="Insecure Cookie",
                                status="vulnerable",
                                severity="medium",
                                description=f"{service_name} cookies missing Secure flag",
                                details={"cookie_header": cookie_header},
                                timestamp=datetime.now(),
                            )
                        )

                    # Check for HttpOnly flag
                    if "HttpOnly" not in cookie_header:
                        security_tester.record_result(
                            SecurityTestResult(
                                test_name=f"{service_name}_cookie_httponly_flag",
                                vulnerability_type="Cookie XSS Risk",
                                status="vulnerable",
                                severity="medium",
                                description=f"{service_name} cookies missing HttpOnly flag",
                                details={"cookie_header": cookie_header},
                                timestamp=datetime.now(),
                            )
                        )
            except Exception:pass


class TestInputValidationSecurity:
    """Input validation and sanitization security tests"""

    @pytest.fixture
    async def security_tester(self):
        tester = SecurityTester()
        await tester.setup()

        yield tester

        await tester.teardown()

    @pytest.mark.asyncio
    async def test_sql_injection(self, security_tester):
        """Test SQL injection vulnerabilities"""

        print("💉 Testing SQL injection vulnerabilities...")

        # Common SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 'a'='a",
            "') OR ('1'='1",
            "' UNION SELECT null,username,password FROM users--",
            "'; DROP TABLE users;--",
            "' OR 1=1 LIMIT 1--",
            "admin'--",
            "admin' #",
            "admin'/*",
            "' or 1=1#",
            "' or 1=1--",
            "' or 1=1/*",
            "') or '1'='1--",
            "') or ('1'='1",
        ]

        # Test endpoints that might be vulnerable
        test_endpoints = [
            "/users",
            "/login",
            "/search",
            "/api/query",
            "/customers",
            "/memories",
            "/workflows",
        ]

        for service_name, base_url in security_tester.base_urls.items():
            for endpoint in test_endpoints:
                for payload in sql_payloads:
                    try:
                        # Test in URL parameters
                        async with security_tester.session.get(
                            f"{base_url}{endpoint}",
                            params={"id": payload, "search": payload},
                        ) as response:
                            await self._check_sql_injection_response(
                                security_tester,
                                service_name,
                                endpoint,
                                payload,
                                response,
                            )

                        # Test in POST body
                        async with security_tester.session.post(
                            f"{base_url}{endpoint}",
                            json={
                                "username": payload,
                                "query": payload,
                                "filter": payload,
                            },
                        ) as response:
                            await self._check_sql_injection_response(
                                security_tester,
                                service_name,
                                endpoint,
                                payload,
                                response,
                            )

                    except Exception:pass  # Endpoint might not exist

    async def _check_sql_injection_response(
        self, security_tester, service_name, endpoint, payload, response
    ):
        """Check response for SQL injection indicators"""
        try:
            response_text = await response.text()

            # SQL error indicators
            sql_error_indicators = [
                "sql syntax",
                "mysql_fetch",
                "ora-01756",
                "microsoft jet database",
                "odbc sql",
                "sqlite_master",
                "postgresql",
                "warning: pg_",
                "valid postgresql result",
                "exception (0x80004005)",
                "oledb.dll error",
                "unclosed quotation mark",
                "quoted string not properly terminated",
            ]

            response_lower = response_text.lower()

            for indicator in sql_error_indicators:
                if indicator in response_lower:
                    security_tester.record_result(
                        SecurityTestResult(
                            test_name=f"{service_name}_sql_injection_{endpoint}",
                            vulnerability_type="SQL Injection",
                            status="vulnerable",
                            severity="critical",
                            description=f"{service_name}{endpoint} vulnerable to SQL injection",
                            details={
                                "payload": payload,
                                "error_indicator": indicator,
                                "response_snippet": response_text[:200],
                            },
                            timestamp=datetime.now(),
                        )
                    )
                    break
        except Exception:pass

    @pytest.mark.asyncio
    async def test_nosql_injection(self, security_tester):
        """Test NoSQL injection vulnerabilities"""

        print("🍃 Testing NoSQL injection vulnerabilities...")

        # NoSQL injection payloads
        nosql_payloads = [
            {"$ne": ""},
            {"$gt": ""},
            {"$where": "1==1"},
            {"$regex": ".*"},
            {"$exists": True},
            {"$nin": []},
            {"$or": [{"username": "admin"}, {"username": "user"}]},
            {"username": {"$regex": ".*"}, "password": {"$regex": ".*"}},
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$where": "this.password.match(/.*/)"}',
        ]

        for service_name, base_url in security_tester.base_urls.items():
            for payload in nosql_payloads:
                try:
                    # Test different endpoints
                    endpoints = ["/api/users", "/login", "/search", "/memories/search"]

                    for endpoint in endpoints:
                        # Test as JSON payload
                        if isinstance(payload, dict):
                            test_data = {"filter": payload, "query": payload}
                        else:
                            test_data = {"filter": payload}

                        async with security_tester.session.post(
                            f"{base_url}{endpoint}", json=test_data
                        ) as response:
                            response_text = await response.text()

                            # Check for NoSQL error indicators
                            nosql_errors = [
                                "mongodb",
                                "bson",
                                "couchdb",
                                "redis error",
                                "cassandra",
                                "$where",
                                "db.eval",
                                "mapreduce",
                            ]

                            response_lower = response_text.lower()

                            for error in nosql_errors:
                                if error in response_lower:
                                    security_tester.record_result(
                                        SecurityTestResult(
                                            test_name=f"{service_name}_nosql_injection_{endpoint}",
                                            vulnerability_type="NoSQL Injection",
                                            status="vulnerable",
                                            severity="high",
                                            description=f"{service_name}{endpoint} vulnerable to NoSQL injection",
                                            details={
                                                "payload": str(payload),
                                                "error_indicator": error,
                                            },
                                            timestamp=datetime.now(),
                                        )
                                    )
                                    break
                except Exception:pass

    @pytest.mark.asyncio
    async def test_xss_vulnerabilities(self, security_tester):
        """Test Cross-Site Scripting vulnerabilities"""

        print("📜 Testing XSS vulnerabilities...")

        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<audio src=x onerror=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "<<SCRIPT>alert('XSS')<</SCRIPT>",
            "<SCRIPT SRC=http://xss.example.com/xss.js></SCRIPT>",
            "';alert('XSS');//",
            "\";alert('XSS');//",
        ]

        for service_name, base_url in security_tester.base_urls.items():
            test_endpoints = ["/api/echo", "/search", "/comments", "/profile"]

            for endpoint in test_endpoints:
                for payload in xss_payloads:
                    try:
                        # Test in URL parameters
                        async with security_tester.session.get(
                            f"{base_url}{endpoint}",
                            params={"q": payload, "message": payload},
                        ) as response:
                            await self._check_xss_response(
                                security_tester,
                                service_name,
                                endpoint,
                                payload,
                                response,
                            )

                        # Test in POST data
                        async with security_tester.session.post(
                            f"{base_url}{endpoint}",
                            json={"content": payload, "message": payload},
                        ) as response:
                            await self._check_xss_response(
                                security_tester,
                                service_name,
                                endpoint,
                                payload,
                                response,
                            )
                    except Exception:pass

    async def _check_xss_response(
        self, security_tester, service_name, endpoint, payload, response
    ):
        """Check response for XSS vulnerabilities"""
        try:
            response_text = await response.text()

            # Check if payload is reflected without encoding
            if payload in response_text:
                # Check if it's properly encoded
                encoded_variants = [
                    urllib.parse.quote(payload),
                    payload.replace("<", "&lt;").replace(">", "&gt;"),
                    payload.replace("'", "&#x27;").replace('"', "&quot;"),
                ]

                is_properly_encoded = any(
                    variant in response_text for variant in encoded_variants
                )

                if not is_properly_encoded:
                    security_tester.record_result(
                        SecurityTestResult(
                            test_name=f"{service_name}_xss_{endpoint}",
                            vulnerability_type="Cross-Site Scripting (XSS)",
                            status="vulnerable",
                            severity="high",
                            description=f"{service_name}{endpoint} vulnerable to XSS",
                            details={
                                "payload": payload,
                                "response_contains_payload": True,
                                "properly_encoded": False,
                            },
                            timestamp=datetime.now(),
                        )
                    )
        except Exception:pass


class TestAPISecurityVulnerabilities:
    """API-specific security vulnerability tests"""

    @pytest.fixture
    async def security_tester(self):
        tester = SecurityTester()
        await tester.setup()

        yield tester

        await tester.teardown()

    @pytest.mark.asyncio
    async def test_cors_vulnerabilities(self, security_tester):
        """Test CORS (Cross-Origin Resource Sharing) vulnerabilities"""

        print("🌐 Testing CORS vulnerabilities...")

        malicious_origins = [
            "http://evil.com",
            "https://attacker.example.com",
            "null",
            "*",
            "file://",
            "data:",
        ]

        for service_name, base_url in security_tester.base_urls.items():
            for origin in malicious_origins:
                try:
                    async with security_tester.session.options(
                        f"{base_url}/api/test",
                        headers={
                            "Origin": origin,
                            "Access-Control-Request-Method": "POST",
                            "Access-Control-Request-Headers": "Content-Type",
                        },
                    ) as response:
                        cors_header = response.headers.get(
                            "Access-Control-Allow-Origin", ""
                        )

                        if cors_header == "*" or cors_header == origin:
                            severity = "high" if origin in ["*", "null"] else "medium"

                            security_tester.record_result(
                                SecurityTestResult(
                                    test_name=f"{service_name}_cors_misconfiguration",
                                    vulnerability_type="CORS Misconfiguration",
                                    status="vulnerable",
                                    severity=severity,
                                    description=f"{service_name} allows requests from {origin}",
                                    details={
                                        "malicious_origin": origin,
                                        "cors_header": cors_header,
                                    },
                                    timestamp=datetime.now(),
                                )
                            )
                except Exception:pass

    @pytest.mark.asyncio
    async def test_http_method_vulnerabilities(self, security_tester):
        """Test HTTP method vulnerabilities"""

        print("🔧 Testing HTTP method vulnerabilities...")

        dangerous_methods = ["TRACE", "TRACK", "DEBUG", "PUT", "DELETE", "PATCH"]

        for service_name, base_url in security_tester.base_urls.items():
            for method in dangerous_methods:
                try:
                    async with security_tester.session.request(
                        method, f"{base_url}/api/test"
                    ) as response:
                        if response.status != 405:  # Method Not Allowed
                            security_tester.record_result(
                                SecurityTestResult(
                                    test_name=f"{service_name}_dangerous_http_method",
                                    vulnerability_type="Dangerous HTTP Method",
                                    status="vulnerable",
                                    severity="medium",
                                    description=f"{service_name} allows {method} method",
                                    details={
                                        "method": method,
                                        "status_code": response.status,
                                    },
                                    timestamp=datetime.now(),
                                )
                            )
                except Exception:pass

    @pytest.mark.asyncio
    async def test_rate_limiting_bypass(self, security_tester):
        """Test rate limiting bypass vulnerabilities"""

        print("⚡ Testing rate limiting bypass...")

        bypass_headers = [
            {"X-Forwarded-For": "${LOCALHOST_IP}"},
            {"X-Real-IP": "192.168.1.1"},
            {"X-Originating-IP": "10.0.0.1"},
            {"X-Remote-IP": "172.16.0.1"},
            {"X-Cluster-Client-IP": "${LOCALHOST_IP}"},
            {"CF-Connecting-IP": "1.1.1.1"},
            {"True-Client-IP": "8.8.8.8"},
        ]

        for service_name, base_url in security_tester.base_urls.items():
            try:
                # First, trigger rate limiting with rapid requests
                for i in range(20):  # Rapid requests
                    async with security_tester.session.get(
                        f"{base_url}/api/test"
                    ) as response:
                        if response.status == 429:  # Rate limited
                            # Now try to bypass with headers
                            for headers in bypass_headers:
                                async with security_tester.session.get(
                                    f"{base_url}/api/test", headers=headers
                                ) as bypass_response:
                                    if bypass_response.status != 429:
                                        security_tester.record_result(
                                            SecurityTestResult(
                                                test_name=f"{service_name}_rate_limit_bypass",
                                                vulnerability_type="Rate Limiting Bypass",
                                                status="vulnerable",
                                                severity="medium",
                                                description=f"{service_name} rate limiting bypassed",
                                                details={
                                                    "bypass_headers": headers,
                                                    "bypass_status": bypass_response.status,
                                                },
                                                timestamp=datetime.now(),
                                            )
                                        )
                            break
            except Exception:pass

    @pytest.mark.asyncio
    async def test_api_versioning_vulnerabilities(self, security_tester):
        """Test API versioning security issues"""

        print("📊 Testing API versioning vulnerabilities...")

        # Test access to older API versions that might have vulnerabilities
        api_versions = ["v1", "v2", "v3", "1.0", "2.0", "beta", "alpha", "dev"]

        for service_name, base_url in security_tester.base_urls.items():
            for version in api_versions:
                version_urls = [
                    f"{base_url}/{version}/admin",
                    f"{base_url}/api/{version}/users",
                    f"{base_url}/{version}/config",
                    f"{base_url}/api/{version}/debug",
                ]

                for url in version_urls:
                    try:
                        async with security_tester.session.get(url) as response:
                            if response.status == 200:
                                response_text = await response.text()

                                # Check if it exposes sensitive information
                                sensitive_keywords = [
                                    "debug",
                                    "admin",
                                    "config",
                                    "password",
                                    "token",
                                    "secret",
                                    "key",
                                    "internal",
                                    "private",
                                ]

                                response_lower = response_text.lower()
                                found_sensitive = [
                                    kw
                                    for kw in sensitive_keywords
                                    if kw in response_lower
                                ]

                                if found_sensitive:
                                    security_tester.record_result(
                                        SecurityTestResult(
                                            test_name=f"{service_name}_api_version_exposure",
                                            vulnerability_type="API Version Information Exposure",
                                            status="vulnerable",
                                            severity="medium",
                                            description=f"{service_name} exposes sensitive info in {version}",
                                            details={
                                                "version": version,
                                                "url": url,
                                                "sensitive_keywords": found_sensitive,
                                            },
                                            timestamp=datetime.now(),
                                        )
                                    )
                    except Exception:pass


class TestDataProtectionSecurity:
    """Data protection and encryption security tests"""

    @pytest.fixture
    async def security_tester(self):
        tester = SecurityTester()
        await tester.setup()

        yield tester

        await tester.teardown()

    @pytest.mark.asyncio
    async def test_sensitive_data_exposure(self, security_tester):
        """Test for sensitive data exposure"""

        print("🔍 Testing sensitive data exposure...")

        # Common endpoints that might expose sensitive data
        sensitive_endpoints = [
            "/debug",
            "/admin",
            "/config",
            "/env",
            "/status",
            "/health",
            "/info",
            "/metrics",
            "/logs",
            "/api/debug",
            "/api/admin",
            "/api/config",
            "/.env",
            "/config.json",
            "/settings.json",
        ]

        sensitive_patterns = [
            r"password[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"secret[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"api[_-]?key[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"token[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"database[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"connection[_-]?string[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"private[_-]?key[\"'\s]*[:=][\"'\s]*[^\s\"']+",
            r"aws[_-]?access[_-]?key",
            r"aws[_-]?secret[_-]?key",
        ]

        import re

        for service_name, base_url in security_tester.base_urls.items():
            for endpoint in sensitive_endpoints:
                try:
                    async with security_tester.session.get(
                        f"{base_url}{endpoint}"
                    ) as response:
                        if response.status == 200:
                            response_text = await response.text()

                            for pattern in sensitive_patterns:
                                matches = re.finditer(
                                    pattern, response_text, re.IGNORECASE
                                )
                                for match in matches:
                                    security_tester.record_result(
                                        SecurityTestResult(
                                            test_name=f"{service_name}_sensitive_data_exposure",
                                            vulnerability_type="Sensitive Data Exposure",
                                            status="vulnerable",
                                            severity="high",
                                            description=f"{service_name} exposes sensitive data",
                                            details={
                                                "endpoint": endpoint,
                                                "pattern_matched": pattern,
                                                "match": match.group()[:50] + "...",
                                            },
                                            timestamp=datetime.now(),
                                        )
                                    )
                except Exception:pass

    @pytest.mark.asyncio
    async def test_encryption_weaknesses(self, security_tester):
        """Test for weak encryption and hashing"""

        print("🔐 Testing encryption weaknesses...")

        for service_name, base_url in security_tester.base_urls.items():
            try:
                # Test SSL/TLS configuration
                if base_url.startswith("https://"):
                    hostname = base_url.split("://")[1].split(":")[0]
                    port = (
                        int(base_url.split(":")[-1])
                        if ":" in base_url.split("://")[1]
                        else 443
                    )

                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE

                    with socket.create_connection((hostname, port), timeout=5) as sock:
                        with context.wrap_socket(
                            sock, server_hostname=hostname
                        ) as ssock:
                            cipher = ssock.cipher()

                            # Check for weak ciphers
                            weak_ciphers = ["RC4", "DES", "3DES", "MD5", "SHA1"]
                            cipher_name = cipher[0] if cipher else ""

                            for weak in weak_ciphers:
                                if weak in cipher_name:
                                    security_tester.record_result(
                                        SecurityTestResult(
                                            test_name=f"{service_name}_weak_cipher",
                                            vulnerability_type="Weak Encryption",
                                            status="vulnerable",
                                            severity="high",
                                            description=f"{service_name} uses weak cipher: {cipher_name}",
                                            details={"cipher": cipher_name},
                                            timestamp=datetime.now(),
                                        )
                                    )

                # Test for weak hashing algorithms in responses
                test_endpoints = ["/api/hash", "/login", "/register"]

                for endpoint in test_endpoints:
                    async with security_tester.session.post(
                        f"{base_url}{endpoint}", json={"password": "test123"}
                    ) as response:
                        response_text = await response.text()

                        # Look for weak hash indicators
                        weak_hash_patterns = [
                            r"[a-f0-9]{32}",  # MD5
                            r"[a-f0-9]{40}",  # SHA1
                            r'"hash":\s*"[a-f0-9]{32}"',  # MD5 in JSON
                            r'"hash":\s*"[a-f0-9]{40}"',  # SHA1 in JSON
                        ]

                        for pattern in weak_hash_patterns:
                            if re.search(pattern, response_text, re.IGNORECASE):
                                security_tester.record_result(
                                    SecurityTestResult(
                                        test_name=f"{service_name}_weak_hashing",
                                        vulnerability_type="Weak Hashing Algorithm",
                                        status="vulnerable",
                                        severity="medium",
                                        description=f"{service_name} uses weak hashing",
                                        details={
                                            "endpoint": endpoint,
                                            "pattern": pattern,
                                        },
                                        timestamp=datetime.now(),
                                    )
                                )
            except Exception:pass


class TestSecurityHeaders:
    """Security headers and configuration tests"""

    @pytest.fixture
    async def security_tester(self):
        tester = SecurityTester()
        await tester.setup()

        yield tester

        await tester.teardown()

    @pytest.mark.asyncio
    async def test_security_headers(self, security_tester):
        """Test for missing security headers"""

        print("🛡️ Testing security headers...")

        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=",
            "Content-Security-Policy": "",
            "Referrer-Policy": [
                "no-referrer",
                "strict-origin",
                "strict-origin-when-cross-origin",
            ],
        }

        for service_name, base_url in security_tester.base_urls.items():
            try:
                async with security_tester.session.get(f"{base_url}/") as response:
                    headers = response.headers

                    for header_name, expected_values in required_headers.items():
                        if header_name not in headers:
                            security_tester.record_result(
                                SecurityTestResult(
                                    test_name=f"{service_name}_missing_security_header",
                                    vulnerability_type="Missing Security Header",
                                    status="vulnerable",
                                    severity="medium",
                                    description=f"{service_name} missing {header_name} header",
                                    details={"missing_header": header_name},
                                    timestamp=datetime.now(),
                                )
                            )
                        else:
                            header_value = headers[header_name]

                            if isinstance(expected_values, list):
                                if not any(
                                    expected in header_value
                                    for expected in expected_values
                                ):
                                    security_tester.record_result(
                                        SecurityTestResult(
                                            test_name=f"{service_name}_weak_security_header",
                                            vulnerability_type="Weak Security Header",
                                            status="vulnerable",
                                            severity="low",
                                            description=f"{service_name} weak {header_name}: {header_value}",
                                            details={
                                                "header": header_name,
                                                "value": header_value,
                                                "expected": expected_values,
                                            },
                                            timestamp=datetime.now(),
                                        )
                                    )
                            elif (
                                expected_values and expected_values not in header_value
                            ):
                                security_tester.record_result(
                                    SecurityTestResult(
                                        test_name=f"{service_name}_weak_security_header",
                                        vulnerability_type="Weak Security Header",
                                        status="vulnerable",
                                        severity="low",
                                        description=f"{service_name} weak {header_name}: {header_value}",
                                        details={
                                            "header": header_name,
                                            "value": header_value,
                                            "expected": expected_values,
                                        },
                                        timestamp=datetime.now(),
                                    )
                                )
            except Exception:pass

    @pytest.mark.asyncio
    async def test_information_disclosure(self, security_tester):
        """Test for information disclosure in headers"""

        print("📢 Testing information disclosure...")

        for service_name, base_url in security_tester.base_urls.items():
            try:
                async with security_tester.session.get(f"{base_url}/") as response:
                    headers = response.headers

                    # Check for information disclosure in headers
                    disclosure_headers = {
                        "Server": "Reveals server software and version",
                        "X-Powered-By": "Reveals technology stack",
                        "X-AspNet-Version": "Reveals ASP.NET version",
                        "X-Runtime": "Reveals runtime information",
                        "X-Version": "Reveals application version",
                    }

                    for header_name, description in disclosure_headers.items():
                        if header_name in headers:
                            security_tester.record_result(
                                SecurityTestResult(
                                    test_name=f"{service_name}_information_disclosure",
                                    vulnerability_type="Information Disclosure",
                                    status="vulnerable",
                                    severity="low",
                                    description=f"{service_name} {description}",
                                    details={
                                        "header": header_name,
                                        "value": headers[header_name],
                                    },
                                    timestamp=datetime.now(),
                                )
                            )
            except Exception:pass


class TestComprehensiveSecurityAssessment:
    """Comprehensive security assessment combining all tests"""

    @pytest.fixture
    async def security_tester(self):
        tester = SecurityTester()
        await tester.setup()

        yield tester

        await tester.teardown()

    @pytest.mark.asyncio
    async def test_comprehensive_security_scan(self, security_tester):
        """Run comprehensive security scan across all components"""

        print("🔒 Running comprehensive security assessment...")

        # Initialize test classes
        auth_tester = TestAuthenticationSecurity()
        input_tester = TestInputValidationSecurity()
        api_tester = TestAPISecurityVulnerabilities()
        data_tester = TestDataProtectionSecurity()
        header_tester = TestSecurityHeaders()

        # Run all security tests
        await auth_tester.test_jwt_token_security(security_tester)
        await auth_tester.test_authentication_bypass(security_tester)
        await auth_tester.test_session_management(security_tester)

        await input_tester.test_sql_injection(security_tester)
        await input_tester.test_nosql_injection(security_tester)
        await input_tester.test_xss_vulnerabilities(security_tester)

        await api_tester.test_cors_vulnerabilities(security_tester)
        await api_tester.test_http_method_vulnerabilities(security_tester)
        await api_tester.test_rate_limiting_bypass(security_tester)

        await data_tester.test_sensitive_data_exposure(security_tester)
        await data_tester.test_encryption_weaknesses(security_tester)

        await header_tester.test_security_headers(security_tester)
        await header_tester.test_information_disclosure(security_tester)

        # Generate comprehensive reports
        reports = {}
        for component in ["unified_mcp", "artemis", "bi_server", "mem0", "base_mcp"]:
            reports[component] = security_tester.generate_report(component)

        # Print summary
        print("\n🔒 Security Assessment Summary:")
        print("=" * 50)

        total_vulnerabilities = 0
        total_critical = 0
        total_high = 0

        for component, report in reports.items():
            print(f"\n{component.upper()}:")
            print(f"  Total Tests: {report.total_tests}")
            print(f"  Vulnerabilities: {report.vulnerabilities_found}")
            print(f"  Critical: {report.critical_issues}")
            print(f"  High: {report.high_issues}")
            print(f"  Medium: {report.medium_issues}")
            print(f"  Low: {report.low_issues}")

            total_vulnerabilities += report.vulnerabilities_found
            total_critical += report.critical_issues
            total_high += report.high_issues

        print("\nOVERALL SECURITY STATUS:")
        print(f"  Total Vulnerabilities Found: {total_vulnerabilities}")
        print(f"  Critical Issues: {total_critical}")
        print(f"  High Severity Issues: {total_high}")

        # Security assertions
        assert (
            total_critical == 0
        ), f"Critical security vulnerabilities found: {total_critical}"
        assert total_high <= 2, f"Too many high-severity vulnerabilities: {total_high}"

        if total_vulnerabilities == 0:
            print("✅ No security vulnerabilities detected!")
        else:
            print(f"⚠️  {total_vulnerabilities} security issues require attention")

        return reports


if __name__ == "__main__":
    # Run security vulnerability tests
    pytest.main(
        [__file__, "-v", "--tb=short", "-x", "--durations=10"]
    )  # Stop on first failure
