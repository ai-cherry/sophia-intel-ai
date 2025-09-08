#!/usr/bin/env python3
"""
Artemis Domain MCP Server Contract
Specialized contract for Artemis (development/technical) domain servers
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any

from .base_contract import (
    BaseMCPServerContract,
    CapabilityDeclaration,
    CapabilityStatus,
    HealthCheckResult,
    HealthStatus,
    MCPRequest,
    MCPResponse,
)


class CodeAnalysisRequest(MCPRequest):
    """Specialized request for code analysis"""

    def __init__(self, **data):
        super().__init__(**data)
        # Artemis-specific validations can be added here


class CodeAnalysisResult(dict):
    """Specialized result for code analysis"""

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure required fields for code analysis results
        self.setdefault("analysis_type", "unknown")
        self.setdefault("findings", [])
        self.setdefault("metrics", {})
        self.setdefault("recommendations", [])


class FilesystemRequest(MCPRequest):
    """Specialized request for filesystem operations"""

    def __init__(self, **data):
        super().__init__(**data)
        # Add filesystem-specific validation


class ArtemisServerContract(BaseMCPServerContract):
    """
    Artemis domain contract for technical/development MCP servers
    Extends base contract with Artemis-specific capabilities
    """

    def __init__(self, server_id: str, name: str, version: str = "1.0.0"):
        super().__init__(server_id, name, version)

        # Register standard Artemis capabilities
        asyncio.create_task(self._register_standard_capabilities())

    async def _register_standard_capabilities(self):
        """Register standard Artemis capabilities"""

        # Code Analysis Capability
        code_analysis = CapabilityDeclaration(
            name="code_analysis",
            methods=[
                "analyze_file",
                "analyze_directory",
                "quality_check",
                "complexity_analysis",
                "dependency_analysis",
                "security_scan",
                "performance_analysis",
            ],
            description="Comprehensive code analysis and quality assessment",
            requirements=["file_path"],
            dependencies=["filesystem"],
            configuration={
                "supported_languages": [
                    "python",
                    "javascript",
                    "typescript",
                    "go",
                    "rust",
                    "java",
                ],
                "analysis_depth": ["shallow", "medium", "deep"],
                "output_formats": ["json", "markdown", "html"],
            },
        )
        await self.register_capability(code_analysis)

        # Filesystem Capability
        filesystem = CapabilityDeclaration(
            name="filesystem",
            methods=[
                "read_file",
                "write_file",
                "list_directory",
                "create_directory",
                "delete_file",
                "move_file",
                "copy_file",
                "search_files",
                "watch_directory",
            ],
            description="File system operations for code repositories",
            requirements=["path"],
            configuration={
                "max_file_size": "100MB",
                "supported_encodings": ["utf-8", "ascii", "latin1"],
                "watch_events": ["create", "modify", "delete", "move"],
            },
        )
        await self.register_capability(filesystem)

        # Git Operations Capability
        git_ops = CapabilityDeclaration(
            name="git_operations",
            methods=[
                "status",
                "diff",
                "log",
                "commit",
                "push",
                "pull",
                "branch",
                "merge",
                "blame",
                "show",
            ],
            description="Git repository operations and version control",
            requirements=["repository_path"],
            dependencies=["filesystem"],
            configuration={
                "max_commit_size": "50MB",
                "supported_protocols": ["https", "ssh"],
                "auto_fetch": True,
            },
        )
        await self.register_capability(git_ops)

        # Test Generation Capability
        test_generation = CapabilityDeclaration(
            name="test_generation",
            methods=[
                "generate_unit_tests",
                "generate_integration_tests",
                "generate_test_data",
                "analyze_test_coverage",
                "suggest_test_improvements",
            ],
            description="Automated test generation and analysis",
            requirements=["source_file"],
            dependencies=["code_analysis", "filesystem"],
            configuration={
                "test_frameworks": ["pytest", "jest", "junit", "go_test"],
                "coverage_threshold": 80,
                "mock_strategies": ["manual", "automatic", "hybrid"],
            },
        )
        await self.register_capability(test_generation)

        # Refactoring Capability
        refactoring = CapabilityDeclaration(
            name="refactoring",
            methods=[
                "extract_method",
                "extract_class",
                "rename_symbol",
                "move_file",
                "optimize_imports",
                "remove_dead_code",
                "apply_pattern",
            ],
            description="Code refactoring and optimization operations",
            requirements=["target_file", "refactoring_type"],
            dependencies=["code_analysis", "filesystem"],
            configuration={
                "safety_checks": True,
                "backup_before_refactor": True,
                "validation_required": True,
            },
        )
        await self.register_capability(refactoring)

    # Artemis-specific abstract methods

    @abstractmethod
    async def analyze_codebase(
        self, request: CodeAnalysisRequest
    ) -> CodeAnalysisResult:
        """Analyze codebase with Artemis intelligence"""
        pass

    @abstractmethod
    async def perform_filesystem_operation(
        self, request: FilesystemRequest
    ) -> dict[str, Any]:
        """Perform filesystem operation with security and validation"""
        pass

    @abstractmethod
    async def generate_code_suggestions(
        self, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate intelligent code suggestions"""
        pass

    # Enhanced health check for Artemis servers

    async def perform_health_check(self) -> HealthCheckResult:
        """Perform Artemis-specific health check"""
        start_time = datetime.now()

        try:
            health_details = {}
            capabilities_status = {}

            # Check filesystem access
            try:
                # Test basic filesystem operations
                import tempfile

                with tempfile.NamedTemporaryFile(delete=True) as tmp:
                    tmp.write(b"health_check_test")
                    tmp.flush()

                    # Test read
                    with open(tmp.name, "rb") as f:
                        content = f.read()

                    if content == b"health_check_test":
                        health_details["filesystem"] = "operational"
                        capabilities_status["filesystem"] = CapabilityStatus.AVAILABLE
                    else:
                        health_details["filesystem"] = "read_error"
                        capabilities_status["filesystem"] = CapabilityStatus.DEGRADED

            except Exception as e:
                health_details["filesystem"] = f"error: {str(e)}"
                capabilities_status["filesystem"] = CapabilityStatus.UNAVAILABLE

            # Check git availability
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "--version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    health_details["git"] = f"available: {result.stdout.strip()}"
                    capabilities_status["git_operations"] = CapabilityStatus.AVAILABLE
                else:
                    health_details["git"] = "command_failed"
                    capabilities_status["git_operations"] = CapabilityStatus.UNAVAILABLE
            except Exception as e:
                health_details["git"] = f"error: {str(e)}"
                capabilities_status["git_operations"] = CapabilityStatus.UNAVAILABLE

            # Check code analysis tools availability
            analysis_tools = {
                "ast": "Python AST parsing",
                "pathlib": "Path operations",
                "json": "JSON processing",
            }

            available_tools = []
            for tool, description in analysis_tools.items():
                try:
                    __import__(tool)
                    available_tools.append(f"{tool}: {description}")
                except ImportError:
                    pass

            health_details["analysis_tools"] = available_tools
            if available_tools:
                capabilities_status["code_analysis"] = CapabilityStatus.AVAILABLE
            else:
                capabilities_status["code_analysis"] = CapabilityStatus.DEGRADED

            # Determine overall health
            unavailable_count = sum(
                1
                for status in capabilities_status.values()
                if status == CapabilityStatus.UNAVAILABLE
            )

            if unavailable_count == 0:
                overall_status = HealthStatus.HEALTHY
            elif unavailable_count <= len(capabilities_status) // 2:
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.UNHEALTHY

            response_time = (datetime.now() - start_time).total_seconds()

            return HealthCheckResult(
                status=overall_status,
                timestamp=datetime.now(),
                response_time=response_time,
                details=health_details,
                capabilities_status=capabilities_status,
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.now(),
                response_time=response_time,
                details={"error": str(e)},
                error_message=f"Health check failed: {str(e)}",
            )

    # Artemis-specific request handling

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle Artemis-specific requests with enhanced processing"""
        start_time = datetime.now()

        try:
            # Update connection activity
            await self.update_connection_activity(request.client_id)

            # Validate request
            is_valid, error_message = await self.validate_request(request)
            if not is_valid:
                return await self.create_error_response(
                    request,
                    error_message,
                    "VALIDATION_ERROR",
                    (datetime.now() - start_time).total_seconds(),
                )

            # Route to capability-specific handler
            if request.capability == "code_analysis":
                result = await self._handle_code_analysis(request)
            elif request.capability == "filesystem":
                result = await self._handle_filesystem(request)
            elif request.capability == "git_operations":
                result = await self._handle_git_operations(request)
            elif request.capability == "test_generation":
                result = await self._handle_test_generation(request)
            elif request.capability == "refactoring":
                result = await self._handle_refactoring(request)
            else:
                return await self.create_error_response(
                    request,
                    f"Unsupported capability: {request.capability}",
                    "CAPABILITY_NOT_SUPPORTED",
                    (datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            return await self.create_success_response(request, result, execution_time)

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            # Update error count
            if request.client_id in self.active_connections:
                self.active_connections[request.client_id].error_count += 1

            return await self.create_error_response(
                request,
                f"Internal server error: {str(e)}",
                "INTERNAL_ERROR",
                execution_time,
            )

    # Capability-specific handlers (to be implemented by concrete servers)

    async def _handle_code_analysis(self, request: MCPRequest) -> dict[str, Any]:
        """Handle code analysis requests"""
        # Default implementation - to be overridden
        return {"message": "Code analysis capability not implemented"}

    async def _handle_filesystem(self, request: MCPRequest) -> dict[str, Any]:
        """Handle filesystem requests"""
        # Default implementation - to be overridden
        return {"message": "Filesystem capability not implemented"}

    async def _handle_git_operations(self, request: MCPRequest) -> dict[str, Any]:
        """Handle git operation requests"""
        # Default implementation - to be overridden
        return {"message": "Git operations capability not implemented"}

    async def _handle_test_generation(self, request: MCPRequest) -> dict[str, Any]:
        """Handle test generation requests"""
        # Default implementation - to be overridden
        return {"message": "Test generation capability not implemented"}

    async def _handle_refactoring(self, request: MCPRequest) -> dict[str, Any]:
        """Handle refactoring requests"""
        # Default implementation - to be overridden
        return {"message": "Refactoring capability not implemented"}


# Import needed for async task in __init__
import asyncio
