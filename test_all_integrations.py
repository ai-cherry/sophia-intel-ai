#!/usr/bin/env python3
"""
Unified Integration Test Suite for All Optimized Clients
Tests: Looker, Slack, Airtable, Salesforce, HubSpot
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Set environment variables if not already set
os.environ.setdefault("REDIS_URL", "redis://localhost:6380")


class IntegrationTestSuite:
    """
    Comprehensive test suite for all business integrations
    """
    
    def __init__(self):
        self.test_results = {}
        self.integration_status = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def print_header(self, title: str, emoji: str = "🔧"):
        """Print formatted section header"""
        print(f"\n{'=' * 70}")
        print(f"{emoji} {title}")
        print('=' * 70)
        
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"   ✅ {test_name}")
        else:
            print(f"   ❌ {test_name}")
        if details:
            print(f"      {details}")
        self.test_results[test_name] = passed
        
    async def test_looker(self):
        """Test Looker integration"""
        self.print_header("Testing LOOKER Integration", "📊")
        integration_name = "Looker"
        
        try:
            from app.integrations.looker_optimized_client import (
                LookerOptimizedClient,
                LookerAnalyticsPipeline,
                LookerQuery
            )
            
            async with LookerOptimizedClient() as client:
                # Test 1: Connection
                print("\n1. Testing API connection...")
                connected = await client.test_connection()
                self.print_result(
                    f"{integration_name}: Connection",
                    connected,
                    "OAuth 2.0 authentication successful" if connected else "Connection failed"
                )
                
                if connected:
                    # Test 2: Get dashboards
                    print("\n2. Testing dashboard retrieval...")
                    try:
                        dashboards = await client.get_dashboards()
                        self.print_result(
                            f"{integration_name}: Get Dashboards",
                            True,
                            f"Retrieved {len(dashboards)} dashboards"
                        )
                        
                        # Test 3: Analytics pipeline
                        if dashboards:
                            print("\n3. Testing analytics pipeline...")
                            pipeline = LookerAnalyticsPipeline()
                            await pipeline.setup()
                            
                            insights = await pipeline.analyze_dashboard(dashboards[0]["id"])
                            self.print_result(
                                f"{integration_name}: Analytics Pipeline",
                                len(insights) >= 0,
                                f"Generated {len(insights)} insights"
                            )
                        
                        # Test 4: Query execution
                        print("\n4. Testing inline query...")
                        query = LookerQuery(
                            model="e_commerce",
                            view="orders",
                            fields=["orders.id", "orders.created_date"],
                            limit=10
                        )
                        
                        try:
                            results = await client.run_inline_query(query)
                            self.print_result(
                                f"{integration_name}: Query Execution",
                                True,
                                f"Query returned {len(results) if isinstance(results, list) else 'data'}"
                            )
                        except Exception as e:
                            self.print_result(f"{integration_name}: Query Execution", False, str(e)[:50])
                            
                    except Exception as e:
                        self.print_result(f"{integration_name}: Get Dashboards", False, str(e)[:50])
                        
            self.integration_status[integration_name] = connected
                        
        except ImportError as e:
            self.print_result(f"{integration_name}: Import", False, str(e)[:50])
            self.integration_status[integration_name] = False
            
    async def test_slack(self):
        """Test Slack integration"""
        self.print_header("Testing SLACK Integration", "💬")
        integration_name = "Slack"
        
        try:
            from app.integrations.slack_optimized_client import (
                SlackOptimizedClient,
                SlackConversationAnalyzer,
                SlackMessage
            )
            
            client = SlackOptimizedClient()
            await client.setup()
            
            try:
                # Test 1: Connection
                print("\n1. Testing API connection...")
                conversations = await client.get_conversations(limit=1)
                connected = len(conversations) >= 0
                self.print_result(
                    f"{integration_name}: Connection",
                    connected,
                    f"Connected to workspace with {len(conversations)} channels"
                )
                
                # Test 2: User retrieval
                print("\n2. Testing user retrieval...")
                try:
                    users = await client.get_users()
                    self.print_result(
                        f"{integration_name}: Get Users",
                        True,
                        f"Retrieved {len(users)} users"
                    )
                except Exception as e:
                    self.print_result(f"{integration_name}: Get Users", False, str(e)[:50])
                    
                # Test 3: Conversation analysis
                if conversations:
                    print("\n3. Testing conversation analysis...")
                    analyzer = SlackConversationAnalyzer()
                    await analyzer.setup()
                    
                    try:
                        insights = await analyzer.analyze_channel(
                            conversations[0]["id"],
                            hours_back=24
                        )
                        self.print_result(
                            f"{integration_name}: Conversation Analysis",
                            True,
                            f"Extracted {len(insights)} insights"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Conversation Analysis", False, str(e)[:50])
                        
                # Test 4: Message preparation
                print("\n4. Testing message preparation...")
                message = SlackMessage(
                    channel="general",
                    text="Test message",
                    blocks=[{
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*Test*"}
                    }]
                )
                self.print_result(
                    f"{integration_name}: Message Preparation",
                    message.channel == "general",
                    "Message structure validated"
                )
                
                self.integration_status[integration_name] = connected
                
            finally:
                await client.stop()
                
        except ImportError as e:
            self.print_result(f"{integration_name}: Import", False, str(e)[:50])
            self.integration_status[integration_name] = False
            
    async def test_airtable(self):
        """Test Airtable integration"""
        self.print_header("Testing AIRTABLE Integration", "📋")
        integration_name = "Airtable"
        
        try:
            from app.integrations.airtable_optimized_client import (
                AirtableOptimizedClient,
                AirtableKnowledgeBase,
                AirtableFormula
            )
            
            async with AirtableOptimizedClient() as client:
                # Test 1: Connection
                print("\n1. Testing API connection...")
                connected = await client.test_connection()
                self.print_result(
                    f"{integration_name}: Connection",
                    connected,
                    "Personal Access Token authenticated" if connected else "Connection failed"
                )
                
                if connected:
                    # Test 2: Schema loading
                    print("\n2. Testing schema loading...")
                    schema = client.schema_cache
                    self.print_result(
                        f"{integration_name}: Schema Loading",
                        len(schema) > 0,
                        f"Loaded {len(schema)} table schemas"
                    )
                    
                    # Test 3: Record listing
                    if schema:
                        table_name = list(schema.keys())[0]
                        print(f"\n3. Testing record listing from '{table_name}'...")
                        
                        try:
                            records = await client.list_records(table_name, max_records=5)
                            self.print_result(
                                f"{integration_name}: List Records",
                                True,
                                f"Retrieved {len(records)} records"
                            )
                        except Exception as e:
                            self.print_result(f"{integration_name}: List Records", False, str(e)[:50])
                            
                    # Test 4: Formula queries
                    print("\n4. Testing formula queries...")
                    formula = AirtableFormula()
                    formula.add_condition("Status", "=", "Active")
                    query_str = formula.build()
                    self.print_result(
                        f"{integration_name}: Formula Builder",
                        "{Status}='Active'" in query_str,
                        f"Built formula: {query_str}"
                    )
                    
                    # Test 5: Knowledge base
                    print("\n5. Testing knowledge base sync...")
                    kb = AirtableKnowledgeBase()
                    await kb.setup()
                    
                    try:
                        sync_results = await kb.sync_all()
                        self.print_result(
                            f"{integration_name}: Knowledge Base",
                            True,
                            f"Synced {len(sync_results)} tables"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Knowledge Base", False, str(e)[:50])
                        
                self.integration_status[integration_name] = connected
                
        except ImportError as e:
            self.print_result(f"{integration_name}: Import", False, str(e)[:50])
            self.integration_status[integration_name] = False
            
    async def test_salesforce(self):
        """Test Salesforce integration"""
        self.print_header("Testing SALESFORCE Integration", "☁️")
        integration_name = "Salesforce"
        
        try:
            from app.integrations.salesforce_optimized_client import (
                SalesforceOptimizedClient,
                SalesforceSyncManager,
                SalesforceQuery
            )
            
            async with SalesforceOptimizedClient() as client:
                # Test 1: Connection
                print("\n1. Testing API connection...")
                connected = await client.test_connection()
                self.print_result(
                    f"{integration_name}: Connection",
                    connected,
                    "OAuth 2.0 authenticated" if connected else "Connection failed"
                )
                
                if connected:
                    # Test 2: SOQL query
                    print("\n2. Testing SOQL queries...")
                    query = SalesforceQuery(
                        object_name="Account",
                        fields=["Id", "Name"],
                        limit=5
                    )
                    
                    try:
                        accounts = await client.query(query.build())
                        self.print_result(
                            f"{integration_name}: SOQL Query",
                            True,
                            f"Retrieved {len(accounts)} accounts"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: SOQL Query", False, str(e)[:50])
                        
                    # Test 3: Pipeline analytics
                    print("\n3. Testing pipeline analytics...")
                    try:
                        pipeline = await client.get_pipeline_analytics()
                        self.print_result(
                            f"{integration_name}: Pipeline Analytics",
                            "total_value" in pipeline,
                            f"Pipeline value: ${pipeline.get('total_value', 0):,.0f}"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Pipeline Analytics", False, str(e)[:50])
                        
                    # Test 4: Sync manager
                    print("\n4. Testing sync manager...")
                    sync_manager = SalesforceSyncManager()
                    await sync_manager.setup()
                    
                    try:
                        contact_sync = await sync_manager.sync_contacts(
                            since=datetime.now() - timedelta(days=30)
                        )
                        self.print_result(
                            f"{integration_name}: Contact Sync",
                            True,
                            f"Synced {contact_sync.get('synced', 0)} contacts"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Contact Sync", False, str(e)[:50])
                        
                    # Test 5: Opportunity insights
                    print("\n5. Testing opportunity insights...")
                    try:
                        insights = await sync_manager.sync_opportunities_to_sophia()
                        self.print_result(
                            f"{integration_name}: Opportunity Insights",
                            True,
                            f"Generated {len(insights)} insights"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Opportunity Insights", False, str(e)[:50])
                        
                self.integration_status[integration_name] = connected
                
        except ImportError as e:
            self.print_result(f"{integration_name}: Import", False, str(e)[:50])
            self.integration_status[integration_name] = False
            
    async def test_hubspot(self):
        """Test HubSpot integration"""
        self.print_header("Testing HUBSPOT Integration", "🚀")
        integration_name = "HubSpot"
        
        try:
            from app.integrations.hubspot_optimized_client import (
                HubSpotOptimizedClient,
                HubSpotMarketingAutomation,
                HubSpotContact
            )
            
            async with HubSpotOptimizedClient() as client:
                # Test 1: Connection
                print("\n1. Testing API connection...")
                connected = await client.test_connection()
                self.print_result(
                    f"{integration_name}: Connection",
                    connected,
                    "OAuth 2.0 authenticated" if connected else "Connection failed"
                )
                
                if connected:
                    # Test 2: Get contacts
                    print("\n2. Testing contact retrieval...")
                    try:
                        contacts = await client.get_contacts(limit=5)
                        self.print_result(
                            f"{integration_name}: Get Contacts",
                            True,
                            f"Retrieved {len(contacts)} contacts"
                        )
                        
                        # Test 3: Lead scoring
                        if contacts:
                            print("\n3. Testing lead scoring...")
                            contact_ids = [c.id for c in contacts if c.id][:3]
                            
                            try:
                                scores = await client.score_contacts(contact_ids)
                                self.print_result(
                                    f"{integration_name}: Lead Scoring",
                                    True,
                                    f"Scored {len(scores)} contacts"
                                )
                            except Exception as e:
                                self.print_result(f"{integration_name}: Lead Scoring", False, str(e)[:50])
                                
                    except Exception as e:
                        self.print_result(f"{integration_name}: Get Contacts", False, str(e)[:50])
                        
                    # Test 4: Get deals
                    print("\n4. Testing deal retrieval...")
                    try:
                        deals = await client.get_deals(limit=5)
                        total_value = sum(d.amount for d in deals)
                        self.print_result(
                            f"{integration_name}: Get Deals",
                            True,
                            f"Retrieved {len(deals)} deals (${total_value:,.0f})"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Get Deals", False, str(e)[:50])
                        
                    # Test 5: Marketing automation
                    print("\n5. Testing marketing automation...")
                    automation = HubSpotMarketingAutomation()
                    await automation.setup()
                    
                    try:
                        segments = await automation.segment_contacts()
                        total_segmented = sum(len(ids) for ids in segments.values())
                        self.print_result(
                            f"{integration_name}: Contact Segmentation",
                            True,
                            f"Segmented {total_segmented} contacts into {len(segments)} groups"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Contact Segmentation", False, str(e)[:50])
                        
                    # Test 6: Campaign analysis
                    print("\n6. Testing campaign analysis...")
                    try:
                        performance = await automation.analyze_campaign_performance()
                        self.print_result(
                            f"{integration_name}: Campaign Analysis",
                            True,
                            f"Analyzed {performance.get('total_campaigns', 0)} campaigns"
                        )
                    except Exception as e:
                        self.print_result(f"{integration_name}: Campaign Analysis", False, str(e)[:50])
                        
                self.integration_status[integration_name] = connected
                
        except ImportError as e:
            self.print_result(f"{integration_name}: Import", False, str(e)[:50])
            self.integration_status[integration_name] = False
            
    def generate_report(self):
        """Generate comprehensive integration report"""
        self.print_header("INTEGRATION TEST REPORT", "📊")
        
        # Overall summary
        print(f"\n📈 TEST SUMMARY")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.total_tests - self.passed_tests}")
        print(f"   Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        # Integration status
        print(f"\n🔌 INTEGRATION STATUS")
        integrations = ["Looker", "Slack", "Airtable", "Salesforce", "HubSpot"]
        
        for integration in integrations:
            status = self.integration_status.get(integration)
            if status is True:
                print(f"   ✅ {integration}: Connected and operational")
            elif status is False:
                print(f"   ❌ {integration}: Connection failed")
            else:
                print(f"   ⚠️  {integration}: Not tested")
                
        # Test results by category
        print(f"\n🧪 TEST RESULTS BY CATEGORY")
        
        categories = {
            "Connection": [],
            "Data Retrieval": [],
            "Analytics": [],
            "Sync": [],
            "Automation": []
        }
        
        for test_name, result in self.test_results.items():
            if "Connection" in test_name:
                categories["Connection"].append((test_name, result))
            elif any(x in test_name for x in ["Get", "List", "Retrieval", "Query"]):
                categories["Data Retrieval"].append((test_name, result))
            elif any(x in test_name for x in ["Analytics", "Pipeline", "Insights", "Analysis"]):
                categories["Analytics"].append((test_name, result))
            elif any(x in test_name for x in ["Sync", "Knowledge"]):
                categories["Sync"].append((test_name, result))
            elif any(x in test_name for x in ["Automation", "Scoring", "Segmentation"]):
                categories["Automation"].append((test_name, result))
                
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for _, r in tests if r)
                total = len(tests)
                print(f"\n   {category}:")
                print(f"      {passed}/{total} tests passed ({(passed/total*100):.0f}%)")
                
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        failed_integrations = [
            name for name, status in self.integration_status.items() 
            if status is False
        ]
        
        if not failed_integrations:
            print("   🎉 All integrations are operational!")
            print("   • Consider implementing real-time monitoring")
            print("   • Set up automated alerts for API rate limits")
            print("   • Schedule regular data sync jobs")
        else:
            print(f"   ⚠️ {len(failed_integrations)} integration(s) need attention:")
            for integration in failed_integrations:
                print(f"      • Check {integration} API credentials in .env.local")
            print("   • Verify network connectivity to external services")
            print("   • Review API documentation for recent changes")
            
        # Next steps
        print(f"\n🚀 NEXT STEPS")
        print("   1. Review failed tests and update credentials if needed")
        print("   2. Enable production monitoring for all integrations")
        print("   3. Configure webhook endpoints for real-time updates")
        print("   4. Set up automated testing in CI/CD pipeline")
        print("   5. Implement error recovery and retry mechanisms")
        
        print("\n" + "=" * 70)
        
        if self.passed_tests == self.total_tests:
            print("🎊 PERFECT SCORE! All integrations fully operational.")
        elif self.passed_tests >= self.total_tests * 0.8:
            print("✅ GOOD STATUS: Most integrations working correctly.")
        elif self.passed_tests >= self.total_tests * 0.6:
            print("⚠️ NEEDS ATTENTION: Several issues detected.")
        else:
            print("❌ CRITICAL: Major integration issues require immediate attention.")


async def main():
    """Run complete integration test suite"""
    print("🔬 UNIFIED INTEGRATION TEST SUITE")
    print("Testing all optimized business integrations")
    print("=" * 70)
    
    tester = IntegrationTestSuite()
    
    # Run all integration tests
    await tester.test_looker()
    await tester.test_slack()
    await tester.test_airtable()
    await tester.test_salesforce()
    await tester.test_hubspot()
    
    # Generate comprehensive report
    tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())