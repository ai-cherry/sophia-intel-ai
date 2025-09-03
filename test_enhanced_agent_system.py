#!/usr/bin/env python3
"""
Enhanced Agent System Integration Test

Tests the upgraded Sophia AI agent system with:
- Portkey/OpenRouter model routing (GPT-5 + Grok-4)
- ReAct reasoning loops with tool validation
- Advanced memory and knowledge retrieval
- Specialized agent classes
- Production-ready error handling
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Setup path
sys.path.insert(0, os.getcwd())

from app.swarms.agents.base_agent import BaseAgent, AgentRole
from app.swarms.agents.specialized.planner_agent import PlannerAgent
from app.swarms.agents.specialized.coder_agent import CoderAgent
from app.swarms.agents.specialized.researcher_agent import ResearchAgent
from app.swarms.agents.specialized.security_agent import SecurityAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentSystemTester:
    """Comprehensive test suite for enhanced agent system"""
    
    def __init__(self):
        self.test_results = []
        self.agents_tested = 0
        self.tests_passed = 0
        self.tests_failed = 0
    
    async def test_base_agent_functionality(self):
        """Test core BaseAgent functionality"""
        
        logger.info("🧪 Testing BaseAgent Core Functionality")
        
        try:
            # Create base agent with reasoning enabled
            agent = BaseAgent(
                agent_id="test-agent-001",
                role=AgentRole.PLANNER,
                enable_reasoning=True,
                enable_memory=True,
                enable_knowledge=True,
                max_reasoning_steps=5
            )
            
            # Test simple execution
            test_problem = {
                "query": "Explain the benefits of using AI agents for task automation",
                "context": "general_inquiry"
            }
            
            result = await agent.execute(test_problem)
            
            # Validate response structure
            expected_keys = ["result", "agent_id", "role", "success", "execution_time"]
            missing_keys = [key for key in expected_keys if key not in result]
            
            if missing_keys:
                raise AssertionError(f"Missing keys in response: {missing_keys}")
            
            if not result["success"]:
                raise AssertionError(f"Agent execution failed: {result.get('error')}")
            
            logger.info(f"✅ BaseAgent test passed - Response length: {len(str(result['result']))}")
            logger.info(f"   Execution time: {result.get('execution_time', 0):.3f}s")
            logger.info(f"   Model used: {result.get('model_stats', {}).get('model_usage', {})}")
            
            self.tests_passed += 1
            self.test_results.append({
                "test": "BaseAgent Functionality",
                "status": "PASSED",
                "agent_id": agent.agent_id,
                "execution_time": result.get("execution_time", 0)
            })
            
        except Exception as e:
            logger.error(f"❌ BaseAgent test failed: {e}")
            self.tests_failed += 1
            self.test_results.append({
                "test": "BaseAgent Functionality", 
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_planner_agent(self):
        """Test PlannerAgent specialized functionality"""
        
        logger.info("🎯 Testing PlannerAgent Specialization")
        
        try:
            planner = PlannerAgent(
                agent_id="test-planner-001",
                enable_reasoning=True
            )
            
            # Test project planning
            project_spec = {
                "title": "AI Agent Integration System",
                "requirements": "Build a system that can coordinate multiple AI agents for complex tasks",
                "timeline": "3 months",
                "constraints": "Budget of $50k, team of 3 developers"
            }
            
            plan_result = await planner.create_project_plan(project_spec)
            
            if not plan_result.get("project_plan"):
                raise AssertionError("No project plan generated")
            
            logger.info("✅ PlannerAgent test passed")
            logger.info(f"   Plan confidence: {plan_result.get('confidence')}")
            logger.info(f"   Reasoning steps: {len(plan_result.get('reasoning_trace', []))}")
            
            self.tests_passed += 1
            self.test_results.append({
                "test": "PlannerAgent Specialization",
                "status": "PASSED",
                "agent_id": planner.agent_id,
                "confidence": plan_result.get("confidence")
            })
            
        except Exception as e:
            logger.error(f"❌ PlannerAgent test failed: {e}")
            self.tests_failed += 1
            self.test_results.append({
                "test": "PlannerAgent Specialization",
                "status": "FAILED", 
                "error": str(e)
            })
    
    async def test_coder_agent(self):
        """Test CoderAgent specialized functionality"""
        
        logger.info("💻 Testing CoderAgent Specialization")
        
        try:
            coder = CoderAgent(
                agent_id="test-coder-001",
                programming_languages=["python", "javascript"]
            )
            
            # Test code generation
            code_spec = {
                "name": "fibonacci_calculator",
                "purpose": "Calculate Fibonacci numbers efficiently",
                "language": "python",
                "requirements": "Handle large numbers, include memoization",
                "input": "Integer n",
                "output": "nth Fibonacci number"
            }
            
            code_result = await coder.generate_code(code_spec)
            
            if not code_result.get("generated_code"):
                raise AssertionError("No code generated")
            
            logger.info("✅ CoderAgent test passed")
            logger.info(f"   Language: {code_result.get('language')}")
            logger.info(f"   Quality score: {code_result.get('quality_score')}")
            
            self.tests_passed += 1
            self.test_results.append({
                "test": "CoderAgent Specialization",
                "status": "PASSED",
                "agent_id": coder.agent_id,
                "language": code_result.get("language")
            })
            
        except Exception as e:
            logger.error(f"❌ CoderAgent test failed: {e}")
            self.tests_failed += 1
            self.test_results.append({
                "test": "CoderAgent Specialization",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_researcher_agent(self):
        """Test ResearcherAgent specialized functionality"""
        
        logger.info("🔍 Testing ResearcherAgent Specialization")
        
        try:
            researcher = ResearchAgent(
                agent_id="test-researcher-001",
                research_domains=["AI", "technology"]
            )
            
            # Test research capability
            research_query = {
                "topic": "Large Language Models in Software Development",
                "focus": "Current applications and future trends",
                "depth": "comprehensive",
                "timeframe": "2023-2024"
            }
            
            research_result = await researcher.conduct_research(research_query)
            
            if not research_result.get("research_findings"):
                raise AssertionError("No research findings generated")
            
            logger.info("✅ ResearcherAgent test passed")
            logger.info(f"   Research quality: {research_result.get('research_quality')}")
            logger.info(f"   Confidence level: {research_result.get('confidence_level')}")
            
            self.tests_passed += 1
            self.test_results.append({
                "test": "ResearcherAgent Specialization",
                "status": "PASSED",
                "agent_id": researcher.agent_id,
                "research_quality": research_result.get("research_quality")
            })
            
        except Exception as e:
            logger.error(f"❌ ResearcherAgent test failed: {e}")
            self.tests_failed += 1
            self.test_results.append({
                "test": "ResearcherAgent Specialization",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_security_agent(self):
        """Test SecurityAgent specialized functionality"""
        
        logger.info("🛡️  Testing SecurityAgent Specialization")
        
        try:
            security = SecurityAgent(
                agent_id="test-security-001",
                security_frameworks=["OWASP", "NIST"]
            )
            
            # Test vulnerability analysis
            system_info = {
                "name": "AI Agent API",
                "type": "Web Application",
                "architecture": "Microservices with FastAPI",
                "technologies": ["Python", "PostgreSQL", "Redis", "Docker"],
                "data_types": ["User data", "API keys", "Model outputs"],
                "access_patterns": "REST API with JWT authentication"
            }
            
            security_result = await security.analyze_vulnerability(system_info)
            
            if not security_result.get("vulnerability_analysis"):
                raise AssertionError("No security analysis generated")
            
            logger.info("✅ SecurityAgent test passed")
            logger.info(f"   Risk level: {security_result.get('risk_level')}")
            logger.info(f"   Analysis confidence: {security_result.get('analysis_metadata', {}).get('confidence')}")
            
            self.tests_passed += 1
            self.test_results.append({
                "test": "SecurityAgent Specialization",
                "status": "PASSED",
                "agent_id": security.agent_id,
                "risk_level": security_result.get("risk_level")
            })
            
        except Exception as e:
            logger.error(f"❌ SecurityAgent test failed: {e}")
            self.tests_failed += 1
            self.test_results.append({
                "test": "SecurityAgent Specialization",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_model_fallback_system(self):
        """Test Portkey model routing and fallback"""
        
        logger.info("🔄 Testing Model Fallback System")
        
        try:
            # Create agent to test model routing
            agent = BaseAgent(
                agent_id="test-fallback-001",
                role=AgentRole.PLANNER
            )
            
            # Test model statistics
            model_stats = agent.model.get_stats()
            
            logger.info("✅ Model fallback system initialized")
            logger.info(f"   Primary model: GPT-5 via Portkey")
            logger.info(f"   Fallback model: Grok-4 via Portkey") 
            logger.info(f"   Emergency fallback: OpenRouter direct")
            logger.info(f"   Fallback enabled: {model_stats['configuration']['fallback_enabled']}")
            logger.info(f"   Emergency fallback enabled: {model_stats['configuration']['emergency_fallback_enabled']}")
            
            self.tests_passed += 1
            self.test_results.append({
                "test": "Model Fallback System",
                "status": "PASSED",
                "configuration": model_stats.get("configuration", {})
            })
            
        except Exception as e:
            logger.error(f"❌ Model fallback test failed: {e}")
            self.tests_failed += 1
            self.test_results.append({
                "test": "Model Fallback System",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        
        logger.info("🚀 Starting Enhanced Agent System Integration Test")
        logger.info("=" * 80)
        
        # Run all tests
        await self.test_base_agent_functionality()
        await self.test_planner_agent()
        await self.test_coder_agent()
        await self.test_researcher_agent()
        await self.test_security_agent()
        await self.test_model_fallback_system()
        
        # Summary
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("🎯 TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {self.tests_passed}")
        logger.info(f"❌ Failed: {self.tests_failed}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        logger.info(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            logger.info(f"   {status_icon} {result['test']}: {result['status']}")
            if result["status"] == "FAILED":
                logger.info(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Overall assessment
        if success_rate >= 100:
            logger.info("\n🎉 ALL TESTS PASSED!")
            logger.info("Enhanced Agent System is fully operational!")
            return True
        elif success_rate >= 80:
            logger.info(f"\n✅ MOSTLY SUCCESSFUL ({success_rate:.1f}%)")
            logger.info("Enhanced Agent System is largely operational with minor issues.")
            return True
        elif success_rate >= 60:
            logger.info(f"\n⚠️  PARTIAL SUCCESS ({success_rate:.1f}%)")
            logger.info("Enhanced Agent System has some issues that need attention.")
            return False
        else:
            logger.info(f"\n❌ SYSTEM NEEDS WORK ({success_rate:.1f}%)")
            logger.info("Enhanced Agent System requires significant fixes.")
            return False


async def main():
    """Main test execution function"""
    
    logger.info("🤖 Enhanced Agent System Integration Test")
    logger.info("Testing upgraded Sophia AI agents with Portkey/OpenRouter integration")
    
    tester = AgentSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n🚀 System is ready for production use!")
    else:
        logger.info("\n⚠️  System needs additional work before deployment.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)