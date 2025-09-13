#!/usr/bin/env python3
"""
Test RAG Orchestrator Integration
Validates that --with-rag flag properly starts memory services
"""
import asyncio
import subprocess
import sys
from pathlib import Path
class RAGIntegrationTester:
    """Test RAG integration in unified orchestrator"""
    def __init__(self):
        self.test_results = {}
        self.base_dir = Path(__file__).parent.parent
    async def test_rag_flag_validation(self):
        """Test that --with-rag flag is recognized"""
        print("🧪 Testing --with-rag flag recognition...")
        try:
            # Test help output includes --with-rag
            result = subprocess.run(
                [sys.executable, "scripts/unified_orchestrator.py", "--help"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if "--with-rag" in result.stdout:
                self.test_results["rag_flag_recognized"] = "✅ PASS"
                print("  ✅ --with-rag flag found in help output")
            else:
                self.test_results["rag_flag_recognized"] = "❌ FAIL"
                print("  ❌ --with-rag flag not found in help output")
        except Exception as e:
            self.test_results["rag_flag_recognized"] = f"❌ ERROR: {e}"
            print(f"  ❌ Error testing flag recognition: {e}")
    async def test_rag_service_definitions(self):
        """Test that RAG services are properly defined"""
        print("\n🧪 Testing RAG service definitions...")
        try:
            # Import the orchestrator and check service definitions
            sys.path.append(str(self.base_dir / "scripts"))
            from unified_orchestrator import UnifiedOrchestrator
            orchestrator = UnifiedOrchestrator()
            config = orchestrator.config
            services = config.get("services", {})
            # Check sophia_memory service
            if "sophia_memory" in services:
                sophia_service = services["sophia_memory"]
                checks = {
                    "domain": sophia_service.get("domain") == "rag",
                    "port": sophia_service.get("port") == 8767,
                    "command": "sophia_memory" in sophia_service.get("command", ""),
                    "health_endpoint": sophia_service.get("health_endpoint")
                    == "/health",
                }
                if all(checks.values()):
                    self.test_results["sophia_memory_config"] = "✅ PASS"
                    print("  ✅ sophia_memory service properly configured")
                else:
                    self.test_results["sophia_memory_config"] = f"❌ FAIL: {checks}"
                    print(f"  ❌ sophia_memory config issues: {checks}")
            else:
                self.test_results["sophia_memory_config"] = "❌ FAIL: Service not found"
                print("  ❌ sophia_memory service not found in config")
            # Check _memory service
            if "_memory" in services:
                _service = services["_memory"]
                checks = {
                    "domain": _service.get("domain") == "rag",
                    "port": _service.get("port") == 8768,
                    "command": "_memory" in _service.get("command", ""),
                    "health_endpoint": _service.get("health_endpoint")
                    == "/health",
                }
                if all(checks.values()):
                    self.test_results["_memory_config"] = "✅ PASS"
                    print("  ✅ _memory service properly configured")
                else:
                    self.test_results["_memory_config"] = f"❌ FAIL: {checks}"
                    print(f"  ❌ _memory config issues: {checks}")
            else:
                self.test_results["_memory_config"] = (
                    "❌ FAIL: Service not found"
                )
                print("  ❌ _memory service not found in config")
        except Exception as e:
            self.test_results["service_definitions"] = f"❌ ERROR: {e}"
            print(f"  ❌ Error testing service definitions: {e}")
    async def test_rag_service_files(self):
        """Test that RAG service files exist and are executable"""
        print("\n🧪 Testing RAG service file availability...")
        rag_files = {
            "sophia_memory": self.base_dir / "app" / "memory" / "sophia_memory.py",
            "_memory": self.base_dir / "app" / "memory" / "_memory.py",
        }
        for service_name, file_path in rag_files.items():
            if file_path.exists():
                # Check if file has main entry point
                try:
                    content = file_path.read_text()
                    if 'if __name__ == "__main__"' in content and ".run()" in content:
                        self.test_results[f"{service_name}_file"] = "✅ PASS"
                        print(f"  ✅ {service_name}.py exists and is executable")
                    else:
                        self.test_results[f"{service_name}_file"] = (
                            "❌ FAIL: No main entry"
                        )
                        print(f"  ❌ {service_name}.py missing main entry point")
                except Exception as e:
                    self.test_results[f"{service_name}_file"] = f"❌ ERROR: {e}"
                    print(f"  ❌ Error reading {service_name}.py: {e}")
            else:
                self.test_results[f"{service_name}_file"] = "❌ FAIL: File not found"
                print(f"  ❌ {service_name}.py not found at {file_path}")
    async def test_dry_run_with_rag(self):
        """Test dry run with --with-rag flag"""
        print("\n🧪 Testing --with-rag dry run...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/unified_orchestrator.py",
                    "--with-rag",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
                timeout=30,
            )
            output = result.stdout + result.stderr
            # Check if RAG services are mentioned in dry run output
            rag_mentioned = "sophia_memory" in output or "_memory" in output
            if result.returncode == 0 and rag_mentioned:
                self.test_results["dry_run_with_rag"] = "✅ PASS"
                print("  ✅ Dry run with --with-rag completed successfully")
                print(f"    └─ Output contained RAG services: {rag_mentioned}")
            else:
                self.test_results["dry_run_with_rag"] = (
                    f"❌ FAIL: rc={result.returncode}, rag_mentioned={rag_mentioned}"
                )
                print(f"  ❌ Dry run failed: return code {result.returncode}")
                print(f"    └─ RAG services mentioned: {rag_mentioned}")
                if result.stderr:
                    print(f"    └─ Stderr: {result.stderr[:200]}...")
        except Exception as e:
            self.test_results["dry_run_with_rag"] = f"❌ ERROR: {e}"
            print(f"  ❌ Error during dry run test: {e}")
    async def test_service_startup_logic(self):
        """Test the _should_start_optional logic for RAG services"""
        print("\n🧪 Testing RAG service startup logic...")
        try:
            sys.path.append(str(self.base_dir / "scripts"))
            from unified_orchestrator import UnifiedOrchestrator
            orchestrator = UnifiedOrchestrator()
            # Test with --with-rag in sys.argv
            original_argv = sys.argv[:]
            # Test --with-rag
            sys.argv = ["unified_orchestrator.py", "--with-rag"]
            sophia_should_start = orchestrator._should_start_optional("sophia_memory")
            _should_start = orchestrator._should_start_optional("_memory")
            if sophia_should_start and _should_start:
                print("  ✅ --with-rag properly enables both RAG services")
                self.test_results["rag_startup_logic_with"] = "✅ PASS"
            else:
                print(
                    f"  ❌ --with-rag logic failed: sophia={sophia_should_start}, ={_should_start}"
                )
                self.test_results["rag_startup_logic_with"] = "❌ FAIL"
            # Test --no-rag
            sys.argv = ["unified_orchestrator.py", "--no-rag"]
            sophia_should_not_start = not orchestrator._should_start_optional(
                "sophia_memory"
            )
            _should_not_start = not orchestrator._should_start_optional(
                "_memory"
            )
            if sophia_should_not_start and _should_not_start:
                print("  ✅ --no-rag properly disables both RAG services")
                self.test_results["rag_startup_logic_no"] = "✅ PASS"
            else:
                print(
                    f"  ❌ --no-rag logic failed: sophia_disabled={sophia_should_not_start}, _disabled={_should_not_start}"
                )
                self.test_results["rag_startup_logic_no"] = "❌ FAIL"
            # Restore original argv
            sys.argv = original_argv
        except Exception as e:
            self.test_results["rag_startup_logic"] = f"❌ ERROR: {e}"
            print(f"  ❌ Error testing startup logic: {e}")
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("🧪 RAG INTEGRATION TEST SUMMARY")
        print("=" * 60)
        passed = sum(
            1 for result in self.test_results.values() if result.startswith("✅")
        )
        total = len(self.test_results)
        for test_name, result in self.test_results.items():
            print(f"{test_name.ljust(30)}: {result}")
        print(f"\n📊 Results: {passed}/{total} tests passed")
        if passed == total:
            print("🎉 All RAG integration tests passed!")
            print("✅ Phase A3: RAG orchestrator integration is complete")
        else:
            print("⚠️  Some tests failed - review implementation")
        print("=" * 60)
async def main():
    """Main test execution"""
    print("🚀 RAG Integration Test Suite")
    print("Testing --with-rag flag functionality in unified orchestrator\n")
    tester = RAGIntegrationTester()
    # Run all tests
    await tester.test_rag_flag_validation()
    await tester.test_rag_service_definitions()
    await tester.test_rag_service_files()
    await tester.test_dry_run_with_rag()
    await tester.test_service_startup_logic()
    # Print summary
    tester.print_summary()
if __name__ == "__main__":
    asyncio.run(main())
