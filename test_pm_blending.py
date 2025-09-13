#!/usr/bin/env python3
"""
Test Project Management Blending Capabilities
Demonstrates how Slack, Asana, and Linear insights are combined
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
sys.path.insert(0, '/Users/lynnmusil/sophia-intel-ai')

# Load environment
load_dotenv('.env')

async def test_project_overview():
    """Test the unified project overview endpoint"""
    from app.api.routers.projects import get_project_overview, get_sync_status
    
    print("=" * 70)
    print("PROJECT MANAGEMENT BLENDING TEST")
    print("=" * 70)
    
    # Check sync status first
    print("\n1. Checking Integration Status...")
    sync_status = await get_sync_status()
    print(json.dumps(sync_status, indent=2))
    
    # Get unified project overview
    print("\n2. Fetching Unified Project Overview...")
    overview = await get_project_overview()
    
    print("\n📊 UNIFIED PROJECT INSIGHTS:")
    print("-" * 50)
    
    # Display sources
    print("\nData Sources:")
    for source, status in overview['sources'].items():
        icon = "✅" if status['configured'] else "❌"
        print(f"  {icon} {source.upper()}: {status['details']}")
    
    # Display major projects
    if overview['major_projects']:
        print(f"\n🎯 Major Projects ({len(overview['major_projects'])} total):")
        for project in overview['major_projects'][:5]:
            risk_indicator = "🔴" if project.get('is_overdue') or project.get('risk') == 'high' else "🟢"
            print(f"  {risk_indicator} {project['name'][:50]}")
            print(f"     Source: {project['source']}, Status: {project.get('status', 'N/A')}")
            if project.get('is_overdue'):
                print(f"     ⚠️  OVERDUE")
    
    # Display communication issues
    if overview['communication_issues']:
        print(f"\n💬 Communication Issues ({len(overview['communication_issues'])} detected):")
        for issue in overview['communication_issues'][:3]:
            print(f"  - {issue.get('pattern', issue.get('issue'))}")
            if issue.get('channel'):
                print(f"    Channel: {issue['channel']}")
            if issue.get('impact'):
                print(f"    Impact: {issue['impact']}")
    
    # Display blockages
    if overview['blockages']:
        print(f"\n🚧 Blockages ({len(overview['blockages'])} found):")
        for blockage in overview['blockages'][:3]:
            print(f"  - {blockage}")
    
    # Display notes
    if overview['notes']:
        print(f"\n📝 System Notes:")
        for note in overview['notes']:
            print(f"  - {note}")
    
    return overview

async def test_individual_connectors():
    """Test individual connector capabilities"""
    from app.connectors.registry import ConnectorRegistry
    
    print("\n" + "=" * 70)
    print("INDIVIDUAL CONNECTOR TESTS")
    print("=" * 70)
    
    registry = ConnectorRegistry()
    
    # Test Slack connector
    if registry.configured("slack"):
        print("\n🔷 Testing Slack Connector...")
        try:
            slack = registry.get("slack")
            channels = await slack.fetch_recent()
            if channels:
                print(f"  ✅ Retrieved {len(channels)} Slack channels")
                # Show sample channel
                if channels:
                    ch = channels[0]
                    print(f"  Sample: #{ch.get('name')} ({ch.get('num_members', 0)} members)")
        except Exception as e:
            print(f"  ❌ Slack test failed: {e}")
    
    # Test Asana connector
    if registry.configured("asana"):
        print("\n🔶 Testing Asana Connector...")
        try:
            asana = registry.get("asana")
            projects = await asana.fetch_recent()
            if projects:
                print(f"  ✅ Retrieved {len(projects)} Asana projects")
                # Show sample project
                if projects:
                    p = projects[0]
                    print(f"  Sample: {p.get('name', 'Unknown')}")
        except Exception as e:
            print(f"  ❌ Asana test failed: {e}")
    
    # Test Linear connector
    if registry.configured("linear"):
        print("\n🔵 Testing Linear Connector...")
        try:
            linear = registry.get("linear")
            health = await linear.fetch_recent()
            if health:
                print(f"  ✅ Retrieved Linear project health data")
                if isinstance(health, list) and health:
                    print(f"  Found {len(health)} projects")
        except Exception as e:
            print(f"  ❌ Linear test failed: {e}")

async def test_business_intelligence():
    """Test business intelligence capabilities of individual integrations"""
    print("\n" + "=" * 70)
    print("BUSINESS INTELLIGENCE CAPABILITIES")
    print("=" * 70)
    
    # Test Asana BI
    if os.getenv('ASANA_PAT_TOKEN') or os.getenv('ASANA_API_TOKEN'):
        print("\n📊 Asana Business Intelligence:")
        try:
            from app.integrations.asana_client import AsanaClient
            client = AsanaClient()
            
            # Get workspaces first
            workspaces = await client.get_workspaces()
            if workspaces:
                workspace_gid = workspaces[0].get('gid')
                
                # Analyze project health
                health = await client.analyze_project_health(workspace_gid)
                print(f"  Total Projects: {health['total_projects']}")
                print(f"  Active Projects: {health['active_projects']}")
                print(f"  Overdue Projects: {health['overdue_projects']}")
                print(f"  Health Score: {health['health_score']:.2f}")
                
                if health['recommendations']:
                    print("  Recommendations:")
                    for rec in health['recommendations'][:3]:
                        print(f"    - {rec}")
        except Exception as e:
            print(f"  ❌ Asana BI failed: {e}")
    
    # Test Linear BI
    if os.getenv('LINEAR_API_KEY'):
        print("\n📈 Linear Business Intelligence:")
        try:
            from app.integrations.linear_client import LinearClient
            client = LinearClient()
            
            # Get teams first
            teams = await client.get_teams()
            if teams and teams.get('teams'):
                team = teams['teams']['nodes'][0]
                team_id = team['id']
                
                # Get development velocity
                velocity = await client.analyze_development_velocity(team_id=team_id, days=14)
                if velocity.get('success'):
                    metrics = velocity.get('metrics', {})
                    print(f"  Team: {team['name']}")
                    print(f"  Issues Completed: {metrics.get('issues_completed', 0)}")
                    print(f"  Avg Cycle Time: {metrics.get('average_cycle_time_hours', 0):.1f} hours")
                    print(f"  Velocity Trend: {metrics.get('velocity_trend', 'stable')}")
        except Exception as e:
            print(f"  ❌ Linear BI failed: {e}")

async def test_sophia_orchestrator():
    """Test Sophia orchestrator context aggregation"""
    print("\n" + "=" * 70)
    print("SOPHIA ORCHESTRATOR CONTEXT AGGREGATION")
    print("=" * 70)
    
    try:
        from app.orchestrators.sophia.orchestrator import SophiaOrchestrator
        
        orchestrator = SophiaOrchestrator()
        
        # Test context aggregation
        test_context = {
            "page": "projects",
            "entityId": "test-project-123",
            "user": "test-user"
        }
        
        result = await orchestrator.aggregate(
            session_id="test-session",
            page_context=test_context,
            message="Show me project health and team velocity"
        )
        
        print("\n🤖 Sophia Context Layers:")
        trace = result.get('trace', {})
        layers = trace.get('layers', {})
        
        # RAG Layer
        if 'rag' in layers:
            rag = layers['rag']
            print(f"\n  📚 RAG Layer (Weaviate):")
            print(f"     Documents found: {rag.get('hits', 0)}")
            if rag.get('samples'):
                print(f"     Sample sources: {[s.get('source') for s in rag['samples'][:3]]}")
        
        # Facts Layer
        if 'facts' in layers:
            facts = layers['facts']
            print(f"\n  💾 Facts Layer (PostgreSQL):")
            print(f"     Connected: {facts.get('ok', False)}")
            if facts.get('tables'):
                print(f"     Tables: {facts['tables'][:5]}")
        
        # Graph Layer
        if 'graph' in layers:
            graph = layers['graph']
            print(f"\n  🔗 Graph Layer (Neo4j):")
            print(f"     Connected: {graph.get('ok', False)}")
            print(f"     Total nodes: {graph.get('nodes', 0)}")
        
        print(f"\n  Session ID: {trace.get('session_id')}")
        
    except Exception as e:
        print(f"  ❌ Sophia orchestrator test failed: {e}")

async def main():
    """Run all PM blending tests"""
    print("\n🚀 Starting Project Management Blending Tests\n")
    
    # Test unified overview
    await test_project_overview()
    
    # Test individual connectors
    await test_individual_connectors()
    
    # Test BI capabilities
    await test_business_intelligence()
    
    # Test Sophia orchestrator
    await test_sophia_orchestrator()
    
    print("\n" + "=" * 70)
    print("✅ PROJECT MANAGEMENT BLENDING TESTS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())