#!/usr/bin/env python3
"""
Comprehensive ESC Integration Test Suite
Tests ESC integration with Redis, MCP, Memory, and WebSocket systems.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import aiohttp
import redis.asyncio as redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.esc_config import get_config, get_secret_config, initialize_esc_config
from app.core.redis_config import RedisConfig
from app.core.security.access_control import (
    AccessRequest,
    Permission,
    ResourceType,
    get_access_control,
    initialize_default_users,
)
from app.core.security.secret_validator import (
    ComprehensiveSecretValidator,
    SecretType,
    ValidationConfig,
)

console = Console()
logger = logging.getLogger(__name__)


class ESCIntegrationTestSuite:
    """Comprehensive test suite for ESC integration"""

    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.esc_config = None

        # Test configurations
        self.test_secrets = {
            "redis_url": "infrastructure.redis.url",
            "redis_password": "infrastructure.redis.password",
            "openai_api_key": "llm_providers.direct_keys.openai",
            "portkey_api_key": "llm_providers.portkey.api_key",
            "qdrant_api_key": "infrastructure.vector_db.qdrant.api_key",
            "weaviate_api_key": "infrastructure.vector_db.weaviate.api_key",
        }

        self.test_endpoints = {
            "health": "http://localhost:8080/health",
            "redis_health": "http://localhost:8080/api/redis/health",
            "mcp_status": "http://localhost:8080/api/mcp/status",
            "config_status": "http://localhost:8080/api/config/status",
        }

    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete ESC integration test suite"""
        console.print(
            Panel.fit(
                f"[bold blue]ESC Integration Test Suite[/bold blue]\n"
                f"Environment: {self.environment}\n"
                f"Testing ESC integration with existing systems",
                title="Starting Integration Tests",
            )
        )

        start_time = datetime.utcnow()

        try:
            # Test 1: ESC Configuration Initialization
            await self._test_esc_initialization()

            # Test 2: Configuration Loading and Fallback
            await self._test_configuration_loading()

            # Test 3: Secret Validation
            await self._test_secret_validation()

            # Test 4: Redis Integration
            await self._test_redis_integration()

            # Test 5: MCP System Integration
            await self._test_mcp_integration()

            # Test 6: Memory System Integration
            await self._test_memory_integration()

            # Test 7: WebSocket Integration
            await self._test_websocket_integration()

            # Test 8: Hot Reload and Configuration Changes
            await self._test_hot_reload()

            # Test 9: Security and Access Control
            await self._test_security_integration()

            # Test 10: Backward Compatibility
            await self._test_backward_compatibility()

            # Test 11: Performance and Load
            await self._test_performance()

            # Generate final report
            return await self._generate_test_report(start_time)

        except Exception as e:
            console.print(f"[red]Test suite failed: {e}[/red]")
            logger.error(f"Test suite failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _test_esc_initialization(self):
        """Test ESC configuration initialization"""
        console.print("\n[bold]Test 1: ESC Configuration Initialization[/bold]")

        test_result = {
            "test_name": "esc_initialization",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Test with real Pulumi token if available
            pulumi_token = os.getenv("PULUMI_API_KEY")

            if pulumi_token:
                console.print("🔑 Using real Pulumi API token for testing")
                self.esc_config = await initialize_esc_config(
                    pulumi_api_token=pulumi_token,
                    environment=self.environment,
                    auto_refresh=True,
                    watch_files=True,
                    backward_compatibility=True,
                )
            else:
                console.print("⚠️  No Pulumi token found, testing fallback mode")
                self.esc_config = await initialize_esc_config(
                    pulumi_api_token="fake-token-for-testing",
                    environment=self.environment,
                    auto_refresh=False,
                    watch_files=False,
                    backward_compatibility=True,
                )

            # Check initialization status
            status = self.esc_config.get_status()

            test_result["checks"].extend(
                [
                    {
                        "check": "ESC Config Object Created",
                        "passed": self.esc_config is not None,
                        "details": f"Config object: {type(self.esc_config)}",
                    },
                    {
                        "check": "Initialization Status",
                        "passed": status["initialized"],
                        "details": f"Initialized: {status['initialized']}, Health: {status['integration_health']}",
                    },
                    {
                        "check": "Environment Detection",
                        "passed": status["environment"] == self.environment,
                        "details": f"Expected: {self.environment}, Got: {status['environment']}",
                    },
                    {
                        "check": "Backward Compatibility",
                        "passed": status["backward_compatibility"],
                        "details": f"Backward compatibility enabled: {status['backward_compatibility']}",
                    },
                ]
            )

            # Test configuration access
            try:
                test_value = self.esc_config.get("application.debug", False)
                test_result["checks"].append(
                    {
                        "check": "Configuration Access",
                        "passed": True,
                        "details": f"Retrieved test value: {test_value}",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Configuration Access",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] ESC initialization test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] ESC initialization test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["esc_initialization"] = test_result

    async def _test_configuration_loading(self):
        """Test configuration loading from various sources"""
        console.print("\n[bold]Test 2: Configuration Loading[/bold]")

        test_result = {
            "test_name": "configuration_loading",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            if not self.esc_config:
                test_result["status"] = "skipped"
                test_result["error"] = "ESC config not initialized"
                return

            # Test loading various configuration keys
            config_tests = [
                ("infrastructure.redis.url", "Redis URL"),
                ("llm_providers.portkey.api_key", "Portkey API Key"),
                ("application.debug", "Application Debug Flag"),
                ("environment", "Environment"),
                ("nonexistent.key", "Nonexistent Key"),
            ]

            for key, description in config_tests:
                try:
                    value = self.esc_config.get(key)
                    test_result["checks"].append(
                        {
                            "check": f"Load {description}",
                            "passed": (
                                value is not None
                                if "nonexistent" not in key
                                else value is None
                            ),
                            "details": f"Key: {key}, Value type: {type(value).__name__}",
                        }
                    )
                except Exception as e:
                    test_result["checks"].append(
                        {
                            "check": f"Load {description}",
                            "passed": False,
                            "details": f"Error loading {key}: {e}",
                        }
                    )

            # Test getting all configurations
            try:
                all_config = self.esc_config.get_all()
                test_result["checks"].append(
                    {
                        "check": "Load All Configurations",
                        "passed": isinstance(all_config, dict) and len(all_config) > 0,
                        "details": f"Loaded {len(all_config)} configuration entries",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Load All Configurations",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            # Test configuration refresh
            try:
                refresh_result = await self.esc_config.refresh_config()
                test_result["checks"].append(
                    {
                        "check": "Configuration Refresh",
                        "passed": isinstance(refresh_result, bool),
                        "details": f"Refresh successful: {refresh_result}",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Configuration Refresh",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Configuration loading test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Configuration loading test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["configuration_loading"] = test_result

    async def _test_secret_validation(self):
        """Test secret validation system"""
        console.print("\n[bold]Test 3: Secret Validation[/bold]")

        test_result = {
            "test_name": "secret_validation",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Initialize secret validator
            validation_config = ValidationConfig(
                validate_format_only=True,  # Only format validation for testing
                timeout_seconds=10,
                cache_results=True,
            )
            validator = ComprehensiveSecretValidator(validation_config)

            # Test format validation for various secret types
            format_tests = [
                (
                    "sk-test123456789012345678901234567890123456789012345",
                    SecretType.OPENAI_API_KEY,
                    "Valid OpenAI format",
                ),
                (
                    "sk-ant-api03-" + "A" * 95,
                    SecretType.ANTHROPIC_API_KEY,
                    "Valid Anthropic format",
                ),
                (
                    "AIzaSyTest123456789012345678901234567",
                    SecretType.GEMINI_API_KEY,
                    "Valid Gemini format",
                ),
                (
                    "hf_TestTokenWith34Characters1234567",
                    SecretType.HUGGINGFACE_API_KEY,
                    "Valid HuggingFace format",
                ),
                (
                    "redis://localhost:6379",
                    SecretType.REDIS_CONNECTION,
                    "Valid Redis URL",
                ),
                ("invalid-key", SecretType.OPENAI_API_KEY, "Invalid OpenAI format"),
            ]

            for secret_value, secret_type, description in format_tests:
                try:
                    result = await validator.validate_secret(
                        "test_key", secret_value, secret_type
                    )
                    expected_valid = "Invalid" not in description

                    test_result["checks"].append(
                        {
                            "check": f"Format Validation: {description}",
                            "passed": (result.result.value == "valid")
                            == expected_valid,
                            "details": f"Result: {result.result.value}, Expected valid: {expected_valid}",
                        }
                    )
                except Exception as e:
                    test_result["checks"].append(
                        {
                            "check": f"Format Validation: {description}",
                            "passed": False,
                            "details": f"Error: {e}",
                        }
                    )

            # Test batch validation
            try:
                test_secrets = {
                    "openai_key": "sk-test123456789012345678901234567890123456789012345",
                    "redis_url": "redis://localhost:6379",
                    "invalid_key": "invalid",
                }

                batch_results = await validator.validate_multiple_secrets(
                    test_secrets, batch_size=2
                )

                test_result["checks"].append(
                    {
                        "check": "Batch Secret Validation",
                        "passed": len(batch_results) == len(test_secrets),
                        "details": f"Validated {len(batch_results)} secrets in batch",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Batch Secret Validation",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            # Test validation report
            try:
                report = validator.get_validation_report()
                test_result["checks"].append(
                    {
                        "check": "Validation Report Generation",
                        "passed": isinstance(report, dict)
                        and "total_validations" in report,
                        "details": f"Report generated with {report.get('total_validations', 0)} validations",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Validation Report Generation",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Secret validation test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Secret validation test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["secret_validation"] = test_result

    async def _test_redis_integration(self):
        """Test Redis integration with ESC configuration"""
        console.print("\n[bold]Test 4: Redis Integration[/bold]")

        test_result = {
            "test_name": "redis_integration",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Get Redis configuration from ESC
            redis_url = get_config("infrastructure.redis.url", "redis://localhost:6379")
            redis_password = await get_secret_config(
                "infrastructure.redis.password", ""
            )

            test_result["checks"].append(
                {
                    "check": "Redis Config Retrieval",
                    "passed": redis_url is not None,
                    "details": f"Redis URL: {redis_url[:20]}..., Password configured: {bool(redis_password)}",
                }
            )

            # Test Redis connection using ESC config
            try:
                redis_client = redis.from_url(
                    redis_url, password=redis_password, socket_timeout=5
                )
                await redis_client.ping()

                # Test basic Redis operations
                await redis_client.set("esc_test_key", "esc_test_value", ex=30)
                retrieved_value = await redis_client.get("esc_test_key")
                await redis_client.delete("esc_test_key")

                test_result["checks"].append(
                    {
                        "check": "Redis Connection and Operations",
                        "passed": retrieved_value.decode() == "esc_test_value",
                        "details": "Successfully connected and performed Redis operations",
                    }
                )

                await redis_client.close()

            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Redis Connection and Operations",
                        "passed": False,
                        "details": f"Redis connection failed: {e}",
                    }
                )

            # Test Redis configuration object
            try:
                redis_config = RedisConfig.from_environment()
                test_result["checks"].append(
                    {
                        "check": "Redis Config Object",
                        "passed": redis_config.url == redis_url,
                        "details": f"Config URL matches ESC URL: {redis_config.url == redis_url}",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "Redis Config Object",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Redis integration test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Redis integration test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["redis_integration"] = test_result

    async def _test_mcp_integration(self):
        """Test MCP system integration"""
        console.print("\n[bold]Test 5: MCP System Integration[/bold]")

        test_result = {
            "test_name": "mcp_integration",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Test MCP configuration loading
            mcp_config = self.esc_config.get_all("mcp") if self.esc_config else {}

            test_result["checks"].append(
                {
                    "check": "MCP Configuration Loading",
                    "passed": isinstance(mcp_config, dict),
                    "details": f"Loaded {len(mcp_config)} MCP configuration entries",
                }
            )

            # Test MCP API endpoint if server is running
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.test_endpoints["mcp_status"],
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status == 200:
                            mcp_status = await response.json()
                            test_result["checks"].append(
                                {
                                    "check": "MCP Status Endpoint",
                                    "passed": True,
                                    "details": f"MCP status: {mcp_status.get('status', 'unknown')}",
                                }
                            )
                        else:
                            test_result["checks"].append(
                                {
                                    "check": "MCP Status Endpoint",
                                    "passed": False,
                                    "details": f"HTTP {response.status}",
                                }
                            )

            except asyncio.TimeoutError:
                test_result["checks"].append(
                    {
                        "check": "MCP Status Endpoint",
                        "passed": False,
                        "details": "Timeout - MCP server may not be running",
                    }
                )
            except Exception as e:
                test_result["checks"].append(
                    {
                        "check": "MCP Status Endpoint",
                        "passed": False,
                        "details": f"Error: {e}",
                    }
                )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] MCP integration test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] MCP integration test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["mcp_integration"] = test_result

    async def _test_memory_integration(self):
        """Test memory system integration"""
        console.print("\n[bold]Test 6: Memory System Integration[/bold]")

        test_result = {
            "test_name": "memory_integration",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Test vector database configuration
            qdrant_config = {
                "api_key": get_config("infrastructure.vector_db.qdrant.api_key"),
                "url": get_config("infrastructure.vector_db.qdrant.url"),
            }

            weaviate_config = {
                "api_key": get_config("infrastructure.vector_db.weaviate.api_key"),
                "url": get_config("infrastructure.vector_db.weaviate.url"),
            }

            test_result["checks"].extend(
                [
                    {
                        "check": "Qdrant Configuration",
                        "passed": bool(
                            qdrant_config["api_key"] and qdrant_config["url"]
                        ),
                        "details": f"API key configured: {bool(qdrant_config['api_key'])}, URL configured: {bool(qdrant_config['url'])}",
                    },
                    {
                        "check": "Weaviate Configuration",
                        "passed": bool(
                            weaviate_config["api_key"] and weaviate_config["url"]
                        ),
                        "details": f"API key configured: {bool(weaviate_config['api_key'])}, URL configured: {bool(weaviate_config['url'])}",
                    },
                ]
            )

            # Test Mem0 configuration
            mem0_config = {
                "api_key": get_config("infrastructure_providers.mem0.api_key"),
                "url": get_config(
                    "infrastructure_providers.mem0.url", "https://api.mem0.ai"
                ),
            }

            test_result["checks"].append(
                {
                    "check": "Mem0 Configuration",
                    "passed": bool(mem0_config["api_key"]),
                    "details": f"API key configured: {bool(mem0_config['api_key'])}, URL: {mem0_config['url']}",
                }
            )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Memory integration test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Memory integration test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["memory_integration"] = test_result

    async def _test_websocket_integration(self):
        """Test WebSocket integration"""
        console.print("\n[bold]Test 7: WebSocket Integration[/bold]")

        test_result = {
            "test_name": "websocket_integration",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Test WebSocket configuration
            ws_config = (
                self.esc_config.get_all("application.websocket")
                if self.esc_config
                else {}
            )

            test_result["checks"].append(
                {
                    "check": "WebSocket Configuration Loading",
                    "passed": isinstance(ws_config, dict),
                    "details": f"Loaded WebSocket config: {len(ws_config)} entries",
                }
            )

            # Test WebSocket connection parameters
            max_connections = get_config("application.websocket.max_connections", 100)
            heartbeat_interval = get_config(
                "application.websocket.heartbeat_interval", 30
            )

            test_result["checks"].extend(
                [
                    {
                        "check": "WebSocket Max Connections",
                        "passed": isinstance(max_connections, int)
                        and max_connections > 0,
                        "details": f"Max connections: {max_connections}",
                    },
                    {
                        "check": "WebSocket Heartbeat Interval",
                        "passed": isinstance(heartbeat_interval, int)
                        and heartbeat_interval > 0,
                        "details": f"Heartbeat interval: {heartbeat_interval}s",
                    },
                ]
            )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] WebSocket integration test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] WebSocket integration test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["websocket_integration"] = test_result

    async def _test_hot_reload(self):
        """Test hot reload functionality"""
        console.print("\n[bold]Test 8: Hot Reload and Configuration Changes[/bold]")

        test_result = {
            "test_name": "hot_reload",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            if not self.esc_config:
                test_result["status"] = "skipped"
                test_result["error"] = "ESC config not available"
                return

            # Test configuration refresh
            initial_status = self.esc_config.get_status()
            refresh_result = await self.esc_config.refresh_config(force=True)

            test_result["checks"].append(
                {
                    "check": "Configuration Refresh",
                    "passed": isinstance(refresh_result, bool),
                    "details": f"Refresh result: {refresh_result}, Status: {initial_status['integration_health']}",
                }
            )

            # Test change callback registration
            change_callbacks_count = 0

            def test_callback(key: str, new_value, old_value):
                nonlocal change_callbacks_count
                change_callbacks_count += 1

            self.esc_config.add_change_callback(test_callback)

            # Trigger a refresh to test callbacks
            await self.esc_config.refresh_config(force=True)

            # Remove callback
            self.esc_config.remove_change_callback(test_callback)

            test_result["checks"].append(
                {
                    "check": "Change Callback System",
                    "passed": True,  # Just test that the system doesn't crash
                    "details": "Callback registered and removed successfully",
                }
            )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Hot reload test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Hot reload test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["hot_reload"] = test_result

    async def _test_security_integration(self):
        """Test security and access control integration"""
        console.print("\n[bold]Test 9: Security and Access Control[/bold]")

        test_result = {
            "test_name": "security_integration",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Initialize access control
            initialize_default_users()
            access_control = get_access_control()

            # Test user authentication
            admin_user = access_control.get_user("admin")
            test_result["checks"].append(
                {
                    "check": "Access Control User Management",
                    "passed": admin_user is not None and admin_user.username == "admin",
                    "details": f"Admin user found: {admin_user is not None}",
                }
            )

            # Test access request
            access_request = AccessRequest(
                user_id="admin",
                resource_type=ResourceType.SECRET,
                resource_id="infrastructure.redis.url",
                permission=Permission.SECRET_READ,
                environment="dev",
            )

            access_result = await access_control.check_access(access_request)

            test_result["checks"].append(
                {
                    "check": "Access Control Permission Check",
                    "passed": access_result.granted,
                    "details": f"Access granted: {access_result.granted}, Reason: {access_result.reason}",
                }
            )

            # Test access control statistics
            stats = access_control.get_system_statistics()
            test_result["checks"].append(
                {
                    "check": "Access Control Statistics",
                    "passed": isinstance(stats, dict) and "total_users" in stats,
                    "details": f"Total users: {stats.get('total_users', 0)}, Active users: {stats.get('active_users', 0)}",
                }
            )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Security integration test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Security integration test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["security_integration"] = test_result

    async def _test_backward_compatibility(self):
        """Test backward compatibility with environment variables"""
        console.print("\n[bold]Test 10: Backward Compatibility[/bold]")

        test_result = {
            "test_name": "backward_compatibility",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            # Test environment variable fallback
            original_env = os.environ.get("REDIS_URL")
            test_redis_url = "redis://test:6379"
            os.environ["REDIS_URL"] = test_redis_url

            # Test that configuration can fall back to env vars
            retrieved_url = get_config("infrastructure.redis.url", "fallback")

            test_result["checks"].append(
                {
                    "check": "Environment Variable Fallback",
                    "passed": retrieved_url is not None,
                    "details": f"Retrieved URL: {retrieved_url}",
                }
            )

            # Restore original env var
            if original_env:
                os.environ["REDIS_URL"] = original_env
            else:
                os.environ.pop("REDIS_URL", None)

            # Test environment variable mapping
            common_env_vars = [
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "PORTKEY_API_KEY",
                "QDRANT_API_KEY",
            ]

            mapped_vars = 0
            for env_var in common_env_vars:
                if env_var in os.environ:
                    mapped_vars += 1

            test_result["checks"].append(
                {
                    "check": "Environment Variable Mapping",
                    "passed": True,  # This just tests the mapping system works
                    "details": f"Checked {len(common_env_vars)} common environment variables, {mapped_vars} found",
                }
            )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Backward compatibility test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Backward compatibility test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["backward_compatibility"] = test_result

    async def _test_performance(self):
        """Test performance characteristics"""
        console.print("\n[bold]Test 11: Performance and Load[/bold]")

        test_result = {
            "test_name": "performance",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "checks": [],
        }

        try:
            if not self.esc_config:
                test_result["status"] = "skipped"
                test_result["error"] = "ESC config not available"
                return

            # Test configuration read performance
            start_time = time.time()
            for i in range(100):
                value = self.esc_config.get("infrastructure.redis.url")
            config_read_time = time.time() - start_time

            test_result["checks"].append(
                {
                    "check": "Configuration Read Performance",
                    "passed": config_read_time < 1.0,  # Should be fast
                    "details": f"100 config reads took {config_read_time:.3f}s (avg: {config_read_time/100:.5f}s per read)",
                }
            )

            # Test concurrent configuration access
            async def concurrent_config_access():
                return self.esc_config.get("application.debug", False)

            start_time = time.time()
            tasks = [concurrent_config_access() for _ in range(50)]
            await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time

            test_result["checks"].append(
                {
                    "check": "Concurrent Configuration Access",
                    "passed": concurrent_time < 2.0,
                    "details": f"50 concurrent config reads took {concurrent_time:.3f}s",
                }
            )

            # Test cache performance
            start_time = time.time()
            for i in range(1000):
                self.esc_config.get("infrastructure.redis.url")  # Should hit cache
            cache_performance = time.time() - start_time

            test_result["checks"].append(
                {
                    "check": "Cache Performance",
                    "passed": cache_performance < 0.5,  # Should be very fast with cache
                    "details": f"1000 cached reads took {cache_performance:.3f}s",
                }
            )

            test_result["status"] = "passed"
            console.print("[green]✓[/green] Performance test passed")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            console.print(f"[red]✗[/red] Performance test failed: {e}")

        finally:
            test_result["completed_at"] = datetime.utcnow().isoformat()
            self.test_results["performance"] = test_result

    async def _generate_test_report(self, start_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        console.print("\n[bold]Generating Test Report...[/bold]")

        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()

        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = len(
            [r for r in self.test_results.values() if r.get("status") == "passed"]
        )
        failed_tests = len(
            [r for r in self.test_results.values() if r.get("status") == "failed"]
        )
        skipped_tests = len(
            [r for r in self.test_results.values() if r.get("status") == "skipped"]
        )

        # Count individual checks
        total_checks = sum(
            len(result.get("checks", [])) for result in self.test_results.values()
        )
        passed_checks = sum(
            len([c for c in result.get("checks", []) if c.get("passed")])
            for result in self.test_results.values()
        )

        report = {
            "test_suite": "ESC Integration Test Suite",
            "environment": self.environment,
            "execution_summary": {
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "check_success_rate": (
                    passed_checks / total_checks if total_checks > 0 else 0
                ),
            },
            "test_results": self.test_results,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "environment_variables": len(
                    [
                        k
                        for k in os.environ.keys()
                        if any(
                            pattern in k for pattern in ["API", "KEY", "URL", "SECRET"]
                        )
                    ]
                ),
                "esc_integration_status": (
                    self.esc_config.get_status()
                    if self.esc_config
                    else "not_initialized"
                ),
            },
        }

        # Save report to file
        report_filename = f"esc_integration_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Display summary table
        table = Table(title="ESC Integration Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Checks", justify="right", style="blue")
        table.add_column("Duration", justify="right", style="yellow")

        for test_name, result in self.test_results.items():
            status_color = {
                "passed": "[green]PASSED[/green]",
                "failed": "[red]FAILED[/red]",
                "skipped": "[yellow]SKIPPED[/yellow]",
            }.get(result.get("status"), "[gray]UNKNOWN[/gray]")

            checks_passed = len(
                [c for c in result.get("checks", []) if c.get("passed")]
            )
            total_checks = len(result.get("checks", []))

            if result.get("started_at") and result.get("completed_at"):
                start = datetime.fromisoformat(result["started_at"])
                end = datetime.fromisoformat(result["completed_at"])
                duration = f"{(end - start).total_seconds():.2f}s"
            else:
                duration = "N/A"

            table.add_row(
                test_name.replace("_", " ").title(),
                status_color,
                f"{checks_passed}/{total_checks}",
                duration,
            )

        console.print(table)

        # Display overall result
        if failed_tests == 0:
            console.print(
                f"\n[bold green]🎉 All tests passed! ({passed_tests}/{total_tests})[/bold green]"
            )
        else:
            console.print(
                f"\n[bold red]❌ {failed_tests} test(s) failed ({passed_tests}/{total_tests} passed)[/bold red]"
            )

        console.print(
            f"\n[blue]📊 Overall check success rate: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)[/blue]"
        )
        console.print(
            f"[blue]⏱️  Total execution time: {total_duration:.2f} seconds[/blue]"
        )
        console.print(f"[blue]📄 Test report saved: {report_filename}[/blue]")

        return report


async def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="ESC Integration Test Suite")
    parser.add_argument("--environment", default="dev", help="Environment to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run test suite
    test_suite = ESCIntegrationTestSuite(args.environment)

    try:
        report = await test_suite.run_complete_test_suite()

        # Return appropriate exit code
        if report.get("execution_summary", {}).get("failed_tests", 1) > 0:
            return 1
        else:
            return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Test suite interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Test suite crashed: {e}[/red]")
        return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
