#!/usr/bin/env python3
"""
Sophia Slack Integration Comprehensive Test Suite
==================================================

This script tests Sophia's integration with Slack using the provided credentials:
- SLACK_APP_TOKEN: xapp-1-A08BXNNKH2P-8419174294449-0017379454ab9f022e02af300c29819d9d665e961a0d223aa782c2c9e0cd875f
- Client ID: 293968207940.8405770663091
- Client Secret: 778e2fb5b026f97587210602acfe1e0b
- Bot Token: xoxe.xoxb-1-MS0yLTI5Mzk2ODIwNzk0MC04Mzk5OTUyNDE5MjA2LTg0MjkzOTEwOTc3MjgtODQxOTI2NzQzNjExMy01NmExNGJlMjNmNmNlZGQ2ODkzYTk4MzZlNTM5OWNhY2Q4NThiZmIwZmJmZThlMzc0YTgyNzg5NDRhMGQ1N2I1

Tests:
1. Slack API connectivity and authentication
2. Sophia server integration with Slack
3. Message sending capabilities
4. Workflow integration tests
5. Error handling and recovery
"""

import asyncio
import json
import time
import aiohttp
from datetime import datetime
from typing import Dict, Any, List
import os
import sys

# Slack credentials from user
SLACK_CREDENTIALS = {
    "app_token": "xapp-1-A08BXNNKH2P-8419174294449-0017379454ab9f022e02af300c29819d9d665e961a0d223aa782c2c9e0cd875f",
    "client_id": "293968207940.8405770663091",
    "client_secret": "778e2fb5b026f97587210602acfe1e0b",
    "signing_secret": "535eff2a503b06c333ec880f0e61d3c0",
    "socket_token": "xapp-1-A08BXNNKH2P-8419174294449-0017379454ab9f022e02af300c29819d9d665e961a0d223aa782c2c9e0cd875f",
    "bot_token": "xoxe.xoxb-1-MS0yLTI5Mzk2ODIwNzk0MC04Mzk5OTUyNDE5MjA2LTg0MjkzOTEwOTc3MjgtODQxOTI2NzQzNjExMy01NmExNGJlMjNmNmNlZGQ2ODkzYTk4MzZlNTM5OWNhY2Q4NThiZmIwZmJmZThlMzc0YTgyNzg5NDRhMGQ1N2I1",
    "refresh_token": "xoxe-1-MS0yLTI5Mzk2ODIwNzk0MC04MzkwNDI5MzM3NjE3LTg0MTkyNjc0MzYxMTMtODRkNzA4ZjNiODViODA1ZGU4YzFiMTZhOTFmODA5NGI1MDhkNmJmNjdmYWFmZTBiNGMwYTE5NWE1N2I4NmQ5OA",
    "workspace": "Pay Ready"
}

# Sophia server URLs
SOPHIA_URLS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "http://localhost:3333",  # MCP unified server
    "http://127.0.0.1:3333"
]

class SlackIntegrationTester:
    """Comprehensive Slack integration tester for Sophia"""
    
    def __init__(self):
        self.results = []
        self.sophia_base_url = None
        self.start_time = time.time()
        
    async def log_result(self, test_name: str, status: str, details: Dict[str, Any] = None, error: str = None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,  # "passed", "failed", "skipped", "warning"
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": (time.time() - self.start_time) * 1000,
            "details": details or {},
            "error": error
        }
        self.results.append(result)
        
        status_emoji = {
            "passed": "✅",
            "failed": "❌", 
            "skipped": "⏭️",
            "warning": "⚠️"
        }
        
        print(f"{status_emoji.get(status, '❓')} {test_name}: {status.upper()}")
        if error:
            print(f"   Error: {error}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()
    
    async def find_active_sophia_server(self) -> str:
        """Find which Sophia server URL is active"""
        print("🔍 Finding active Sophia server...")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for url in SOPHIA_URLS:
                try:
                    async with session.get(f"{url}/health") as response:
                        if response.status == 200:
                            data = await response.json()
                            if "sophia" in str(data).lower():
                                self.sophia_base_url = url
                                await self.log_result(
                                    "find_sophia_server",
                                    "passed",
                                    {"active_url": url, "health_check": data}
                                )
                                print(f"✅ Found active Sophia server at: {url}")
                                return url
                except Exception as e:
                    continue
            
            # Try without /health endpoint
            for url in SOPHIA_URLS:
                try:
                    async with session.get(f"{url}/docs") as response:
                        if response.status == 200:
                            self.sophia_base_url = url
                            await self.log_result(
                                "find_sophia_server",
                                "passed",
                                {"active_url": url, "endpoint": "/docs"}
                            )
                            print(f"✅ Found active Sophia server at: {url} (via /docs)")
                            return url
                except Exception as e:
                    continue
        
        await self.log_result(
            "find_sophia_server",
            "failed",
            error="No active Sophia server found"
        )
        return None
    
    async def test_slack_api_connectivity(self):
        """Test basic Slack API connectivity"""
        print("🔗 Testing Slack API connectivity...")
        
        headers = {
            "Authorization": f"Bearer {SLACK_CREDENTIALS['bot_token']}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            # Test auth
            try:
                async with session.post(
                    "https://slack.com/api/auth.test",
                    headers=headers
                ) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        await self.log_result(
                            "slack_api_auth",
                            "passed",
                            {
                                "user_id": data.get("user_id"),
                                "team": data.get("team"),
                                "team_id": data.get("team_id"),
                                "url": data.get("url")
                            }
                        )
                    else:
                        await self.log_result(
                            "slack_api_auth",
                            "failed",
                            error=f"Slack auth failed: {data.get('error', 'Unknown error')}"
                        )
                        return False
                        
            except Exception as e:
                await self.log_result(
                    "slack_api_auth",
                    "failed",
                    error=f"Exception during Slack auth: {str(e)}"
                )
                return False
            
            # Test team info
            try:
                async with session.post(
                    "https://slack.com/api/team.info",
                    headers=headers
                ) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        team_info = data.get("team", {})
                        await self.log_result(
                            "slack_team_info",
                            "passed",
                            {
                                "team_name": team_info.get("name"),
                                "domain": team_info.get("domain"),
                                "email_domain": team_info.get("email_domain")
                            }
                        )
                    else:
                        await self.log_result(
                            "slack_team_info",
                            "warning",
                            error=f"Team info failed: {data.get('error', 'Unknown error')}"
                        )
                        
            except Exception as e:
                await self.log_result(
                    "slack_team_info",
                    "warning",
                    error=f"Exception getting team info: {str(e)}"
                )
        
        return True
    
    async def test_sophia_integration_endpoints(self):
        """Test Sophia's integration endpoints"""
        print("🤖 Testing Sophia integration endpoints...")
        
        if not self.sophia_base_url:
            await self.log_result(
                "sophia_endpoints",
                "skipped",
                error="No active Sophia server found"
            )
            return
        
        test_endpoints = [
            "/api/integrations/status",
            "/business/slack/test",
            "/api/business/dashboard", 
            "/api/factory/personas",
            "/health"
        ]
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for endpoint in test_endpoints:
                try:
                    async with session.get(f"{self.sophia_base_url}{endpoint}") as response:
                        status = "passed" if response.status < 400 else "failed" 
                        
                        try:
                            data = await response.json()
                        except:
                            data = {"raw_response": await response.text()}
                        
                        await self.log_result(
                            f"sophia_endpoint_{endpoint.replace('/', '_')}",
                            status,
                            {
                                "status_code": response.status,
                                "response_size": len(str(data)),
                                "has_data": bool(data)
                            },
                            error=None if status == "passed" else f"HTTP {response.status}"
                        )
                        
                except Exception as e:
                    await self.log_result(
                        f"sophia_endpoint_{endpoint.replace('/', '_')}",
                        "failed",
                        error=f"Exception: {str(e)}"
                    )
    
    async def test_slack_message_functionality(self):
        """Test Slack message sending capabilities"""
        print("💬 Testing Slack message functionality...")
        
        if not self.sophia_base_url:
            await self.log_result(
                "slack_messaging",
                "skipped",
                error="No active Sophia server found"
            )
            return
        
        # Test if there's a Slack message endpoint
        test_endpoints = [
            "/api/integrations/slack/send",
            "/business/slack/message",
            "/api/business/slack/notify"
        ]
        
        test_message = {
            "text": f"🤖 Sophia Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "channel": "#general"  # Fallback channel
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint in test_endpoints:
                try:
                    async with session.post(
                        f"{self.sophia_base_url}{endpoint}",
                        json=test_message,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        
                        try:
                            data = await response.json()
                        except:
                            data = {"raw_response": await response.text()}
                        
                        status = "passed" if response.status < 400 else "warning"
                        await self.log_result(
                            f"slack_message_{endpoint.split('/')[-1]}",
                            status,
                            {
                                "endpoint": endpoint,
                                "status_code": response.status,
                                "response": data
                            },
                            error=None if status == "passed" else f"HTTP {response.status}"
                        )
                        
                        if status == "passed":
                            print(f"   ✅ Successfully sent test message via {endpoint}")
                            return True
                            
                except Exception as e:
                    await self.log_result(
                        f"slack_message_{endpoint.split('/')[-1]}",
                        "failed",
                        error=f"Exception: {str(e)}"
                    )
        
        # If no endpoints work, try direct Slack API call
        await self.test_direct_slack_message()
    
    async def test_direct_slack_message(self):
        """Test direct Slack API message sending"""
        print("📤 Testing direct Slack API message sending...")
        
        headers = {
            "Authorization": f"Bearer {SLACK_CREDENTIALS['bot_token']}",
            "Content-Type": "application/json"
        }
        
        # First, get list of channels to find a valid one
        async with aiohttp.ClientSession() as session:
            try:
                # Get channels list
                async with session.post(
                    "https://slack.com/api/conversations.list",
                    headers=headers,
                    json={"types": "public_channel,private_channel"}
                ) as response:
                    channels_data = await response.json()
                    
                    if channels_data.get("ok") and channels_data.get("channels"):
                        # Find a suitable channel (prefer #general or #random)
                        target_channel = None
                        for channel in channels_data["channels"]:
                            if channel["name"] in ["general", "random", "test"]:
                                target_channel = channel["id"]
                                break
                        
                        if not target_channel:
                            target_channel = channels_data["channels"][0]["id"]  # Use first available
                        
                        await self.log_result(
                            "slack_channels_list",
                            "passed",
                            {
                                "total_channels": len(channels_data["channels"]),
                                "target_channel": target_channel
                            }
                        )
                        
                        # Try to send a message
                        message = {
                            "channel": target_channel,
                            "text": f"🤖 Sophia Integration Test Message\n⏰ Timestamp: {datetime.now().isoformat()}\n🔬 Testing Slack connectivity from Sophia AI system"
                        }
                        
                        async with session.post(
                            "https://slack.com/api/chat.postMessage",
                            headers=headers,
                            json=message
                        ) as msg_response:
                            msg_data = await msg_response.json()
                            
                            if msg_data.get("ok"):
                                await self.log_result(
                                    "slack_direct_message",
                                    "passed",
                                    {
                                        "message_ts": msg_data.get("ts"),
                                        "channel": msg_data.get("channel"),
                                        "message_text": message["text"][:100] + "..."
                                    }
                                )
                                print("   ✅ Successfully sent message directly to Slack!")
                                return True
                            else:
                                await self.log_result(
                                    "slack_direct_message",
                                    "failed",
                                    error=f"Message sending failed: {msg_data.get('error', 'Unknown error')}"
                                )
                    else:
                        await self.log_result(
                            "slack_channels_list",
                            "failed",
                            error=f"Failed to get channels: {channels_data.get('error', 'Unknown error')}"
                        )
                        
            except Exception as e:
                await self.log_result(
                    "slack_direct_api",
                    "failed",
                    error=f"Exception: {str(e)}"
                )
        
        return False
    
    async def test_sophia_slack_workflows(self):
        """Test Sophia's Slack workflow integration"""
        print("🔄 Testing Sophia-Slack workflow integration...")
        
        if not self.sophia_base_url:
            await self.log_result(
                "workflow_integration",
                "skipped",
                error="No active Sophia server found"
            )
            return
        
        # Test workflow endpoints that might integrate with Slack
        workflow_tests = [
            {
                "endpoint": "/api/business/workflows/trigger",
                "method": "POST",
                "payload": {"type": "slack_notification", "message": "Test workflow"}
            },
            {
                "endpoint": "/api/business/notifications/send",
                "method": "POST", 
                "payload": {"platform": "slack", "message": "Test notification"}
            },
            {
                "endpoint": "/api/factory/deploy",
                "method": "POST",
                "payload": {"persona": "sophia", "task": "slack integration test"}
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in workflow_tests:
                try:
                    if test["method"] == "POST":
                        async with session.post(
                            f"{self.sophia_base_url}{test['endpoint']}",
                            json=test["payload"],
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            
                            try:
                                data = await response.json()
                            except:
                                data = {"raw_response": await response.text()}
                            
                            status = "passed" if response.status < 400 else "warning"
                            await self.log_result(
                                f"workflow_{test['endpoint'].split('/')[-1]}",
                                status,
                                {
                                    "endpoint": test["endpoint"],
                                    "status_code": response.status,
                                    "payload": test["payload"],
                                    "response": data
                                },
                                error=None if status == "passed" else f"HTTP {response.status}"
                            )
                            
                except Exception as e:
                    await self.log_result(
                        f"workflow_{test['endpoint'].split('/')[-1]}",
                        "failed",
                        error=f"Exception: {str(e)}"
                    )
    
    async def test_error_handling(self):
        """Test error handling and recovery"""
        print("🛡️ Testing error handling...")
        
        # Test invalid Slack token
        invalid_headers = {
            "Authorization": "Bearer xoxb-invalid-token",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://slack.com/api/auth.test",
                    headers=invalid_headers
                ) as response:
                    data = await response.json()
                    
                    if not data.get("ok") and data.get("error") == "invalid_auth":
                        await self.log_result(
                            "error_handling_invalid_token",
                            "passed",
                            {"expected_error": "invalid_auth", "received_error": data.get("error")}
                        )
                    else:
                        await self.log_result(
                            "error_handling_invalid_token",
                            "warning",
                            {"unexpected_response": data}
                        )
                        
            except Exception as e:
                await self.log_result(
                    "error_handling_exception",
                    "failed",
                    error=f"Exception during error handling test: {str(e)}"
                )
    
    async def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "passed"])
        failed = len([r for r in self.results if r["status"] == "failed"])
        warnings = len([r for r in self.results if r["status"] == "warning"])
        skipped = len([r for r in self.results if r["status"] == "skipped"])
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        total_time = (time.time() - self.start_time) * 1000
        
        report = {
            "test_run_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time_ms": total_time,
                "sophia_server_url": self.sophia_base_url,
                "slack_workspace": SLACK_CREDENTIALS["workspace"]
            },
            "results_summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "success_rate_percent": round(success_rate, 2)
            },
            "integration_status": {
                "slack_api_connectivity": "passed" if any(r["test_name"] == "slack_api_auth" and r["status"] == "passed" for r in self.results) else "failed",
                "sophia_server_found": "passed" if self.sophia_base_url else "failed", 
                "direct_messaging": "passed" if any("slack_direct_message" in r["test_name"] and r["status"] == "passed" for r in self.results) else "failed",
                "workflow_integration": "partial" if any("workflow" in r["test_name"] and r["status"] in ["passed", "warning"] for r in self.results) else "not_tested"
            },
            "recommendations": [],
            "detailed_results": self.results
        }
        
        # Generate recommendations
        if not self.sophia_base_url:
            report["recommendations"].append({
                "priority": "high",
                "issue": "No active Sophia server found",
                "suggestion": "Start Sophia server on port 9000 or 3333 and ensure it's accessible"
            })
        
        if failed > 0:
            report["recommendations"].append({
                "priority": "medium",
                "issue": f"{failed} tests failed",
                "suggestion": "Review failed tests and implement missing Slack integration endpoints"
            })
        
        if not any("slack_direct_message" in r["test_name"] and r["status"] == "passed" for r in self.results):
            report["recommendations"].append({
                "priority": "high", 
                "issue": "Slack messaging not working",
                "suggestion": "Implement Slack SDK integration with proper bot token authentication"
            })
        
        # Save report
        report_file = f"sophia_slack_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        return report, report_file
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("=" * 80)
        print("🚀 SOPHIA SLACK INTEGRATION COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏢 Slack workspace: {SLACK_CREDENTIALS['workspace']}")
        print()
        
        # Run all tests
        await self.find_active_sophia_server()
        await self.test_slack_api_connectivity()
        await self.test_sophia_integration_endpoints()
        await self.test_slack_message_functionality()
        await self.test_sophia_slack_workflows()
        await self.test_error_handling()
        
        # Generate final report
        report, report_file = await self.generate_comprehensive_report()
        
        print("=" * 80)
        print("📊 TEST SUITE COMPLETE - FINAL REPORT")
        print("=" * 80)
        print(f"⏰ Total execution time: {report['test_run_summary']['total_execution_time_ms']:.0f}ms")
        print(f"📈 Success rate: {report['results_summary']['success_rate_percent']:.1f}%")
        print(f"✅ Passed: {report['results_summary']['passed']}")
        print(f"❌ Failed: {report['results_summary']['failed']}")
        print(f"⚠️ Warnings: {report['results_summary']['warnings']}")
        print(f"⏭️ Skipped: {report['results_summary']['skipped']}")
        print()
        
        print("🔍 Integration Status:")
        for key, value in report["integration_status"].items():
            status_emoji = {"passed": "✅", "failed": "❌", "partial": "🟡", "not_tested": "⏭️"}
            print(f"   {status_emoji.get(value, '❓')} {key.replace('_', ' ').title()}: {value}")
        print()
        
        if report["recommendations"]:
            print("💡 Recommendations:")
            for rec in report["recommendations"]:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                print(f"   {priority_emoji.get(rec['priority'], '📝')} {rec['issue']}")
                print(f"      → {rec['suggestion']}")
            print()
        
        print(f"📝 Detailed report saved to: {report_file}")
        print()
        
        return report


async def main():
    """Main test execution function"""
    tester = SlackIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())