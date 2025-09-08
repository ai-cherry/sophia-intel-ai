#!/usr/bin/env python3
"""
Sophia AI Custom MCP Server
Provides real-time operational context and intelligence for Genspark integration
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import mcp.server.stdio
from mcp import Server, types
from mcp.server.models import InitializationOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sophia-ai-mcp")


class SophiaAIMCPServer:
    """Custom MCP Server for Sophia AI Platform Intelligence"""

    def __init__(self):
        self.server = Server("sophia-ai-intelligence")
        self.lambda_labs_ip = "192.222.58.232"
        self.domains = [
            "api.sophia-intel.ai",
            "chat.sophia-intel.ai",
            "dashboard.sophia-intel.ai",
        ]

        # API configuration (masked for security)
        self.api_config = {
            "serper": {
                "key": os.getenv("SERPER_API_KEY"),
                "endpoint": "https://google.serper.dev/search",
            },
            "perplexity": {
                "key": os.getenv("PERPLEXITY_API_KEY"),
                "endpoint": "https://api.perplexity.ai/chat/completions",
            },
            "brave": {
                "key": os.getenv("BRAVE_API_KEY"),
                "endpoint": "https://api.search.brave.com/res/v1/web/search",
            },
            "exa": {
                "key": os.getenv("EXA_API_KEY"),
                "endpoint": "https://api.exa.ai/search",
            },
            "tavily": {
                "key": os.getenv("TAVILY_API_KEY"),
                "endpoint": "https://api.tavily.com/search",
            },
        }

        # Service endpoints
        self.service_endpoints = {
            "enhanced_search": f"http://{self.lambda_labs_ip}:8004",
            "enhanced_neural": f"http://{self.lambda_labs_ip}:8001",
            "original_neural": f"http://{self.lambda_labs_ip}:8000",
            "nginx": f"http://{self.lambda_labs_ip}:80",
        }

        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP server handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="sophia_health_check",
                    description="Get real-time health status of all Sophia AI services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "enum": [
                                    "all",
                                    "search",
                                    "neural",
                                    "gateway",
                                    "infrastructure",
                                ],
                                "description": "Specific service to check or 'all' for complete status",
                            },
                            "detailed": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include detailed metrics and response data",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="sophia_performance_metrics",
                    description="Get performance metrics and response times for Sophia AI services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeframe": {
                                "type": "string",
                                "enum": ["1h", "24h", "7d"],
                                "default": "1h",
                                "description": "Time period for metrics analysis",
                            },
                            "service": {
                                "type": "string",
                                "enum": ["all", "search", "neural", "api"],
                                "default": "all",
                                "description": "Specific service to analyze",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="sophia_api_usage",
                    description="Monitor API usage across all integrated external services",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api": {
                                "type": "string",
                                "enum": [
                                    "all",
                                    "serper",
                                    "perplexity",
                                    "brave",
                                    "exa",
                                    "tavily",
                                ],
                                "default": "all",
                                "description": "Specific API to monitor",
                            },
                            "include_costs": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include cost analysis in the report",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="sophia_search_test",
                    description="Test enhanced search functionality with real queries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to test with the enhanced search system",
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20,
                                "description": "Maximum number of results to return",
                            },
                            "apis": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["serper", "brave", "exa", "tavily"],
                                },
                                "description": "Specific APIs to use (default: all available)",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                types.Tool(
                    name="sophia_neural_inference",
                    description="Test neural inference capabilities with the DeepSeek model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Inference prompt for the neural model",
                            },
                            "model": {
                                "type": "string",
                                "default": "deepseek-r1-0528",
                                "description": "Neural model to use for inference",
                            },
                            "max_tokens": {
                                "type": "integer",
                                "default": 1000,
                                "minimum": 1,
                                "maximum": 4000,
                                "description": "Maximum tokens in response",
                            },
                        },
                        "required": ["prompt"],
                    },
                ),
                types.Tool(
                    name="sophia_deployment_status",
                    description="Get deployment and infrastructure status information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component": {
                                "type": "string",
                                "enum": [
                                    "dns",
                                    "lambda_labs",
                                    "services",
                                    "docker",
                                    "all",
                                ],
                                "default": "all",
                                "description": "Infrastructure component to check",
                            },
                            "include_history": {
                                "type": "boolean",
                                "default": False,
                                "description": "Include recent deployment history",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="sophia_troubleshoot",
                    description="Intelligent troubleshooting assistant for common issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue": {
                                "type": "string",
                                "description": "Description of the issue or error message",
                            },
                            "service": {
                                "type": "string",
                                "enum": [
                                    "search",
                                    "neural",
                                    "api",
                                    "infrastructure",
                                    "unknown",
                                ],
                                "default": "unknown",
                                "description": "Service where the issue is occurring",
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "default": "medium",
                                "description": "Severity level of the issue",
                            },
                        },
                        "required": ["issue"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "sophia_health_check":
                    return await self.check_service_health(
                        arguments.get("service", "all"),
                        arguments.get("detailed", False),
                    )
                elif name == "sophia_performance_metrics":
                    return await self.get_performance_metrics(
                        arguments.get("timeframe", "1h"),
                        arguments.get("service", "all"),
                    )
                elif name == "sophia_api_usage":
                    return await self.monitor_api_usage(
                        arguments.get("api", "all"),
                        arguments.get("include_costs", True),
                    )
                elif name == "sophia_search_test":
                    return await self.sophia_search_functionality(
                        arguments["query"],
                        arguments.get("max_results", 5),
                        arguments.get("apis", []),
                    )
                elif name == "sophia_neural_inference":
                    return await self.sophia_neural_inference(
                        arguments["prompt"],
                        arguments.get("model", "deepseek-r1-0528"),
                        arguments.get("max_tokens", 1000),
                    )
                elif name == "sophia_deployment_status":
                    return await self.check_deployment_status(
                        arguments.get("component", "all"),
                        arguments.get("include_history", False),
                    )
                elif name == "sophia_troubleshoot":
                    return await self.troubleshoot_issue(
                        arguments["issue"],
                        arguments.get("service", "unknown"),
                        arguments.get("severity", "medium"),
                    )
                else:
                    return [
                        types.TextContent(type="text", text=f"Unknown tool: {name}")
                    ]
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [
                    types.TextContent(
                        type="text", text=f"Error executing {name}: {str(e)}"
                    )
                ]

        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available resources"""
            return [
                types.Resource(
                    uri="sophia://architecture/overview",
                    name="Sophia AI Architecture Overview",
                    description="Complete system architecture and component relationships",
                    mimeType="application/json",
                ),
                types.Resource(
                    uri="sophia://services/status",
                    name="Real-time Service Status",
                    description="Current status of all Sophia AI services with health metrics",
                    mimeType="application/json",
                ),
                types.Resource(
                    uri="sophia://apis/integration",
                    name="API Integration Status",
                    description="Status and usage statistics for all integrated APIs",
                    mimeType="application/json",
                ),
                types.Resource(
                    uri="sophia://performance/metrics",
                    name="Performance Metrics Dashboard",
                    description="Real-time performance data, trends, and analytics",
                    mimeType="application/json",
                ),
                types.Resource(
                    uri="sophia://deployment/config",
                    name="Deployment Configuration",
                    description="Current deployment settings, infrastructure, and environment",
                    mimeType="application/json",
                ),
                types.Resource(
                    uri="sophia://troubleshooting/guide",
                    name="Troubleshooting Guide",
                    description="Common issues, solutions, and debugging procedures",
                    mimeType="text/markdown",
                ),
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "sophia://architecture/overview":
                return await self.get_architecture_overview()
            elif uri == "sophia://services/status":
                return await self.get_services_status()
            elif uri == "sophia://apis/integration":
                return await self.get_api_integration_status()
            elif uri == "sophia://performance/metrics":
                return await self.get_performance_dashboard()
            elif uri == "sophia://deployment/config":
                return await self.get_deployment_config()
            elif uri == "sophia://troubleshooting/guide":
                return await self.get_troubleshooting_guide()
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def check_service_health(
        self, service: str, detailed: bool
    ) -> List[types.TextContent]:
        """Check health of Sophia AI services"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "services": {},
        }

        services_to_check = (
            self.service_endpoints.keys() if service == "all" else [service]
        )
        healthy_count = 0
        total_count = 0

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            for service_name in services_to_check:
                if service_name in self.service_endpoints:
                    total_count += 1
                    endpoint = f"{self.service_endpoints[service_name]}/health"

                    try:
                        start_time = datetime.now()
                        async with session.get(endpoint) as resp:
                            response_time = (
                                datetime.now() - start_time
                            ).total_seconds() * 1000

                            if resp.status == 200:
                                data = await resp.json()
                                health_data["services"][service_name] = {
                                    "status": "healthy",
                                    "response_time_ms": round(response_time, 2),
                                    "http_status": resp.status,
                                    "data": (
                                        data
                                        if detailed
                                        else {"status": data.get("status", "ok")}
                                    ),
                                }
                                healthy_count += 1
                            else:
                                health_data["services"][service_name] = {
                                    "status": "unhealthy",
                                    "response_time_ms": round(response_time, 2),
                                    "http_status": resp.status,
                                    "error": f"HTTP {resp.status}",
                                }
                    except asyncio.TimeoutError:
                        health_data["services"][service_name] = {
                            "status": "timeout",
                            "error": "Request timeout (>10s)",
                        }
                    except Exception as e:
                        health_data["services"][service_name] = {
                            "status": "error",
                            "error": str(e),
                        }

        # Determine overall status
        if healthy_count == total_count:
            health_data["overall_status"] = "healthy"
        elif healthy_count > 0:
            health_data["overall_status"] = "degraded"
        else:
            health_data["overall_status"] = "unhealthy"

        health_data["summary"] = {
            "healthy_services": healthy_count,
            "total_services": total_count,
            "health_percentage": (
                round((healthy_count / total_count) * 100, 1) if total_count > 0 else 0
            ),
        }

        return [
            types.TextContent(
                type="text",
                text=f"Sophia AI Health Status ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n\n{json.dumps(health_data, indent=2)}",
            )
        ]

    async def sophia_search_functionality(
        self, query: str, max_results: int, apis: List[str]
    ) -> List[types.TextContent]:
        """Test enhanced search with real query"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                payload = {"query": query, "max_results": max_results}

                if apis:
                    payload["apis"] = apis

                start_time = datetime.now()
                async with session.post(
                    f"{self.service_endpoints['enhanced_search']}/search",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    if resp.status == 200:
                        result = await resp.json()

                        # Create summary
                        summary = {
                            "sophia_timestamp": datetime.now().isoformat(),
                            "query": result.get("query", query),
                            "status": "success",
                            "response_time_ms": round(response_time, 2),
                            "apis_used": result.get("apis_used", []),
                            "sources_found": len(result.get("sources", [])),
                            "confidence_score": result.get("confidence", 0),
                            "primary_response_preview": (
                                result.get("primary_response", "")[:200] + "..."
                                if result.get("primary_response")
                                else "No response"
                            ),
                            "source_breakdown": {},
                        }

                        # Analyze sources by API
                        for source in result.get("sources", []):
                            api = source.get("api", "unknown")
                            if api not in summary["source_breakdown"]:
                                summary["source_breakdown"][api] = 0
                            summary["source_breakdown"][api] += 1

                        return [
                            types.TextContent(
                                type="text",
                                text=f"Enhanced Search Test Results:\n\n{json.dumps(summary, indent=2)}",
                            )
                        ]
                    else:
                        error_text = await resp.text()
                        return [
                            types.TextContent(
                                type="text",
                                text=f"Search test failed with HTTP {resp.status}:\n{error_text}",
                            )
                        ]

        except Exception as e:
            return [types.TextContent(type="text", text=f"Search test error: {str(e)}")]

    async def get_performance_metrics(
        self, timeframe: str, service: str
    ) -> List[types.TextContent]:
        """Get performance metrics for services"""
        # This would typically connect to a monitoring system
        # For now, we'll simulate with current health checks

        metrics = {
            "timeframe": timeframe,
            "service": service,
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
        }

        # Perform quick performance tests
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            for service_name, endpoint in self.service_endpoints.items():
                if service == "all" or service in service_name:
                    try:
                        # Test response time
                        start_time = datetime.now()
                        async with session.get(f"{endpoint}/health") as resp:
                            response_time = (
                                datetime.now() - start_time
                            ).total_seconds() * 1000

                            metrics["metrics"][service_name] = {
                                "response_time_ms": round(response_time, 2),
                                "status_code": resp.status,
                                "availability": "up" if resp.status == 200 else "down",
                            }
                    except Exception as e:
                        metrics["metrics"][service_name] = {
                            "response_time_ms": None,
                            "status_code": None,
                            "availability": "error",
                            "error": str(e),
                        }

        return [
            types.TextContent(
                type="text",
                text=f"Performance Metrics ({timeframe}):\n\n{json.dumps(metrics, indent=2)}",
            )
        ]

    async def monitor_api_usage(
        self, api: str, include_costs: bool
    ) -> List[types.TextContent]:
        """Monitor external API usage"""
        # This would typically connect to usage tracking
        # For now, we'll provide configuration and status

        usage_data = {
            "timestamp": datetime.now().isoformat(),
            "api_filter": api,
            "apis": {},
        }

        for api_name, config in self.api_config.items():
            if api == "all" or api == api_name:
                usage_data["apis"][api_name] = {
                    "configured": config["key"] is not None,
                    "endpoint": config["endpoint"],
                    "status": "active" if config["key"] else "not_configured",
                }

                if include_costs:
                    # Estimated costs (would be real data in production)
                    usage_data["apis"][api_name]["estimated_monthly_cost"] = {
                        "serper": "$20-50",
                        "perplexity": "$30-80",
                        "brave": "$15-40",
                        "exa": "$25-60",
                        "tavily": "$20-45",
                    }.get(api_name, "Unknown")

        return [
            types.TextContent(
                type="text",
                text=f"API Usage Report:\n\n{json.dumps(usage_data, indent=2)}",
            )
        ]

    async def check_deployment_status(
        self, component: str, include_history: bool
    ) -> List[types.TextContent]:
        """Check deployment and infrastructure status"""
        deployment_status = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "status": {},
        }

        if component in ["all", "dns"]:
            deployment_status["status"]["dns"] = {
                "provider": "DNSimple",
                "domain": "sophia-intel.ai",
                "configured_subdomains": [
                    "api",
                    "chat",
                    "dashboard",
                    "agents",
                    "docs",
                    "status",
                ],
                "status": "active",
            }

        if component in ["all", "lambda_labs"]:
            deployment_status["status"]["lambda_labs"] = {
                "server_ip": self.lambda_labs_ip,
                "status": "operational",
                "services_running": len(self.service_endpoints),
            }

        if component in ["all", "services"]:
            # Get service status
            health_result = await self.check_service_health("all", False)
            deployment_status["status"]["services"] = "See health check results"

        return [
            types.TextContent(
                type="text",
                text=f"Deployment Status:\n\n{json.dumps(deployment_status, indent=2)}",
            )
        ]

    async def sophia_neural_inference(
        self, prompt: str, model: str, max_tokens: int
    ) -> List[types.TextContent]:
        """Test neural inference capabilities"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                payload = {"prompt": prompt, "model": model, "max_tokens": max_tokens}

                start_time = datetime.now()
                async with session.post(
                    f"{self.service_endpoints['enhanced_neural']}/api/v1/inference",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    if resp.status == 200:
                        result = await resp.json()

                        summary = {
                            "sophia_timestamp": datetime.now().isoformat(),
                            "prompt": (
                                prompt[:100] + "..." if len(prompt) > 100 else prompt
                            ),
                            "model": model,
                            "status": "success",
                            "response_time_ms": round(response_time, 2),
                            "tokens_generated": len(result.get("response", "").split()),
                            "response_preview": (
                                result.get("response", "")[:200] + "..."
                                if result.get("response")
                                else "No response"
                            ),
                        }

                        return [
                            types.TextContent(
                                type="text",
                                text=f"Neural Inference Test Results:\n\n{json.dumps(summary, indent=2)}",
                            )
                        ]
                    else:
                        error_text = await resp.text()
                        return [
                            types.TextContent(
                                type="text",
                                text=f"Neural inference test failed with HTTP {resp.status}:\n{error_text}",
                            )
                        ]

        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"Neural inference test error: {str(e)}"
                )
            ]

    async def troubleshoot_issue(
        self, issue: str, service: str, severity: str
    ) -> List[types.TextContent]:
        """Intelligent troubleshooting assistant"""
        troubleshooting_guide = {
            "timestamp": datetime.now().isoformat(),
            "issue": issue,
            "service": service,
            "severity": severity,
            "recommendations": [],
        }

        # Common troubleshooting patterns
        if "slow" in issue.lower() or "timeout" in issue.lower():
            troubleshooting_guide["recommendations"].extend(
                [
                    "Check service health status",
                    "Verify network connectivity to Lambda Labs",
                    "Review recent deployments for performance regressions",
                    "Check API rate limits and usage",
                ]
            )

        if "error" in issue.lower() or "500" in issue:
            troubleshooting_guide["recommendations"].extend(
                [
                    "Check service logs for error details",
                    "Verify all dependencies are running",
                    "Check API key configurations",
                    "Review recent code changes",
                ]
            )

        if "dns" in issue.lower() or "domain" in issue.lower():
            troubleshooting_guide["recommendations"].extend(
                [
                    "Check DNS propagation status",
                    "Verify DNSimple configuration",
                    "Test direct IP access to services",
                    "Check SSL certificate status",
                ]
            )

        # Add service-specific recommendations
        if service == "search":
            troubleshooting_guide["recommendations"].append(
                "Test individual API integrations"
            )
        elif service == "neural":
            troubleshooting_guide["recommendations"].append(
                "Check GPU memory usage on Lambda Labs"
            )

        return [
            types.TextContent(
                type="text",
                text=f"Troubleshooting Analysis:\n\n{json.dumps(troubleshooting_guide, indent=2)}",
            )
        ]

    # Resource methods
    async def get_architecture_overview(self) -> str:
        """Get architecture overview"""
        architecture = {
            "system_name": "Sophia AI V7 - Unified Domain Intelligence Platform",
            "architecture_type": "Neural-Native Microservices",
            "components": {
                "neural_engine": {
                    "model": "DeepSeek-R1-0528",
                    "purpose": "Advanced AI inference and reasoning",
                    "port": 8001,
                },
                "enhanced_search": {
                    "apis": ["Serper", "Perplexity", "Brave", "Exa", "Tavily"],
                    "purpose": "Multi-source intelligence aggregation",
                    "port": 8004,
                },
                "gateway_services": {
                    "load_balancer": "Nginx",
                    "purpose": "Traffic routing and SSL termination",
                    "port": 80,
                },
                "data_layer": {
                    "database": "PostgreSQL",
                    "cache": "Redis",
                    "vector_db": "Qdrant",
                },
            },
            "infrastructure": {
                "compute": "Lambda Labs GPU Server",
                "dns": "DNSimple",
                "domain": "sophia-intel.ai",
            },
        }

        return json.dumps(architecture, indent=2)

    async def get_services_status(self) -> str:
        """Get current services status"""
        health_result = await self.check_service_health("all", True)
        return health_result[0].text

    async def get_api_integration_status(self) -> str:
        """Get API integration status"""
        usage_result = await self.monitor_api_usage("all", True)
        return usage_result[0].text

    async def get_performance_dashboard(self) -> str:
        """Get performance dashboard data"""
        perf_result = await self.get_performance_metrics("1h", "all")
        return perf_result[0].text

    async def get_deployment_config(self) -> str:
        """Get deployment configuration"""
        deploy_result = await self.check_deployment_status("all", True)
        return deploy_result[0].text

    async def get_troubleshooting_guide(self) -> str:
        """Get troubleshooting guide"""
        guide = """# Sophia AI Troubleshooting Guide

## Common Issues and Solutions

### Service Health Issues
- **Symptom**: Service returning 500 errors
- **Solution**: Check service logs, verify dependencies, restart if needed

### Performance Issues  
- **Symptom**: Slow response times
- **Solution**: Check Lambda Labs resources, verify API rate limits

### DNS Issues
- **Symptom**: Domain not resolving
- **Solution**: Check DNSimple configuration, verify DNS propagation

### API Integration Issues
- **Symptom**: Search results incomplete
- **Solution**: Verify API keys, check rate limits, test individual APIs

## Emergency Contacts
- Infrastructure: Lambda Labs support
- DNS: DNSimple support  
- Development: GitHub repository issues

## Monitoring Dashboards
- Service Health: Use sophia_health_check tool
- Performance: Use sophia_performance_metrics tool
- API Usage: Use sophia_api_usage tool
"""
        return guide


async def main():
    """Main entry point"""
    server_instance = SophiaAIMCPServer()

    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sophia-ai-intelligence",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
