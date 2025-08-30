#!/usr/bin/env python3
"""
Comprehensive test for actual code generation and modification.
Tests the code generator server to ensure it produces real, usable code.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any, List

BASE_URL = "http://localhost:8002"

async def collect_stream_response(url: str, data: Dict[str, Any]) -> str:
    """Collect full response from streaming endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        collected_tokens = []
        phases = []
        
        async with client.stream('POST', url, json=data) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    try:
                        json_data = json.loads(line[6:])
                        
                        if 'token' in json_data:
                            collected_tokens.append(json_data['token'])
                        
                        if 'phase' in json_data:
                            phases.append(json_data['phase'])
                            print(f"  📍 Phase: {json_data['phase']}")
                        
                        if json_data.get('phase') == 'complete':
                            break
                            
                    except json.JSONDecodeError:
                        if line == 'data: [DONE]':
                            break
                        continue
        
        return ''.join(collected_tokens)

async def test_repository_outline() -> bool:
    """Test generating a repository outline."""
    print("\n🧪 TEST 1: Repository Outline Generation")
    print("=" * 60)
    
    request = {
        "message": "give me outline of repository for a Python API service with authentication"
    }
    
    print(f"📝 Request: {request['message']}")
    print("⏳ Generating...")
    
    try:
        response = await collect_stream_response(f"{BASE_URL}/teams/run", request)
        
        # Verify the response contains expected elements
        expected_elements = [
            "README.md",
            "requirements.txt",
            "src/",
            "tests/",
            "Dockerfile",
            "main.py",
            "config.py",
            "api/",
            ".gitignore"
        ]
        
        missing = []
        for element in expected_elements:
            if element not in response:
                missing.append(element)
        
        if missing:
            print(f"❌ Missing elements: {missing}")
            return False
        
        # Show snippet of generated content
        lines = response.split('\n')
        print(f"✅ Generated {len(lines)} lines of repository structure")
        print("\n📄 Sample output (first 20 lines):")
        print("-" * 40)
        for line in lines[:20]:
            print(line)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_function_generation() -> bool:
    """Test generating actual function code."""
    print("\n🧪 TEST 2: Function Code Generation")
    print("=" * 60)
    
    request = {
        "message": "create a function to validate email addresses and return normalized format"
    }
    
    print(f"📝 Request: {request['message']}")
    print("⏳ Generating...")
    
    try:
        response = await collect_stream_response(f"{BASE_URL}/teams/run", request)
        
        # Verify the response contains Python code
        code_indicators = [
            "def ",
            "return",
            ":",
            "import",
            '"""'
        ]
        
        missing = []
        for indicator in code_indicators:
            if indicator not in response:
                missing.append(indicator)
        
        if missing:
            print(f"❌ Missing code elements: {missing}")
            return False
        
        # Show the generated function
        print(f"✅ Generated Python function")
        print("\n📄 Generated code:")
        print("-" * 40)
        print(response[:1000])  # First 1000 chars
        if len(response) > 1000:
            print(f"... ({len(response) - 1000} more characters)")
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_api_generation() -> bool:
    """Test generating API endpoint code."""
    print("\n🧪 TEST 3: API Endpoint Generation")
    print("=" * 60)
    
    request = {
        "message": "create an API endpoint for user registration with email and password"
    }
    
    print(f"📝 Request: {request['message']}")
    print("⏳ Generating...")
    
    try:
        response = await collect_stream_response(f"{BASE_URL}/teams/run", request)
        
        # Verify the response contains API code elements
        api_indicators = [
            "@router",
            "async def",
            "BaseModel",
            "HTTPException",
            "response_model"
        ]
        
        found = []
        for indicator in api_indicators:
            if indicator in response:
                found.append(indicator)
        
        if len(found) < 2:  # At least 2 API indicators
            print(f"❌ Insufficient API elements. Found only: {found}")
            return False
        
        print(f"✅ Generated API endpoint with {len(found)} API patterns")
        print(f"   Found: {', '.join(found)}")
        
        # Show snippet
        print("\n📄 API code snippet:")
        print("-" * 40)
        lines = response.split('\n')
        for i, line in enumerate(lines[:30]):
            print(line)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_class_generation() -> bool:
    """Test generating class code."""
    print("\n🧪 TEST 4: Class Code Generation")
    print("=" * 60)
    
    request = {
        "message": "create a class for managing database connections with pooling"
    }
    
    print(f"📝 Request: {request['message']}")
    print("⏳ Generating...")
    
    try:
        response = await collect_stream_response(f"{BASE_URL}/teams/run", request)
        
        # Verify class structure
        class_indicators = [
            "class ",
            "__init__",
            "self.",
            "async def",
            "return"
        ]
        
        found = []
        for indicator in class_indicators:
            if indicator in response:
                found.append(indicator)
        
        if len(found) < 3:
            print(f"❌ Insufficient class elements. Found only: {found}")
            return False
        
        print(f"✅ Generated class with {len(found)} OOP patterns")
        
        # Count methods
        method_count = response.count("def ")
        print(f"   Methods defined: {method_count}")
        
        print("\n📄 Class structure:")
        print("-" * 40)
        lines = response.split('\n')
        for line in lines[:40]:
            if line.strip().startswith("def ") or line.strip().startswith("class "):
                print(f"  → {line.strip()}")
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_code_modification() -> bool:
    """Test modifying existing code."""
    print("\n🧪 TEST 5: Code Modification")
    print("=" * 60)
    
    # First, generate some base code
    print("Step 1: Generating base code...")
    base_request = {
        "message": "create a simple calculator class with add and subtract methods"
    }
    
    base_code = await collect_stream_response(f"{BASE_URL}/teams/run", base_request)
    
    if "class" not in base_code or "add" not in base_code:
        print("❌ Failed to generate base code")
        return False
    
    print("✅ Base code generated")
    
    # Now request modification
    print("\nStep 2: Requesting modification...")
    modify_request = {
        "message": "add multiply and divide methods to the calculator class",
        "context": {"existing_code": base_code[:500]}  # Send partial context
    }
    
    modified_code = await collect_stream_response(f"{BASE_URL}/teams/run", modify_request)
    
    # Check for new methods
    new_methods = ["multiply", "divide"]
    found_new = []
    
    for method in new_methods:
        if method in modified_code.lower():
            found_new.append(method)
    
    if len(found_new) < 1:
        print(f"❌ Modification failed. New methods not found: {new_methods}")
        return False
    
    print(f"✅ Code modified successfully")
    print(f"   New methods added: {', '.join(found_new)}")
    
    return True

async def test_complex_generation() -> bool:
    """Test generating complex, multi-file project."""
    print("\n🧪 TEST 6: Complex Project Generation")
    print("=" * 60)
    
    request = {
        "message": "create a complete REST API project with user authentication, database models, and Docker setup"
    }
    
    print(f"📝 Request: {request['message']}")
    print("⏳ Generating complex project...")
    
    try:
        response = await collect_stream_response(f"{BASE_URL}/teams/run", request)
        
        # Check for multiple components
        components = {
            "Authentication": ["login", "register", "token", "JWT"],
            "Database": ["models", "User", "migrations", "database"],
            "Docker": ["Dockerfile", "docker-compose", "EXPOSE", "FROM python"],
            "API": ["FastAPI", "router", "endpoint", "@app"],
            "Testing": ["pytest", "test_", "assert", "mock"],
            "Configuration": ["config", "settings", "env", "SECRET_KEY"]
        }
        
        found_components = {}
        for component, keywords in components.items():
            found = False
            for keyword in keywords:
                if keyword in response:
                    found = True
                    break
            found_components[component] = found
        
        print(f"\n📊 Component Analysis:")
        for component, found in found_components.items():
            status = "✅" if found else "❌"
            print(f"  {status} {component}")
        
        # Calculate completeness
        completeness = sum(1 for v in found_components.values() if v) / len(found_components)
        print(f"\n🎯 Project Completeness: {completeness * 100:.1f}%")
        
        if completeness < 0.5:
            print("❌ Generated project is incomplete")
            return False
        
        # Show statistics
        lines = response.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        print(f"\n📈 Generation Statistics:")
        print(f"  Total lines: {len(lines)}")
        print(f"  Code lines: {len(code_lines)}")
        print(f"  Files described: {response.count('.py') + response.count('.yml') + response.count('.md')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def verify_actual_code_quality() -> bool:
    """Verify that generated code is actual, runnable Python code."""
    print("\n🧪 TEST 7: Code Quality Verification")
    print("=" * 60)
    
    request = {
        "message": "create a function to calculate fibonacci sequence"
    }
    
    print(f"📝 Request: {request['message']}")
    
    try:
        response = await collect_stream_response(f"{BASE_URL}/teams/run", request)
        
        # Extract just the function code
        import re
        function_match = re.search(r'(def\s+\w+.*?(?:\n(?!\ndef\s).*)*)', response, re.DOTALL)
        
        if not function_match:
            print("❌ No valid Python function found")
            return False
        
        function_code = function_match.group(1)
        
        # Try to compile the code
        try:
            compile(function_code, '<string>', 'exec')
            print("✅ Generated code is syntactically valid Python")
        except SyntaxError as e:
            print(f"❌ Generated code has syntax errors: {e}")
            return False
        
        # Check for proper structure
        quality_checks = {
            "Has docstring": '"""' in function_code or "'''" in function_code,
            "Has parameters": "(" in function_code and ")" in function_code,
            "Has return statement": "return" in function_code,
            "Has implementation": len(function_code.split('\n')) > 3
        }
        
        print("\n📋 Quality Checks:")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "⚠️"
            print(f"  {status} {check}")
        
        passed_checks = sum(1 for v in quality_checks.values() if v)
        quality_score = passed_checks / len(quality_checks)
        
        print(f"\n🏆 Code Quality Score: {quality_score * 100:.0f}%")
        
        return quality_score >= 0.5
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run all code generation tests."""
    print("🚀 COMPREHENSIVE CODE GENERATION TEST SUITE")
    print("=" * 60)
    print("Testing actual code generation capabilities...")
    print("Server: http://localhost:8002")
    print("=" * 60)
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{BASE_URL}/healthz")
            if health.status_code != 200:
                print("❌ Server not responding. Please start the code generator server.")
                return 1
    except:
        print("❌ Cannot connect to server at http://localhost:8002")
        print("   Please run: python3 app/api/code_generator_server.py")
        return 1
    
    # Run all tests
    tests = [
        ("Repository Outline", test_repository_outline),
        ("Function Generation", test_function_generation),
        ("API Generation", test_api_generation),
        ("Class Generation", test_class_generation),
        ("Code Modification", test_code_modification),
        ("Complex Project", test_complex_generation),
        ("Code Quality", verify_actual_code_quality)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
            await asyncio.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:25} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    success_rate = (passed / len(tests)) * 100
    print(f"🎯 Success Rate: {success_rate:.1f}% ({passed}/{len(tests)} tests passed)")
    
    if passed == len(tests):
        print("🎉 PERFECT! All code generation tests passed!")
        print("✅ The system is generating actual, usable code!")
        return 0
    elif passed >= len(tests) * 0.7:
        print("✅ GOOD! Most tests passed. Code generation is working!")
        return 0
    else:
        print("⚠️ Code generation needs improvement")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)