#!/usr/bin/env python3
"""
Orchestration and automation systems testing script
Tests n8n, LangGraph, and agent systems
"""

import os
import sys
import json
import time
import requests
import subprocess
from typing import Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_environment():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env.remediation', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        print("Warning: .env.remediation file not found")
    return env_vars

def test_n8n_access():
    """Test n8n workflow automation access"""
    print("\n=== Testing n8n Workflow Automation ===")
    
    # Try different n8n endpoints
    n8n_endpoints = [
        "https://n8n.sophia-intel.ai",
        "https://app.n8n.cloud/workflow",
        "https://n8n.cloud"
    ]
    
    for endpoint in n8n_endpoints:
        print(f"\nTrying n8n endpoint: {endpoint}")
        
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ n8n endpoint accessible")
                
                # Check if it's the login page
                if 'login' in response.text.lower() or 'sign in' in response.text.lower():
                    print("📝 Login page detected")
                    return {
                        "status": "ACCESSIBLE", 
                        "endpoint": endpoint,
                        "requires_login": True
                    }
                else:
                    print("✅ n8n dashboard accessible")
                    return {
                        "status": "OK", 
                        "endpoint": endpoint,
                        "requires_login": False
                    }
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
    
    return {"status": "ERROR", "message": "All n8n endpoints failed"}

def test_langgraph_installation():
    """Test LangGraph installation and basic functionality"""
    print("\n=== Testing LangGraph Installation ===")
    
    try:
        # Check if LangGraph is installed
        import langgraph
        print(f"✅ LangGraph installed: version {langgraph.__version__}")
        
        # Test basic LangGraph functionality
        from langgraph.graph import Graph
        
        # Create a simple test graph
        def test_node(state):
            return {"message": "LangGraph test successful"}
        
        graph = Graph()
        graph.add_node("test", test_node)
        graph.set_entry_point("test")
        graph.set_finish_point("test")
        
        compiled_graph = graph.compile()
        result = compiled_graph.invoke({"input": "test"})
        
        print("✅ LangGraph basic functionality working")
        print(f"Test result: {result}")
        
        return {
            "status": "OK",
            "version": langgraph.__version__,
            "test_result": result
        }
        
    except ImportError as e:
        print(f"❌ LangGraph not installed: {str(e)}")
        print("Installing LangGraph...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "langgraph>=0.2.40"])
            print("✅ LangGraph installed successfully")
            return {"status": "INSTALLED", "message": "Newly installed"}
        except Exception as install_error:
            print(f"❌ Failed to install LangGraph: {str(install_error)}")
            return {"status": "ERROR", "message": f"Installation failed: {str(install_error)}"}
            
    except Exception as e:
        print(f"❌ LangGraph test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_agent_system():
    """Test the existing agent system"""
    print("\n=== Testing Sophia Agent System ===")
    
    try:
        # Import the agent system
        from agents.base_agent import BaseAgent, Status
        from agents.coding_agent import CodingAgent
        
        print("✅ Agent system imports successful")
        
        # Test base agent functionality
        print("Testing base agent status system...")
        
        # Check if we can create a coding agent
        try:
            coding_agent = CodingAgent(name="test-coding-agent")
            print(f"✅ Coding agent created: {coding_agent.name}")
            print(f"Status: {coding_agent.status}")
            print(f"Concurrency: {coding_agent.concurrency}")
            
            return {
                "status": "OK",
                "agents_available": ["BaseAgent", "CodingAgent"],
                "test_agent": {
                    "name": coding_agent.name,
                    "status": coding_agent.status.value,
                    "concurrency": coding_agent.concurrency
                }
            }
            
        except Exception as agent_error:
            print(f"⚠️ Agent creation failed: {str(agent_error)}")
            return {
                "status": "PARTIAL",
                "message": "Imports work but agent creation failed",
                "error": str(agent_error)
            }
            
    except ImportError as e:
        print(f"❌ Agent system import failed: {str(e)}")
        return {"status": "ERROR", "message": f"Import failed: {str(e)}"}
    except Exception as e:
        print(f"❌ Agent system test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_agno_phidata():
    """Test Agno/Phidata integration"""
    print("\n=== Testing Agno/Phidata Integration ===")
    
    # Check if Agno or Phidata are installed or referenced
    agno_found = False
    phidata_found = False
    
    try:
        import agno
        agno_found = True
        print("✅ Agno found")
    except ImportError:
        print("❌ Agno not installed")
    
    try:
        import phidata
        phidata_found = True
        print("✅ Phidata found")
    except ImportError:
        print("❌ Phidata not installed")
    
    if not agno_found and not phidata_found:
        print("ℹ️ Neither Agno nor Phidata are installed")
        print("Checking if they should be installed...")
        
        # Check if they're mentioned in any config files
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read().lower()
                if 'agno' in requirements:
                    print("📋 Agno found in requirements.txt")
                if 'phidata' in requirements:
                    print("📋 Phidata found in requirements.txt")
        except FileNotFoundError:
            pass
        
        return {
            "status": "NOT_INSTALLED",
            "message": "Agno and Phidata not found",
            "recommendation": "Install if needed for specific workflows"
        }
    
    return {
        "status": "PARTIAL" if agno_found or phidata_found else "NOT_INSTALLED",
        "agno_available": agno_found,
        "phidata_available": phidata_found
    }

def test_workflow_dependencies():
    """Test workflow and orchestration dependencies"""
    print("\n=== Testing Workflow Dependencies ===")
    
    dependencies_to_test = [
        "haystack-ai",
        "mem0ai", 
        "langchain-openai",
        "langchain-community",
        "sentence-transformers"
    ]
    
    results = {}
    
    for dep in dependencies_to_test:
        try:
            # Try to import the package
            if dep == "haystack-ai":
                import haystack
                results[dep] = {"status": "OK", "version": getattr(haystack, '__version__', 'unknown')}
            elif dep == "mem0ai":
                import mem0
                results[dep] = {"status": "OK", "version": getattr(mem0, '__version__', 'unknown')}
            elif dep == "langchain-openai":
                import langchain_openai
                results[dep] = {"status": "OK", "version": getattr(langchain_openai, '__version__', 'unknown')}
            elif dep == "langchain-community":
                import langchain_community
                results[dep] = {"status": "OK", "version": getattr(langchain_community, '__version__', 'unknown')}
            elif dep == "sentence-transformers":
                import sentence_transformers
                results[dep] = {"status": "OK", "version": sentence_transformers.__version__}
            
            print(f"✅ {dep}: {results[dep]['version']}")
            
        except ImportError:
            results[dep] = {"status": "NOT_INSTALLED", "message": "Package not found"}
            print(f"❌ {dep}: Not installed")
        except Exception as e:
            results[dep] = {"status": "ERROR", "message": str(e)}
            print(f"⚠️ {dep}: {str(e)}")
    
    return results

def generate_orchestration_fixes(results: Dict[str, Any]):
    """Generate fixes for orchestration issues"""
    print("\n" + "="*60)
    print("ORCHESTRATION REMEDIATION RECOMMENDATIONS")
    print("="*60)
    
    fixes = []
    
    # n8n fixes
    if results['n8n']['status'] == 'ACCESSIBLE':
        fixes.append({
            "service": "n8n",
            "issue": "Accessible but requires login credentials",
            "fix": "Verify login credentials for scoobyjava account",
            "priority": "HIGH"
        })
    elif results['n8n']['status'] == 'ERROR':
        fixes.append({
            "service": "n8n", 
            "issue": "n8n endpoints not accessible",
            "fix": "Check n8n cloud account status and endpoint URLs",
            "priority": "HIGH"
        })
    
    # LangGraph fixes
    if results['langgraph']['status'] == 'ERROR':
        fixes.append({
            "service": "LangGraph",
            "issue": "LangGraph installation or functionality issues",
            "fix": "Reinstall LangGraph and check dependencies",
            "priority": "MEDIUM"
        })
    
    # Agent system fixes
    if results['agents']['status'] != 'OK':
        fixes.append({
            "service": "Agent System",
            "issue": "Agent system not fully functional",
            "fix": "Check agent dependencies and fix import issues",
            "priority": "HIGH"
        })
    
    # Agno/Phidata
    if results['agno_phidata']['status'] == 'NOT_INSTALLED':
        fixes.append({
            "service": "Agno/Phidata",
            "issue": "Agent orchestration frameworks not installed",
            "fix": "Install if required for specific workflows",
            "priority": "LOW"
        })
    
    # Print fixes
    for fix in fixes:
        print(f"\n🔧 {fix['service']} ({fix['priority']} PRIORITY)")
        print(f"   Issue: {fix['issue']}")
        print(f"   Fix: {fix['fix']}")
    
    return fixes

def main():
    """Main test execution"""
    print("Sophia AI Orchestration Systems Testing")
    print("="*50)
    
    # Load environment
    env_vars = load_environment()
    print(f"Loaded {len(env_vars)} environment variables")
    
    # Run tests
    results = {
        'n8n': test_n8n_access(),
        'langgraph': test_langgraph_installation(),
        'agents': test_agent_system(),
        'agno_phidata': test_agno_phidata(),
        'dependencies': test_workflow_dependencies()
    }
    
    # Generate fixes
    fixes = generate_orchestration_fixes(results)
    
    # Save results
    with open('orchestration_test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'results': results,
            'fixes': fixes
        }, f, indent=2)
    
    print(f"\n📊 Results saved to orchestration_test_results.json")
    
    # Summary
    print(f"\n📋 SUMMARY")
    print(f"="*20)
    for service, result in results.items():
        if service == 'dependencies':
            continue  # Skip dependencies in summary
        status_emoji = "✅" if result['status'] == 'OK' else "⚠️" if result['status'] in ['ACCESSIBLE', 'PARTIAL', 'INSTALLED'] else "❌"
        print(f"{status_emoji} {service.upper()}: {result['status']}")

if __name__ == "__main__":
    main()

