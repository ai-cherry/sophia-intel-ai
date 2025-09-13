"""
Typed Tool Call Interfaces
This module defines explicit Pydantic schemas for tool invocations,
improving validation, discoverability, and type safety across the agent framework.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from pydantic import BaseModel, Field, validator
class ToolCategory(str, Enum):
    """Categories of tools available to agents"""
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    RESEARCH = "research"
    SECURITY = "security"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    FILE_OPERATIONS = "file_operations"
    WEB_OPERATIONS = "web_operations"
    DATABASE = "database"
class ToolPriority(str, Enum):
    """Tool execution priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
class ToolParameter(BaseModel):
    """Schema for a tool parameter"""
    name: str
    type: str  # python type name
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum_values: Optional[list[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # regex pattern for validation
    @validator("type")
    def validate_type(cls, v):
        valid_types = ["str", "int", "float", "bool", "list", "dict", "Any"]
        if v not in valid_types:
            raise ValueError(f"Invalid type: {v}. Must be one of {valid_types}")
        return v
class ToolCall(BaseModel):
    """Base schema for tool invocation"""
    tool_name: str = Field(..., description="Name of the tool to invoke")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    category: ToolCategory = Field(ToolCategory.ANALYSIS, description="Tool category")
    priority: ToolPriority = Field(
        ToolPriority.MEDIUM, description="Execution priority"
    )
    timeout_seconds: int = Field(30, ge=1, le=300, description="Maximum execution time")
    retry_on_failure: bool = Field(True, description="Whether to retry on failure")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    class Config:
        use_enum_values = True
class PlanningToolCall(ToolCall):
    """Schema for planning tool calls"""
    category: ToolCategory = Field(default=ToolCategory.PLANNING)
    class CreateTimelineParams(BaseModel):
        project_name: str
        tasks: list[str]
        start_date: datetime
        end_date: Optional[datetime] = None
        dependencies: Optional[dict[str, list[str]]] = None
    class AnalyzeDependenciesParams(BaseModel):
        tasks: list[dict[str, Any]]
        identify_circular: bool = True
        suggest_parallelization: bool = True
    class EstimateResourcesParams(BaseModel):
        project_scope: dict[str, Any]
        team_size: int
        skill_levels: dict[str, str]
    class AssessRisksParams(BaseModel):
        project_description: str
        known_constraints: list[str]
        risk_tolerance: str = "medium"
class CodingToolCall(ToolCall):
    """Schema for coding tool calls"""
    category: ToolCategory = Field(default=ToolCategory.CODING)
    class CodeSearchParams(BaseModel):
        query: str
        language: Optional[str] = None
        file_pattern: Optional[str] = None
        include_tests: bool = False
        max_results: int = Field(10, ge=1, le=100)
    class GitOperationParams(BaseModel):
        operation: str  # add, commit, push, pull, branch, merge
        files: Optional[list[str]] = None
        message: Optional[str] = None
        branch: Optional[str] = None
    class TestingParams(BaseModel):
        test_type: str  # unit, integration, e2e
        test_files: Optional[list[str]] = None
        coverage_threshold: float = Field(0.8, ge=0.0, le=1.0)
        parallel: bool = True
class SecurityToolCall(ToolCall):
    """Schema for security tool calls"""
    category: ToolCategory = Field(default=ToolCategory.SECURITY)
    class VulnerabilityScanParams(BaseModel):
        target: str  # file path, URL, or system identifier
        scan_type: str  # static, dynamic, dependency
        severity_threshold: str = "medium"
        include_false_positives: bool = False
    class ComplianceCheckParams(BaseModel):
        framework: str  # OWASP, NIST, ISO27001, SOC2, GDPR, HIPAA
        scope: dict[str, Any]
        generate_report: bool = True
    class ThreatModelParams(BaseModel):
        system_design: dict[str, Any]
        methodology: str = "STRIDE"
        asset_values: Optional[dict[str, str]] = None
class ResearchToolCall(ToolCall):
    """Schema for research tool calls"""
    category: ToolCategory = Field(default=ToolCategory.RESEARCH)
    class WebSearchParams(BaseModel):
        query: str
        max_results: int = Field(10, ge=1, le=50)
        domains: Optional[list[str]] = None
        exclude_domains: Optional[list[str]] = None
        date_range: Optional[tuple[datetime, datetime]] = None
    class DocumentAnalysisParams(BaseModel):
        document_path: str
        analysis_type: str  # summary, sentiment, entities, topics
        output_format: str = "json"
    class SummarizeParams(BaseModel):
        content: str
        max_length: int = Field(500, ge=50, le=5000)
        style: str = "concise"  # concise, detailed, technical, simple
class ToolResponse(BaseModel):
    """Schema for tool execution response"""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = Field(..., ge=0.0)
    retry_count: int = Field(0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
class ToolDefinition(BaseModel):
    """Complete tool definition schema"""
    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter]
    returns: str  # description of return value
    examples: list[dict[str, Any]] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    cost_estimate: Optional[float] = None
    average_execution_time: Optional[float] = None
    success_rate: Optional[float] = None
    def validate_call(self, call: ToolCall) -> tuple[bool, Optional[str]]:
        """Validate a tool call against this definition"""
        if call.tool_name != self.name:
            return False, f"Tool name mismatch: {call.tool_name} != {self.name}"
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in call.parameters:
                return False, f"Missing required parameter: {param.name}"
            # Validate parameter value if present
            if param.name in call.parameters:
                value = call.parameters[param.name]
                # Check enum values
                if param.enum_values and value not in param.enum_values:
                    return (
                        False,
                        f"Invalid value for {param.name}: {value} not in {param.enum_values}",
                    )
                # Check numeric ranges
                if param.min_value is not None and value < param.min_value:
                    return (
                        False,
                        f"Value for {param.name} below minimum: {value} < {param.min_value}",
                    )
                if param.max_value is not None and value > param.max_value:
                    return (
                        False,
                        f"Value for {param.name} above maximum: {value} > {param.max_value}",
                    )
        return True, None
class ToolRegistry(BaseModel):
    """Registry of available tools"""
    tools: dict[str, ToolDefinition] = Field(default_factory=dict)
    categories: dict[ToolCategory, list[str]] = Field(default_factory=dict)
    def register_tool(self, definition: ToolDefinition) -> None:
        """Register a new tool"""
        self.tools[definition.name] = definition
        if definition.category not in self.categories:
            self.categories[definition.category] = []
        if definition.name not in self.categories[definition.category]:
            self.categories[definition.category].append(definition.name)
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        return self.tools.get(name)
    def get_tools_by_category(self, category: ToolCategory) -> list[ToolDefinition]:
        """Get all tools in a category"""
        tool_names = self.categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    def validate_call(self, call: ToolCall) -> tuple[bool, Optional[str]]:
        """Validate a tool call"""
        tool = self.get_tool(call.tool_name)
        if not tool:
            return False, f"Unknown tool: {call.tool_name}"
        return tool.validate_call(call)
# Example tool definitions
def get_default_tool_definitions() -> list[ToolDefinition]:
    """Get default tool definitions"""
    return [
        ToolDefinition(
            name="create_timeline",
            description="Create a project timeline with milestones",
            category=ToolCategory.PLANNING,
            parameters=[
                ToolParameter(
                    name="project_name", type="str", description="Name of the project"
                ),
                ToolParameter(name="tasks", type="list", description="List of tasks"),
                ToolParameter(
                    name="start_date", type="str", description="Start date (ISO format)"
                ),
                ToolParameter(
                    name="end_date",
                    type="str",
                    description="End date (ISO format)",
                    required=False,
                ),
            ],
            returns="Timeline object with milestones and dependencies",
        ),
        ToolDefinition(
            name="code_search",
            description="Search for code patterns in the repository",
            category=ToolCategory.CODING,
            parameters=[
                ToolParameter(
                    name="query", type="str", description="Search query or pattern"
                ),
                ToolParameter(
                    name="language",
                    type="str",
                    description="Programming language",
                    required=False,
                ),
                ToolParameter(
                    name="max_results",
                    type="int",
                    description="Maximum results",
                    default=10,
                    min_value=1,
                    max_value=100,
                ),
            ],
            returns="List of code matches with file paths and line numbers",
        ),
        ToolDefinition(
            name="vulnerability_scan",
            description="Scan for security vulnerabilities",
            category=ToolCategory.SECURITY,
            parameters=[
                ToolParameter(name="target", type="str", description="Target to scan"),
                ToolParameter(
                    name="scan_type",
                    type="str",
                    description="Type of scan",
                    enum_values=["static", "dynamic", "dependency"],
                ),
                ToolParameter(
                    name="severity_threshold",
                    type="str",
                    description="Minimum severity",
                    default="medium",
                    enum_values=["low", "medium", "high", "critical"],
                ),
            ],
            returns="List of vulnerabilities with severity and remediation suggestions",
        ),
        ToolDefinition(
            name="web_search",
            description="Search the web for information",
            category=ToolCategory.RESEARCH,
            parameters=[
                ToolParameter(name="query", type="str", description="Search query"),
                ToolParameter(
                    name="max_results",
                    type="int",
                    description="Maximum results",
                    default=10,
                    min_value=1,
                    max_value=50,
                ),
                ToolParameter(
                    name="domains",
                    type="list",
                    description="Domains to include",
                    required=False,
                ),
            ],
            returns="List of search results with titles, URLs, and snippets",
        ),
    ]
# Global tool registry
global_tool_registry = ToolRegistry()
# Register default tools
for tool_def in get_default_tool_definitions():
    global_tool_registry.register_tool(tool_def)
