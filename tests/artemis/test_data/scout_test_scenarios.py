"""Test scenarios and data for Artemis Scout swarm validation"""

# Test repository structures for scout validation
TEST_REPOSITORIES = {
    "simple_python": {
        "description": "Simple Python project with clear structure",
        "files": {
            "main.py": "def main():\n    print('Hello')\n\nif __name__ == '__main__':\n    main()",
            "utils.py": "def helper():\n    return 42",
            "tests/test_main.py": "def test_main():\n    assert True",
        },
        "expected_findings": {
            "integrations": ["minimal"],
            "hotspots": [],
            "risks": ["no error handling", "minimal tests"],
        },
    },
    "complex_integration": {
        "description": "Complex project with multiple integrations",
        "files": {
            "app/api.py": "# REST API with FastAPI\nimport fastapi\napp = fastapi.FastAPI()",
            "app/database.py": "# PostgreSQL integration\nimport psycopg2",
            "app/redis_cache.py": "# Redis caching\nimport redis",
            "app/mcp_client.py": "# MCP integration\nfrom app.mcp import StdioClient",
        },
        "expected_findings": {
            "integrations": ["fastapi", "postgresql", "redis", "mcp"],
            "hotspots": ["database.py"],
            "risks": ["multiple external dependencies", "no connection pooling"],
        },
    },
    "security_issues": {
        "description": "Repository with security vulnerabilities",
        "files": {
            "auth.py": "password = 'hardcoded123'  # Security issue",
            "api.py": "eval(user_input)  # Dangerous",
            "config.py": "DEBUG = True\nSECRET_KEY = 'exposed'",
        },
        "expected_findings": {
            "integrations": [],
            "hotspots": ["auth.py", "api.py"],
            "risks": ["hardcoded credentials", "eval usage", "exposed secrets"],
        },
    },
    "performance_bottlenecks": {
        "description": "Code with performance issues",
        "files": {
            "processor.py": """
for i in range(1000000):
    for j in range(1000000):
        result = i * j  # O(n²) complexity
""",
            "database.py": """
def get_all_users():
    return db.query("SELECT * FROM users")  # No pagination
""",
        },
        "expected_findings": {
            "integrations": ["database"],
            "hotspots": ["processor.py"],
            "risks": ["O(n²) algorithm", "unbounded queries", "no caching"],
        },
    },
}

# Expected scout output structure for validation
SCOUT_OUTPUT_TEMPLATE = {
    "FINDINGS": ["Pattern: {pattern_type}", "Location: {file}:{line}", "Severity: {severity}"],
    "INTEGRATIONS": ["Service: {name}", "Type: {type}", "Risk: {risk_level}"],
    "RISKS": ["Category: {category}", "Impact: {impact}", "Mitigation: {mitigation}"],
    "RECOMMENDATIONS": ["Priority: {priority}", "Action: {action}", "Effort: {effort}"],
    "METRICS": {"files_analyzed": 0, "patterns_found": 0, "execution_time": 0.0, "confidence": 0.0},
}

# Validation test cases
VALIDATION_TESTS = [
    {
        "name": "test_scout_finds_integrations",
        "repo": "complex_integration",
        "assertions": [
            "len(output['INTEGRATIONS']) >= 3",
            "'fastapi' in str(output['INTEGRATIONS'])",
            "'postgresql' in str(output['INTEGRATIONS'])",
        ],
    },
    {
        "name": "test_scout_identifies_security_risks",
        "repo": "security_issues",
        "assertions": [
            "'hardcoded' in str(output['RISKS']).lower()",
            "'eval' in str(output['RISKS']).lower()",
            "output['METRICS']['confidence'] < 0.5",  # Low confidence due to risks
        ],
    },
    {
        "name": "test_scout_detects_performance_issues",
        "repo": "performance_bottlenecks",
        "assertions": [
            "'O(n²)' in str(output['FINDINGS']) or 'quadratic' in str(output['FINDINGS']).lower()",
            "'pagination' in str(output['RECOMMENDATIONS']).lower()",
        ],
    },
    {
        "name": "test_scout_respects_schema",
        "repo": "simple_python",
        "assertions": [
            "all(k in output for k in ['FINDINGS', 'INTEGRATIONS', 'RISKS', 'RECOMMENDATIONS', 'METRICS'])",
            "isinstance(output['METRICS']['confidence'], float)",
            "0.0 <= output['METRICS']['confidence'] <= 1.0",
        ],
    },
]


def generate_mock_scout_output(repo_type: str) -> dict:
    """Generate mock scout output for testing without LLM calls"""
    repo = TEST_REPOSITORIES[repo_type]

    return {
        "FINDINGS": [
            f"Found {len(repo['expected_findings']['hotspots'])} hotspots",
            f"Identified {len(repo['expected_findings']['integrations'])} integrations",
        ],
        "INTEGRATIONS": repo["expected_findings"]["integrations"],
        "RISKS": repo["expected_findings"]["risks"],
        "RECOMMENDATIONS": [
            "Add comprehensive error handling",
            "Implement connection pooling",
            "Add security scanning to CI/CD",
        ],
        "METRICS": {
            "files_analyzed": len(repo["files"]),
            "patterns_found": len(repo["expected_findings"]["hotspots"]),
            "execution_time": 2.5,
            "confidence": 0.75,
        },
    }
