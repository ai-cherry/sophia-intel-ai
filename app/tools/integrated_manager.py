"""Integrated Tool Manager with shared context and orchestration."""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import asynccontextmanager
import json
from pathlib import Path

# Tool imports - using mock tools for now since agno isn't available
class Tool:
    """Base tool class."""
    def __init__(self):
        pass
    
    async def run(self, **kwargs):
        """Run the tool."""
        return f"Tool executed with args: {kwargs}"

# Mock tool implementations for testing
class CodeSearch(Tool): pass
class SmartCodeSearch(Tool): pass
class GitStatus(Tool): pass
class GitDiff(Tool): pass
class GitCommit(Tool): pass
class GitAdd(Tool): pass
class ReadFile(Tool): pass
class WriteFile(Tool): pass
class ListDirectory(Tool): pass
class RunTests(Tool): pass
class RunTypeCheck(Tool): pass
class RunLint(Tool): pass
class FormatCode(Tool): pass

logger = logging.getLogger(__name__)

@dataclass
class ToolExecutionContext:
    """Shared context for tool executions."""
    session_id: str
    task_description: str
    workspace_path: Path = field(default_factory=lambda: Path.cwd())
    git_status: Optional[Dict] = None
    modified_files: List[str] = field(default_factory=list)
    test_results: Optional[Dict] = None
    lint_results: Optional[Dict] = None
    execution_history: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolResult:
    """Enhanced tool result with metadata."""
    tool_name: str
    success: bool
    output: str
    execution_time_ms: float
    context_updates: Dict[str, Any] = field(default_factory=dict)
    suggested_next_tools: List[str] = field(default_factory=list)
    confidence_score: float = 1.0

class IntegratedToolManager:
    """Orchestrates tools with shared context and intelligent workflows."""
    
    def __init__(self):
        self.tools = self._register_tools()
        self.contexts: Dict[str, ToolExecutionContext] = {}
        self.workflows: Dict[str, List[Dict]] = self._define_workflows()
        self.metrics = {"executions": 0, "failures": 0, "avg_time": 0.0}
    
    def _register_tools(self) -> Dict[str, Tool]:
        """Register all available tools."""
        tools = {}
        
        # File operations
        tools["read_file"] = ReadFile()
        tools["write_file"] = WriteFile()
        tools["list_directory"] = ListDirectory()
        
        # Git operations  
        tools["git_status"] = GitStatus()
        tools["git_diff"] = GitDiff()
        tools["git_add"] = GitAdd()
        tools["git_commit"] = GitCommit()
        
        # Code search
        tools["code_search"] = CodeSearch()
        tools["smart_code_search"] = SmartCodeSearch()
        
        # Quality assurance
        tools["run_tests"] = RunTests()
        tools["run_typecheck"] = RunTypeCheck()
        tools["run_lint"] = RunLint()
        tools["format_code"] = FormatCode()
        
        return tools
    
    def _define_workflows(self) -> Dict[str, List[Dict]]:
        """Define intelligent tool workflows."""
        return {
            "code_implementation": [
                {"tool": "code_search", "purpose": "find_similar_patterns"},
                {"tool": "read_file", "purpose": "understand_context"},
                {"tool": "write_file", "purpose": "implement_feature"},
                {"tool": "run_tests", "purpose": "validate_implementation"},
                {"tool": "run_lint", "purpose": "check_quality"},
                {"tool": "git_add", "purpose": "stage_changes"},
                {"tool": "git_commit", "purpose": "commit_changes"}
            ],
            "code_review": [
                {"tool": "git_status", "purpose": "check_modifications"},
                {"tool": "git_diff", "purpose": "review_changes"},
                {"tool": "run_lint", "purpose": "quality_check"},
                {"tool": "run_tests", "purpose": "regression_check"},
                {"tool": "run_typecheck", "purpose": "type_safety"}
            ],
            "bug_investigation": [
                {"tool": "git_status", "purpose": "check_state"},
                {"tool": "code_search", "purpose": "find_related_code"},
                {"tool": "run_tests", "purpose": "reproduce_issue"},
                {"tool": "git_diff", "purpose": "recent_changes"},
                {"tool": "read_file", "purpose": "examine_suspects"}
            ],
            "refactoring": [
                {"tool": "run_tests", "purpose": "baseline_tests"},
                {"tool": "code_search", "purpose": "find_dependencies"},
                {"tool": "write_file", "purpose": "apply_refactoring"},
                {"tool": "run_tests", "purpose": "verify_functionality"},
                {"tool": "run_lint", "purpose": "check_style"},
                {"tool": "format_code", "purpose": "format_changes"}
            ]
        }
    
    async def create_context(self, session_id: str, task_description: str) -> ToolExecutionContext:
        """Create a new execution context for a session."""
        context = ToolExecutionContext(
            session_id=session_id,
            task_description=task_description,
            workspace_path=Path.cwd()
        )
        self.contexts[session_id] = context
        
        # Initialize context with workspace state
        await self._populate_initial_context(context)
        return context
    
    async def _populate_initial_context(self, context: ToolExecutionContext):
        """Populate context with current workspace state."""
        try:
            # Get git status
            git_tool = self.tools["git_status"]
            git_result = await git_tool.run()
            context.git_status = {"output": git_result, "timestamp": datetime.now()}
            
            # List current directory
            list_tool = self.tools["list_directory"]
            dir_result = await list_tool.run()
            context.metadata["workspace_contents"] = dir_result
            
        except Exception as e:
            logger.warning(f"Failed to populate initial context: {e}")
    
    async def execute_tool(
        self, 
        session_id: str, 
        tool_name: str, 
        **kwargs
    ) -> ToolResult:
        """Execute a tool with shared context."""
        if session_id not in self.contexts:
            raise ValueError(f"No context found for session: {session_id}")
        
        context = self.contexts[session_id]
        tool = self.tools.get(tool_name)
        
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Pre-execution context injection
            enhanced_kwargs = await self._inject_context(tool_name, kwargs, context)
            
            # Execute tool
            output = await tool.run(**enhanced_kwargs)
            
            # Calculate execution time
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Create result
            result = ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                execution_time_ms=execution_time
            )
            
            # Post-execution context updates
            await self._update_context(context, tool_name, result, kwargs)
            
            # Suggest next tools
            result.suggested_next_tools = await self._suggest_next_tools(
                context, tool_name, result
            )
            
            # Update metrics
            self.metrics["executions"] += 1
            self.metrics["avg_time"] = (
                (self.metrics["avg_time"] * (self.metrics["executions"] - 1) + execution_time)
                / self.metrics["executions"]
            )
            
            return result
            
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["failures"] += 1
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=f"Error: {str(e)}",
                execution_time_ms=execution_time,
                confidence_score=0.0
            )
    
    async def _inject_context(
        self, 
        tool_name: str, 
        kwargs: Dict[str, Any], 
        context: ToolExecutionContext
    ) -> Dict[str, Any]:
        """Inject contextual information into tool parameters."""
        enhanced_kwargs = kwargs.copy()
        
        # Tool-specific context injection
        if tool_name == "code_search":
            # Enhance search with task context
            if "query" in kwargs:
                query = kwargs["query"]
                enhanced_kwargs["query"] = f"{query} {context.task_description}"
        
        elif tool_name in ["run_tests", "run_lint", "run_typecheck"]:
            # Focus on modified files if available
            if context.modified_files and "path" not in kwargs:
                enhanced_kwargs["path"] = " ".join(context.modified_files)
        
        elif tool_name == "git_commit":
            # Auto-generate commit message based on context
            if "message" not in kwargs and context.task_description:
                enhanced_kwargs["message"] = f"feat: {context.task_description[:50]}"
        
        return enhanced_kwargs
    
    async def _update_context(
        self,
        context: ToolExecutionContext,
        tool_name: str,
        result: ToolResult,
        original_kwargs: Dict[str, Any]
    ):
        """Update context based on tool execution results."""
        # Record execution in history
        context.execution_history.append({
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "success": result.success,
            "execution_time_ms": result.execution_time_ms
        })
        
        # Tool-specific context updates
        if tool_name == "git_status":
            context.git_status = {
                "output": result.output,
                "timestamp": datetime.now()
            }
            # Extract modified files
            if "modified:" in result.output:
                # Parse git status for modified files
                context.modified_files = self._extract_modified_files(result.output)
        
        elif tool_name == "write_file" and result.success:
            filepath = original_kwargs.get("filepath", "")
            if filepath and filepath not in context.modified_files:
                context.modified_files.append(filepath)
        
        elif tool_name == "run_tests":
            context.test_results = {
                "output": result.output,
                "success": result.success,
                "timestamp": datetime.now()
            }
        
        elif tool_name == "run_lint":
            context.lint_results = {
                "output": result.output,
                "success": result.success,
                "timestamp": datetime.now()
            }
    
    def _extract_modified_files(self, git_status_output: str) -> List[str]:
        """Extract modified file paths from git status output."""
        files = []
        lines = git_status_output.split('\n')
        for line in lines:
            if line.strip().startswith('M '):
                files.append(line.strip()[2:])
        return files
    
    async def _suggest_next_tools(
        self,
        context: ToolExecutionContext,
        executed_tool: str,
        result: ToolResult
    ) -> List[str]:
        """Suggest logical next tools based on execution history."""
        suggestions = []
        
        # Rule-based suggestions
        if executed_tool == "write_file" and result.success:
            suggestions.extend(["run_tests", "run_lint", "git_add"])
        
        elif executed_tool == "git_add" and result.success:
            suggestions.append("git_commit")
        
        elif executed_tool == "run_tests" and not result.success:
            suggestions.extend(["code_search", "read_file", "git_diff"])
        
        elif executed_tool == "code_search":
            suggestions.extend(["read_file", "write_file"])
        
        elif executed_tool == "git_status" and "modified:" in result.output:
            suggestions.extend(["git_diff", "run_tests", "run_lint"])
        
        return suggestions
    
    async def execute_workflow(
        self,
        session_id: str,
        workflow_name: str,
        **kwargs
    ) -> List[ToolResult]:
        """Execute a predefined workflow."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        results = []
        
        for step in workflow:
            tool_name = step["tool"]
            purpose = step["purpose"]
            
            logger.info(f"Executing {tool_name} for {purpose}")
            
            try:
                result = await self.execute_tool(session_id, tool_name, **kwargs)
                results.append(result)
                
                # Stop workflow on critical failure
                if not result.success and purpose in ["validate_implementation", "regression_check"]:
                    logger.warning(f"Workflow stopped due to critical failure in {tool_name}")
                    break
                    
            except Exception as e:
                logger.error(f"Workflow step failed: {tool_name} - {e}")
                break
        
        return results
    
    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the current execution context."""
        if session_id not in self.contexts:
            return {"error": "Context not found"}
        
        context = self.contexts[session_id]
        return {
            "session_id": context.session_id,
            "task": context.task_description,
            "modified_files": context.modified_files,
            "execution_count": len(context.execution_history),
            "last_tools": [h["tool"] for h in context.execution_history[-3:]],
            "test_status": "passed" if context.test_results and context.test_results["success"] else "unknown",
            "lint_status": "passed" if context.lint_results and context.lint_results["success"] else "unknown"
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool manager performance metrics."""
        return {
            **self.metrics,
            "active_contexts": len(self.contexts),
            "available_tools": len(self.tools),
            "workflows": list(self.workflows.keys())
        }

# Usage example
async def main():
    """Example usage of integrated tool manager."""
    manager = IntegratedToolManager()
    
    # Create context
    context = await manager.create_context(
        "session_1",
        "Implement user authentication feature"
    )
    
    # Execute tools with context
    search_result = await manager.execute_tool(
        "session_1",
        "code_search",
        query="authentication user login"
    )
    print(f"Search result: {search_result.success}")
    print(f"Suggested next: {search_result.suggested_next_tools}")
    
    # Execute workflow
    workflow_results = await manager.execute_workflow(
        "session_1",
        "code_implementation"
    )
    print(f"Workflow completed: {len(workflow_results)} steps")
    
    # Get context summary
    summary = await manager.get_context_summary("session_1")
    print(f"Context summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())