#!/usr/bin/env python3
"""
API Key Validation Utility
Tests all external API connections with real keys - NO MOCKS
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv('.env.local')

class APIValidator:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def log(self, message, level="INFO"):
        """Log with timestamp and color coding."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[94m",      # Blue
            "SUCCESS": "\033[92m",   # Green
            "WARNING": "\033[93m",   # Yellow
            "ERROR": "\033[91m",     # Red
            "RESET": "\033[0m"       # Reset
        }
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{timestamp}] {level}: {message}{colors['RESET']}")

    async def test_openai_api(self):
        """Test OpenAI API connection."""
        self.log("Testing OpenAI API...")
        self.total_tests += 1
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "dummy-key":
            self.log("❌ OpenAI API key not found or is dummy", "ERROR")
            self.failed_tests += 1
            self.results["openai"] = {"status": "failed", "error": "Missing API key"}
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    models = response.json()
                    model_count = len(models.get("data", []))
                    self.log(f"✅ OpenAI API connected successfully - {model_count} models available", "SUCCESS")
                    self.passed_tests += 1
                    self.results["openai"] = {"status": "success", "models": model_count}
                    return True
                else:
                    self.log(f"❌ OpenAI API failed with status {response.status_code}: {response.text}", "ERROR")
                    self.failed_tests += 1
                    self.results["openai"] = {"status": "failed", "error": f"HTTP {response.status_code}"}
                    return False
                    
        except Exception as e:
            self.log(f"❌ OpenAI API connection failed: {e}", "ERROR")
            self.failed_tests += 1
            self.results["openai"] = {"status": "failed", "error": str(e)}
            return False

    async def test_anthropic_api(self):
        """Test Anthropic API connection."""
        self.log("Testing Anthropic API...")
        self.total_tests += 1
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self.log("❌ Anthropic API key not found", "ERROR")
            self.failed_tests += 1
            self.results["anthropic"] = {"status": "failed", "error": "Missing API key"}
            return False

        try:
            async with httpx.AsyncClient() as client:
                # Test with a minimal completion request
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}]
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log("✅ Anthropic API connected successfully", "SUCCESS")
                    self.passed_tests += 1
                    self.results["anthropic"] = {"status": "success", "model": "claude-3-haiku-20240307"}
                    return True
                else:
                    self.log(f"❌ Anthropic API failed with status {response.status_code}: {response.text}", "ERROR")
                    self.failed_tests += 1
                    self.results["anthropic"] = {"status": "failed", "error": f"HTTP {response.status_code}"}
                    return False
                    
        except Exception as e:
            self.log(f"❌ Anthropic API connection failed: {e}", "ERROR")
            self.failed_tests += 1
            self.results["anthropic"] = {"status": "failed", "error": str(e)}
            return False

    async def test_openrouter_api(self):
        """Test OpenRouter API connection."""
        self.log("Testing OpenRouter API...")
        self.total_tests += 1
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            self.log("❌ OpenRouter API key not found", "ERROR")
            self.failed_tests += 1
            self.results["openrouter"] = {"status": "failed", "error": "Missing API key"}
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    models = response.json()
                    model_count = len(models.get("data", []))
                    self.log(f"✅ OpenRouter API connected successfully - {model_count} models available", "SUCCESS")
                    self.passed_tests += 1
                    self.results["openrouter"] = {"status": "success", "models": model_count}
                    return True
                else:
                    self.log(f"❌ OpenRouter API failed with status {response.status_code}: {response.text}", "ERROR")
                    self.failed_tests += 1
                    self.results["openrouter"] = {"status": "failed", "error": f"HTTP {response.status_code}"}
                    return False
                    
        except Exception as e:
            self.log(f"❌ OpenRouter API connection failed: {e}", "ERROR")
            self.failed_tests += 1
            self.results["openrouter"] = {"status": "failed", "error": str(e)}
            return False

    async def test_qdrant_connection(self):
        """Test Qdrant vector database connection."""
        self.log("Testing Qdrant connection...")
        self.total_tests += 1
        
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not qdrant_url or not qdrant_api_key:
            self.log("❌ Qdrant URL or API key not found", "ERROR")
            self.failed_tests += 1
            self.results["qdrant"] = {"status": "failed", "error": "Missing credentials"}
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{qdrant_url}/collections",
                    headers={"api-key": qdrant_api_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    collections = response.json()
                    collection_count = len(collections.get("result", {}).get("collections", []))
                    self.log(f"✅ Qdrant connected successfully - {collection_count} collections", "SUCCESS")
                    self.passed_tests += 1
                    self.results["qdrant"] = {"status": "success", "collections": collection_count}
                    return True
                else:
                    self.log(f"❌ Qdrant failed with status {response.status_code}: {response.text}", "ERROR")
                    self.failed_tests += 1
                    self.results["qdrant"] = {"status": "failed", "error": f"HTTP {response.status_code}"}
                    return False
                    
        except Exception as e:
            self.log(f"❌ Qdrant connection failed: {e}", "ERROR")
            self.failed_tests += 1
            self.results["qdrant"] = {"status": "failed", "error": str(e)}
            return False

    async def test_redis_connection(self):
        """Test Redis connection."""
        self.log("Testing Redis connection...")
        self.total_tests += 1
        
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            self.log("❌ Redis URL not found", "ERROR")
            self.failed_tests += 1
            self.results["redis"] = {"status": "failed", "error": "Missing Redis URL"}
            return False

        try:
            import redis
            client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            result = client.ping()
            if result:
                info = client.info()
                version = info.get("redis_version", "unknown")
                self.log(f"✅ Redis connected successfully - version {version}", "SUCCESS")
                self.passed_tests += 1
                self.results["redis"] = {"status": "success", "version": version}
                client.close()
                return True
            else:
                self.log("❌ Redis ping failed", "ERROR")
                self.failed_tests += 1
                self.results["redis"] = {"status": "failed", "error": "Ping failed"}
                return False
                
        except Exception as e:
            self.log(f"❌ Redis connection failed: {e}", "ERROR")
            self.failed_tests += 1
            self.results["redis"] = {"status": "failed", "error": str(e)}
            return False

    async def test_portkey_gateway(self):
        """Test Portkey Gateway connection with proper 2025 configuration."""
        self.log("Testing Portkey Gateway...")
        self.total_tests += 1
        
        portkey_api_key = os.getenv("PORTKEY_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not portkey_api_key:
            self.log("❌ Portkey API key not found", "ERROR")
            self.failed_tests += 1
            self.results["portkey"] = {"status": "failed", "error": "Missing Portkey API key"}
            return False

        if not openai_api_key:
            self.log("❌ OpenAI API key not found (required for Portkey proxy)", "ERROR")
            self.failed_tests += 1
            self.results["portkey"] = {"status": "failed", "error": "Missing OpenAI API key for Portkey"}
            return False

        try:
            async with httpx.AsyncClient() as client:
                # Test Portkey with minimal configuration that works
                config_object = {
                    "retry": {
                        "attempts": 2
                    }
                }
                
                # Test with your real virtual key IDs from Portkey dashboard
                response = await client.post(
                    "https://api.portkey.ai/v1/chat/completions",
                    headers={
                        "x-portkey-api-key": portkey_api_key,
                        "x-portkey-virtual-key": "vkj-openrouter-cc4151",  # Your OpenRouter virtual key
                        "x-portkey-config": json.dumps(config_object),
                        "content-type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",  # Use OpenRouter model
                        "messages": [{"role": "user", "content": "test portkey virtual keys"}],
                        "max_tokens": 10
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log("✅ Portkey Gateway connected successfully with virtual keys", "SUCCESS")
                    self.passed_tests += 1
                    self.results["portkey"] = {"status": "success", "provider": "openai", "model": "gpt-3.5-turbo"}
                    return True
                else:
                    self.log(f"❌ Portkey failed with status {response.status_code}: {response.text}", "ERROR")
                    self.failed_tests += 1
                    self.results["portkey"] = {"status": "failed", "error": f"HTTP {response.status_code}"}
                    return False
                    
        except Exception as e:
            self.log(f"❌ Portkey connection failed: {e}", "ERROR")
            self.failed_tests += 1
            self.results["portkey"] = {"status": "failed", "error": str(e)}
            return False

    async def run_all_tests(self):
        """Run all API validation tests."""
        self.log("🚀 Starting API validation tests...", "INFO")
        self.log("=" * 60)
        
        # Run all tests
        tests = [
            self.test_openai_api(),
            self.test_anthropic_api(),
            self.test_openrouter_api(),
            self.test_qdrant_connection(),
            self.test_redis_connection(),
            self.test_portkey_gateway()
        ]
        
        await asyncio.gather(*tests, return_exceptions=True)
        
        # Print summary
        self.log("=" * 60)
        self.log("📊 VALIDATION SUMMARY", "INFO")
        self.log(f"Total Tests: {self.total_tests}")
        self.log(f"✅ Passed: {self.passed_tests}", "SUCCESS")
        self.log(f"❌ Failed: {self.failed_tests}", "ERROR")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        self.log(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests > 0:
            self.log("❌ DEPLOYMENT NOT READY - Fix failed APIs before proceeding", "ERROR")
            return False
        else:
            self.log("✅ ALL APIS VALIDATED - Ready for local deployment!", "SUCCESS")
            return True

    def save_results(self, filename="api_validation_results.json"):
        """Save results to JSON file."""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            },
            "results": self.results
        }
        
        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)
        
        self.log(f"📁 Results saved to {filename}")

async def main():
    """Main entry point."""
    validator = APIValidator()
    
    try:
        success = await validator.run_all_tests()
        validator.save_results()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        validator.log("\n⏹️  Validation cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        validator.log(f"💥 Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())