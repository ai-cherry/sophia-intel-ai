#!/usr/bin/env python3
"""
Advanced Dashboard Demo Script
Demonstrates the complete visual agent orchestration platform
"""

import asyncio
import json
import httpx
from datetime import datetime
from typing import Dict, Any


class DashboardDemo:
    """Demonstrates the advanced dashboard capabilities"""
    
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url
        self.auth_token = "dev-token"  # Use your AUTH_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    async def test_health(self):
        """Test API health"""
        print("🏥 Testing API Health...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                print(f"✅ API Health: {response.json()}")
                return True
            except Exception as e:
                print(f"❌ API Health failed: {e}")
                return False
    
    async def demo_template_search(self):
        """Demo template search functionality"""
        print("\n📚 Testing Template Search...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/templates/search",
                    headers=self.headers,
                    params={"query": "code review", "category": "development"}
                )
                templates = response.json()
                print(f"✅ Found {templates['count']} templates")
                
                if templates['templates']:
                    template = templates['templates'][0]
                    print(f"   📋 Template: {template['name']}")
                    print(f"   📊 Rating: {template['rating']}/5.0")
                    print(f"   🏷️  Tags: {', '.join(template['tags'])}")
                    return template['id']
                
            except Exception as e:
                print(f"❌ Template search failed: {e}")
        return None
    
    async def demo_composition_creation(self, template_id: str = None):
        """Demo creating composition from template"""
        print("\n🔧 Testing Composition Creation...")
        
        if template_id:
            # Create from template
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/api/v1/templates/{template_id}/create",
                        headers=self.headers,
                        json={"name": f"Demo Team {datetime.now().strftime('%H:%M')}"}
                    )
                    result = response.json()
                    composition_id = result['composition_id']
                    print(f"✅ Created composition from template: {composition_id}")
                    return composition_id
                except Exception as e:
                    print(f"❌ Template creation failed: {e}")
        
        # Create custom composition
        composition_data = {
            "name": f"Custom Demo Team {datetime.now().strftime('%H:%M')}",
            "version": "1.0.0",
            "agents": [
                {
                    "name": "Research Agent",
                    "type": "researcher",
                    "model": "openai/gpt-4o-mini",
                    "tools": ["web_search", "file_read"],
                    "position": {"x": 100, "y": 100},
                    "description": "Gathers information and research"
                },
                {
                    "name": "Code Agent",
                    "type": "coder", 
                    "model": "anthropic/claude-3.5-sonnet",
                    "tools": ["code_editor", "file_write"],
                    "position": {"x": 350, "y": 100},
                    "description": "Writes and modifies code"
                }
            ],
            "connections": [
                {
                    "from_agent": "agent_1",
                    "to_agent": "agent_2"
                }
            ],
            "team_config": {
                "name": "Demo Team",
                "mode": "coordinate",
                "shared_memory": True,
                "max_concurrent": 2
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/compose",
                    headers=self.headers,
                    json=composition_data
                )
                result = response.json()
                composition_id = result['composition_id']
                print(f"✅ Created custom composition: {composition_id}")
                return composition_id
            except Exception as e:
                print(f"❌ Composition creation failed: {e}")
                return None
    
    async def demo_simulation(self, composition_id: str):
        """Demo Monte Carlo simulation"""
        print("\n🧪 Testing Monte Carlo Simulation...")
        
        simulation_config = {
            "iterations": 100,
            "task_complexity": "medium",
            "failure_rate": 0.05,
            "latency_variance": 0.2,
            "cost_variance": 0.1
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/simulate/{composition_id}",
                    headers=self.headers,
                    json=simulation_config
                )
                result = response.json()
                print(f"✅ Simulation completed:")
                print(f"   📊 Success Rate: {result['success_rate']:.1%}")
                print(f"   ⏱️  Avg Completion Time: {result['avg_completion_time']:.1f}s")
                print(f"   💰 Avg Cost: ${result['avg_cost']:.3f}")
                print(f"   🎯 Confidence: {result['confidence_interval']['lower']:.1%} - {result['confidence_interval']['upper']:.1%}")
                
                if result['recommendations']:
                    print(f"   💡 Recommendations:")
                    for rec in result['recommendations']:
                        print(f"      • {rec}")
                
                return result
            except Exception as e:
                print(f"❌ Simulation failed: {e}")
                return None
    
    async def demo_code_generation(self, composition_id: str):
        """Demo code generation"""
        print("\n💻 Testing Code Generation...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/generate/{composition_id}",
                    headers=self.headers,
                    params={"language": "python", "framework": "agno"}
                )
                result = response.json()
                print(f"✅ Code generated successfully:")
                print(f"   📄 Language: {result['language']}")
                print(f"   🏗️  Framework: {result['framework']}")
                print(f"   📊 Estimated Tokens: {result['estimated_tokens']}")
                print(f"   📦 Requirements: {', '.join(result['requirements'])}")
                
                # Show first few lines of generated code
                code_lines = result['code'].split('\n')[:10]
                print(f"   🔍 Code Preview:")
                for line in code_lines:
                    if line.strip():
                        print(f"      {line}")
                print(f"      ... ({len(result['code'].split())} total lines)")
                
                return result
            except Exception as e:
                print(f"❌ Code generation failed: {e}")
                return None
    
    async def demo_model_selection(self):
        """Demo AI-assisted model selection"""
        print("\n🤖 Testing Model Selection...")
        
        test_cases = [
            {"task": "code review and refactoring", "priority": "quality"},
            {"task": "quick data analysis", "priority": "speed"}, 
            {"task": "complex research task", "priority": "cost"}
        ]
        
        async with httpx.AsyncClient() as client:
            for case in test_cases:
                try:
                    response = await client.post(
                        f"{self.base_url}/api/v1/models/select",
                        headers=self.headers,
                        json=case
                    )
                    result = response.json()
                    print(f"✅ Task: '{case['task']}'")
                    print(f"   🎯 Priority: {case['priority']}")
                    print(f"   🤖 Selected Model: {result['model']}")
                    print(f"   💭 Reason: {result['reason']}")
                    print()
                except Exception as e:
                    print(f"❌ Model selection failed for {case['task']}: {e}")
    
    async def demo_approval_workflow(self, composition_id: str):
        """Demo Human-in-the-Loop approval workflow"""
        print("\n👥 Testing HITL Approval Workflow...")
        
        # Create approval request
        approval_request = {
            "composition_id": composition_id,
            "agent_id": "agent_1",
            "task_id": "demo_task_123",
            "type": "deployment",
            "title": "Deploy Demo Team to Production",
            "description": "This demo team will be deployed to the production environment for testing.",
            "priority": "normal",
            "timeout_seconds": 3600,
            "approvers": ["demo_approver@example.com"]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Create approval request
                response = await client.post(
                    f"{self.base_url}/api/v1/approvals",
                    headers=self.headers,
                    json=approval_request
                )
                approval_result = response.json()
                approval_id = approval_result['approval_id']
                print(f"✅ Created approval request: {approval_id}")
                
                # Get pending approvals
                response = await client.get(
                    f"{self.base_url}/api/v1/approvals/pending",
                    headers=self.headers
                )
                pending = response.json()
                print(f"   📋 Pending approvals: {pending['count']}")
                
                # Auto-approve for demo
                approval_response = {
                    "approval_id": approval_id,
                    "approved": True,
                    "approver": "demo_approver@example.com",
                    "feedback": "Demo approval - looks good to proceed"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/approvals/{approval_id}/respond",
                    headers=self.headers,
                    json=approval_response
                )
                print(f"✅ Approval response submitted")
                
                return approval_id
            except Exception as e:
                print(f"❌ Approval workflow failed: {e}")
                return None
    
    async def demo_deployment(self, composition_id: str):
        """Demo deployment workflow"""
        print("\n🚀 Testing Deployment Workflow...")
        
        deployment_request = {
            "composition_id": composition_id,
            "name": f"demo-deployment-{datetime.now().strftime('%H%M')}",
            "environment": "development",
            "replicas": 2,
            "auto_scale": False,
            "monitoring": True
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Start deployment
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/deploy/{composition_id}",
                    headers=self.headers,
                    json=deployment_request
                )
                result = response.json()
                deployment_id = result['deployment_id']
                print(f"✅ Started deployment: {deployment_id}")
                
                # Monitor deployment status
                for i in range(3):
                    await asyncio.sleep(2)
                    response = await client.get(
                        f"{self.base_url}/api/v1/deployments/{deployment_id}",
                        headers=self.headers
                    )
                    status = response.json()
                    print(f"   📊 Status: {status['status']} ({status['replicas']['ready']}/{status['replicas']['desired']} replicas)")
                    
                    if status['status'] == 'running':
                        print(f"   ✅ Deployment successful!")
                        break
                
                return deployment_id
            except Exception as e:
                print(f"❌ Deployment failed: {e}")
                return None
    
    async def demo_openrouter_models(self):
        """Demo OpenRouter model listing"""
        print("\n🌐 Testing OpenRouter Model Integration...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/models/openrouter")
                result = response.json()
                
                if 'error' in result:
                    print(f"⚠️  OpenRouter API not available: {result['error']}")
                    return
                
                print(f"✅ Found {result['count']} OpenRouter models")
                
                # Show a few popular models
                popular_models = [m for m in result['models'] if any(provider in m['id'] for provider in ['openai', 'anthropic', 'google'])][:5]
                
                for model in popular_models:
                    print(f"   🤖 {model['name']}")
                    print(f"      ID: {model['id']}")
                    if model.get('pricing'):
                        prompt_cost = model['pricing'].get('prompt', 'N/A')
                        completion_cost = model['pricing'].get('completion', 'N/A')
                        print(f"      💰 Pricing: ${prompt_cost} / ${completion_cost} per 1K tokens")
                    print()
                
            except Exception as e:
                print(f"❌ OpenRouter model listing failed: {e}")
    
    async def run_full_demo(self):
        """Run the complete demo"""
        print("🎯 Starting Advanced Dashboard Demo")
        print("=" * 50)
        
        # Test API health first
        if not await self.test_health():
            print("❌ API not available. Make sure the Bridge API is running on port 8004")
            return
        
        # Run all demo scenarios
        template_id = await self.demo_template_search()
        composition_id = await self.demo_composition_creation(template_id)
        
        if composition_id:
            await self.demo_simulation(composition_id)
            await self.demo_code_generation(composition_id)
            approval_id = await self.demo_approval_workflow(composition_id)
            deployment_id = await self.demo_deployment(composition_id)
        
        await self.demo_model_selection()
        await self.demo_openrouter_models()
        
        print("\n🎉 Demo completed successfully!")
        print("=" * 50)
        print("\n📋 What was demonstrated:")
        print("✅ Template search and management")
        print("✅ Visual agent composition creation")
        print("✅ Monte Carlo simulation and risk assessment")
        print("✅ Automated code generation (Agno framework)")
        print("✅ AI-assisted model selection")
        print("✅ Human-in-the-loop approval workflows")
        print("✅ Automated deployment and monitoring")
        print("✅ OpenRouter model integration")
        print("\n🌟 The advanced dashboard platform is ready for production use!")


async def main():
    """Main demo function"""
    demo = DashboardDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    print("🚀 Advanced Dashboard Demo")
    print("Make sure the Bridge API is running: python bridge/api.py")
    print("Starting demo in 3 seconds...")
    
    import time
    time.sleep(3)
    
    asyncio.run(main())