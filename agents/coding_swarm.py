"""
LangGraph Coding Swarm Architecture
4-agent collaborative coding system: Planner → Coder → Reviewer → Integrator
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel

from mcp_servers.code_mcp.tools.github_tools import GitHubTools
from mcp_servers.code_mcp.tools.repo_diff import RepoDiffAnalyzer


class CodingTaskType(Enum):
    """Types of coding tasks"""

    FEATURE_IMPLEMENTATION = "feature_implementation"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    CODE_REVIEW = "code_review"


class CodingSwarmState(TypedDict):
    """State for the coding swarm workflow"""

    task_description: str
    task_type: CodingTaskType
    repository: str
    target_files: List[str]
    requirements: List[str]

    # Planning phase
    plan: Optional[Dict[str, Any]]
    planning_complete: bool

    # Coding phase
    code_changes: Optional[Dict[str, Any]]
    coding_complete: bool

    # Review phase
    review_results: Optional[Dict[str, Any]]
    review_complete: bool

    # Integration phase
    integration_results: Optional[Dict[str, Any]]
    integration_complete: bool

    # Workflow state
    current_agent: str
    messages: List[BaseMessage]
    errors: List[str]
    metadata: Dict[str, Any]


class CodingAgent(BaseModel):
    """Base class for coding agents"""

    name: str
    role: str
    system_prompt: str
    llm: Optional[ChatOpenAI] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        if not self.llm:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
            )

    async def process(self, state: CodingSwarmState) -> Dict[str, Any]:
        """Process the current state and return updates"""
        raise NotImplementedError("Subclasses must implement process method")


class PlannerAgent(CodingAgent):
    """Agent responsible for planning coding tasks"""

    def __init__(self):
        super().__init__(
            name="Planner",
            role="Task Planning and Architecture",
            system_prompt="""You are a senior software architect responsible for planning coding tasks.

Your responsibilities:
1. Analyze the task description and requirements
2. Break down complex tasks into manageable steps
3. Identify files that need to be modified or created
4. Define the implementation strategy
5. Estimate complexity and potential risks
6. Create a detailed execution plan

Always provide structured, actionable plans with clear steps and dependencies.""",
        )

    async def process(self, state: CodingSwarmState) -> Dict[str, Any]:
        """Create a detailed plan for the coding task"""
        try:
            logger.info(f"Planner processing task: {state['task_description']}")

            # Prepare planning prompt
            planning_prompt = f"""
Task: {state['task_description']}
Type: {state['task_type'].value}
Repository: {state['repository']}
Target Files: {', '.join(state['target_files']) if state['target_files'] else 'To be determined'}
Requirements: {', '.join(state['requirements']) if state['requirements'] else 'None specified'}

Please create a detailed implementation plan including:
1. Task breakdown into specific steps
2. Files to be modified/created
3. Implementation strategy
4. Dependencies and prerequisites
5. Risk assessment
6. Testing approach
7. Estimated complexity (1-10 scale)

Provide your response in JSON format with the following structure:
{{
    "steps": [
        {{"step": 1, "description": "...", "files": ["..."], "complexity": 1-10}}
    ],
    "files_to_modify": ["file1.py", "file2.py"],
    "files_to_create": ["new_file.py"],
    "implementation_strategy": "...",
    "dependencies": ["..."],
    "risks": ["..."],
    "testing_approach": "...",
    "estimated_complexity": 1-10,
    "estimated_time": "...",
    "success_criteria": ["..."]
}}
"""

            # Get planning response
            messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=planning_prompt)]

            response = await self.llm.ainvoke(messages)

            # Parse the plan
            try:
                plan = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to basic plan if JSON parsing fails
                plan = {
                    "steps": [{"step": 1, "description": state["task_description"], "complexity": 5}],
                    "files_to_modify": state["target_files"],
                    "implementation_strategy": "Standard implementation approach",
                    "estimated_complexity": 5,
                    "success_criteria": ["Task completed successfully"],
                }

            return {
                "plan": plan,
                "planning_complete": True,
                "current_agent": "Coder",
                "messages": state["messages"] + [response],
            }

        except Exception as e:
            logger.error(f"Planner error: {e}")
            return {
                "errors": state["errors"] + [f"Planning error: {e}"],
                "current_agent": "Coder",  # Continue to next agent even if planning fails
            }


class CoderAgent(CodingAgent):
    """Agent responsible for implementing code changes"""

    github_tools: Optional[GitHubTools] = None
    diff_analyzer: Optional[RepoDiffAnalyzer] = None

    def __init__(self, github_tools: GitHubTools, diff_analyzer: RepoDiffAnalyzer):
        super().__init__(
            name="Coder",
            role="Code Implementation",
            system_prompt="""You are an expert software developer responsible for implementing code changes.

Your responsibilities:
1. Implement the planned changes with high quality code
2. Follow best practices and coding standards
3. Write clean, maintainable, and well-documented code
4. Handle edge cases and error conditions
5. Ensure code is compatible with existing codebase
6. Generate appropriate tests when needed

Always write production-ready code with proper error handling and documentation.""",
            github_tools=github_tools,
            diff_analyzer=diff_analyzer,
        )

    async def process(self, state: CodingSwarmState) -> Dict[str, Any]:
        """Implement the planned code changes"""
        try:
            logger.info(f"Coder implementing changes for: {state['task_description']}")

            plan = state.get("plan", {})
            files_to_modify = plan.get("files_to_modify", state.get("target_files", []))

            code_changes = {
                "modified_files": {},
                "created_files": {},
                "implementation_notes": [],
                "complexity_analysis": {},
            }

            # Read existing files
            for file_path in files_to_modify:
                try:
                    file_data = await self.github_tools.read_file_content(state["repository"], file_path)
                    original_content = file_data["content"]

                    # Generate implementation prompt
                    implementation_prompt = f"""
Task: {state['task_description']}
Plan: {json.dumps(plan, indent=2)}
File: {file_path}
Current Content:
```
{original_content}
```

Please implement the required changes to this file. Provide:
1. The complete modified file content
2. Explanation of changes made
3. Any important implementation notes

Respond in JSON format:
{{
    "modified_content": "...",
    "changes_explanation": "...",
    "implementation_notes": ["..."]
}}
"""

                    messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=implementation_prompt)]

                    response = await self.llm.ainvoke(messages)

                    try:
                        implementation = json.loads(response.content)
                        modified_content = implementation.get("modified_content", original_content)

                        # Analyze the changes
                        analysis = await self.diff_analyzer.analyze_file_changes(
                            state["repository"], file_path, original_content, modified_content
                        )

                        code_changes["modified_files"][file_path] = {
                            "original_content": original_content,
                            "modified_content": modified_content,
                            "changes_explanation": implementation.get("changes_explanation", ""),
                            "analysis": analysis,
                        }

                        code_changes["implementation_notes"].extend(implementation.get("implementation_notes", []))

                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse implementation response for {file_path}")
                        code_changes["implementation_notes"].append(
                            f"Warning: Could not parse implementation for {file_path}"
                        )

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    code_changes["implementation_notes"].append(f"Error processing {file_path}: {e}")

            return {"code_changes": code_changes, "coding_complete": True, "current_agent": "Reviewer"}

        except Exception as e:
            logger.error(f"Coder error: {e}")
            return {"errors": state["errors"] + [f"Coding error: {e}"], "current_agent": "Reviewer"}


class ReviewerAgent(CodingAgent):
    """Agent responsible for code review and quality assurance"""

    diff_analyzer: Optional[RepoDiffAnalyzer] = None

    def __init__(self, diff_analyzer: RepoDiffAnalyzer):
        super().__init__(
            name="Reviewer",
            role="Code Review and Quality Assurance",
            system_prompt="""You are a senior code reviewer responsible for ensuring code quality and correctness.

Your responsibilities:
1. Review code changes for correctness and quality
2. Check for potential bugs and security issues
3. Verify adherence to coding standards
4. Assess performance implications
5. Validate test coverage
6. Provide constructive feedback and suggestions

Always provide thorough, constructive reviews with specific recommendations.""",
            diff_analyzer=diff_analyzer,
        )

    async def process(self, state: CodingSwarmState) -> Dict[str, Any]:
        """Review the implemented code changes"""
        try:
            logger.info(f"Reviewer analyzing changes for: {state['task_description']}")

            code_changes = state.get("code_changes", {})
            modified_files = code_changes.get("modified_files", {})

            review_results = {
                "overall_quality": "unknown",
                "file_reviews": {},
                "issues_found": [],
                "recommendations": [],
                "approval_status": "pending",
                "review_summary": "",
            }

            total_issues = 0
            total_files = len(modified_files)

            for file_path, file_changes in modified_files.items():
                try:
                    original_content = file_changes["original_content"]
                    modified_content = file_changes["modified_content"]
                    analysis = file_changes.get("analysis", {})

                    # Validate syntax
                    from pathlib import Path

                    file_extension = Path(file_path).suffix
                    syntax_validation = await self.diff_analyzer.validate_code_syntax(modified_content, file_extension)

                    # Generate review prompt
                    review_prompt = f"""
Please review the following code changes:

File: {file_path}
Task: {state['task_description']}

Original Content:
```
{original_content[:2000]}...
```

Modified Content:
```
{modified_content[:2000]}...
```

Diff Analysis:
{json.dumps(analysis.get("complexity", {}), indent=2)}

Please provide a comprehensive review including:
1. Code quality assessment (1-10 scale)
2. Potential issues or bugs
3. Security considerations
4. Performance implications
5. Adherence to best practices
6. Specific recommendations

Respond in JSON format:
{{
    "quality_score": 1-10,
    "issues": [
        {{"type": "bug|security|performance|style", "severity": "low|medium|high", "description": "...", "line": 0}}
    ],
    "recommendations": ["..."],
    "approval": "approved|needs_changes|rejected",
    "summary": "..."
}}
"""

                    messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=review_prompt)]

                    response = await self.llm.ainvoke(messages)

                    try:
                        file_review = json.loads(response.content)

                        review_results["file_reviews"][file_path] = {
                            "quality_score": file_review.get("quality_score", 5),
                            "issues": file_review.get("issues", []),
                            "recommendations": file_review.get("recommendations", []),
                            "approval": file_review.get("approval", "needs_changes"),
                            "summary": file_review.get("summary", ""),
                            "syntax_validation": syntax_validation,
                        }

                        # Count issues
                        file_issues = len(file_review.get("issues", []))
                        total_issues += file_issues

                        # Add to overall recommendations
                        review_results["recommendations"].extend(file_review.get("recommendations", []))

                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse review response for {file_path}")
                        review_results["file_reviews"][file_path] = {
                            "quality_score": 5,
                            "approval": "needs_changes",
                            "summary": "Review parsing failed",
                        }
                        total_issues += 1

                except Exception as e:
                    logger.error(f"Error reviewing file {file_path}: {e}")
                    review_results["issues_found"].append(f"Review error for {file_path}: {e}")
                    total_issues += 1

            # Determine overall quality and approval
            if total_files > 0:
                avg_quality = (
                    sum(review["quality_score"] for review in review_results["file_reviews"].values()) / total_files
                )

                if avg_quality >= 8 and total_issues == 0:
                    review_results["overall_quality"] = "excellent"
                    review_results["approval_status"] = "approved"
                elif avg_quality >= 6 and total_issues <= 2:
                    review_results["overall_quality"] = "good"
                    review_results["approval_status"] = "approved_with_minor_changes"
                elif avg_quality >= 4:
                    review_results["overall_quality"] = "fair"
                    review_results["approval_status"] = "needs_changes"
                else:
                    review_results["overall_quality"] = "poor"
                    review_results["approval_status"] = "rejected"

            review_results["review_summary"] = (
                f"Reviewed {total_files} files. Overall quality: {review_results['overall_quality']}. Issues found: {total_issues}."
            )

            return {"review_results": review_results, "review_complete": True, "current_agent": "Integrator"}

        except Exception as e:
            logger.error(f"Reviewer error: {e}")
            return {"errors": state["errors"] + [f"Review error: {e}"], "current_agent": "Integrator"}


class IntegratorAgent(CodingAgent):
    """Agent responsible for integrating changes and creating PRs"""

    github_tools: Optional[GitHubTools] = None
    diff_analyzer: Optional[RepoDiffAnalyzer] = None

    def __init__(self, github_tools: GitHubTools, diff_analyzer: RepoDiffAnalyzer):
        super().__init__(
            name="Integrator",
            role="Integration and Deployment",
            system_prompt="""You are responsible for integrating code changes and managing deployments.

Your responsibilities:
1. Create branches and commit changes
2. Generate comprehensive commit messages
3. Create pull requests with detailed descriptions
4. Coordinate with CI/CD systems
5. Handle merge conflicts and integration issues
6. Ensure proper documentation and change logs

Always ensure smooth integration with minimal disruption to the main codebase.""",
            github_tools=github_tools,
            diff_analyzer=diff_analyzer,
        )

    async def process(self, state: CodingSwarmState) -> Dict[str, Any]:
        """Integrate the reviewed changes"""
        try:
            logger.info(f"Integrator processing changes for: {state['task_description']}")

            code_changes = state.get("code_changes", {})
            review_results = state.get("review_results", {})

            # Check if changes are approved
            approval_status = review_results.get("approval_status", "rejected")
            if approval_status == "rejected":
                return {
                    "integration_results": {
                        "status": "rejected",
                        "reason": "Code review rejected the changes",
                        "action_required": "Address review feedback and resubmit",
                    },
                    "integration_complete": True,
                    "errors": state["errors"] + ["Integration halted due to code review rejection"],
                }

            integration_results = {
                "status": "in_progress",
                "branch_created": False,
                "files_committed": [],
                "pr_created": False,
                "pr_url": None,
                "commit_messages": [],
                "integration_summary": "",
            }

            try:
                # Create a new branch
                timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                task_slug = state["task_description"].lower().replace(" ", "-")[:30]
                branch_name = f"feature/{task_slug}-{timestamp}"

                _branch_result = await self.github_tools.create_branch(state["repository"], branch_name)
                integration_results["branch_created"] = True
                integration_results["branch_name"] = branch_name

                # Commit changes
                modified_files = code_changes.get("modified_files", {})
                changes_for_commit = []

                for file_path, file_data in modified_files.items():
                    try:
                        # Generate commit message for this file
                        commit_message = await self.diff_analyzer.generate_commit_message(
                            [{"file_path": file_path, "analysis": file_data.get("analysis", {})}]
                        )

                        # Commit the file
                        _commit_result = await self.github_tools.commit_file_change(
                            repository=state["repository"],
                            file_path=file_path,
                            content=file_data["modified_content"],
                            commit_message=commit_message,
                            branch=branch_name,
                        )

                        integration_results["files_committed"].append(file_path)
                        integration_results["commit_messages"].append(commit_message)
                        changes_for_commit.append(file_data)

                    except Exception as e:
                        logger.error(f"Error committing {file_path}: {e}")
                        integration_results["errors"] = integration_results.get("errors", [])
                        integration_results["errors"].append(f"Commit error for {file_path}: {e}")

                # Create pull request
                if integration_results["files_committed"]:
                    pr_title = f"feat: {state['task_description']}"

                    pr_description = f"""## Task Description
{state['task_description']}

## Changes Made
{len(integration_results['files_committed'])} files modified:
{chr(10).join(f'- {fp}' for fp in integration_results['files_committed'])}

## Implementation Notes
{chr(10).join(f'- {note}' for note in code_changes.get('implementation_notes', []))}

## Code Review Summary
{review_results.get('review_summary', 'No review summary available')}

## Quality Assessment
- Overall Quality: {review_results.get('overall_quality', 'Unknown')}
- Approval Status: {review_results.get('approval_status', 'Unknown')}

## Files Changed
{chr(10).join(f'### {fp}' + chr(10) + file_data.get('changes_explanation', 'No explanation provided') for fp, file_data in modified_files.items())}

---
*Generated by Sophia Intel Coding Swarm*
"""

                    pr_result = await self.github_tools.create_pull_request(
                        repository=state["repository"],
                        title=pr_title,
                        description=pr_description,
                        head_branch=branch_name,
                    )

                    integration_results["pr_created"] = True
                    integration_results["pr_url"] = pr_result["pr_url"]
                    integration_results["pr_number"] = pr_result["pr_number"]

                integration_results["status"] = "completed"
                integration_results["integration_summary"] = (
                    f"Successfully integrated {len(integration_results['files_committed'])} files into branch {branch_name} and created PR #{integration_results.get('pr_number', 'N/A')}"
                )

            except Exception as e:
                logger.error(f"Integration error: {e}")
                integration_results["status"] = "failed"
                integration_results["error"] = str(e)

            return {"integration_results": integration_results, "integration_complete": True}

        except Exception as e:
            logger.error(f"Integrator error: {e}")
            return {"errors": state["errors"] + [f"Integration error: {e}"], "integration_complete": True}


class CodingSwarm:
    """LangGraph-based coding swarm orchestrator"""

    def __init__(self):
        self.github_tools = GitHubTools()
        self.diff_analyzer = RepoDiffAnalyzer(self.github_tools)

        # Initialize agents
        self.planner = PlannerAgent()
        self.coder = CoderAgent(self.github_tools, self.diff_analyzer)
        self.reviewer = ReviewerAgent(self.diff_analyzer)
        self.integrator = IntegratorAgent(self.github_tools, self.diff_analyzer)

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(CodingSwarmState)

        # Add nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("coder", self._coder_node)
        workflow.add_node("reviewer", self._reviewer_node)
        workflow.add_node("integrator", self._integrator_node)

        # Define the flow
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "coder")
        workflow.add_edge("coder", "reviewer")
        workflow.add_edge("reviewer", "integrator")
        workflow.add_edge("integrator", END)

        return workflow.compile()

    async def _planner_node(self, state: CodingSwarmState) -> CodingSwarmState:
        """Planner node execution"""
        updates = await self.planner.process(state)
        return {**state, **updates}

    async def _coder_node(self, state: CodingSwarmState) -> CodingSwarmState:
        """Coder node execution"""
        updates = await self.coder.process(state)
        return {**state, **updates}

    async def _reviewer_node(self, state: CodingSwarmState) -> CodingSwarmState:
        """Reviewer node execution"""
        updates = await self.reviewer.process(state)
        return {**state, **updates}

    async def _integrator_node(self, state: CodingSwarmState) -> CodingSwarmState:
        """Integrator node execution"""
        updates = await self.integrator.process(state)
        return {**state, **updates}

    async def execute_coding_task(
        self,
        task_description: str,
        repository: str,
        task_type: CodingTaskType = CodingTaskType.FEATURE_IMPLEMENTATION,
        target_files: List[str] = None,
        requirements: List[str] = None,
    ) -> Dict[str, Any]:
        """Execute a coding task using the swarm"""

        # Initialize state
        initial_state = CodingSwarmState(
            task_description=task_description,
            task_type=task_type,
            repository=repository,
            target_files=target_files or [],
            requirements=requirements or [],
            plan=None,
            planning_complete=False,
            code_changes=None,
            coding_complete=False,
            review_results=None,
            review_complete=False,
            integration_results=None,
            integration_complete=False,
            current_agent="Planner",
            messages=[],
            errors=[],
            metadata={"start_time": datetime.utcnow().isoformat(), "swarm_version": "1.0.0"},
        )

        try:
            # Execute the workflow
            logger.info(f"Starting coding swarm for task: {task_description}")

            final_state = await self.workflow.ainvoke(initial_state)

            # Add completion metadata
            final_state["metadata"]["end_time"] = datetime.utcnow().isoformat()
            final_state["metadata"]["success"] = len(final_state.get("errors", [])) == 0

            return final_state

        except Exception as e:
            logger.error(f"Coding swarm execution error: {e}")
            return {
                **initial_state,
                "errors": [f"Workflow execution error: {e}"],
                "metadata": {**initial_state["metadata"], "end_time": datetime.utcnow().isoformat(), "success": False},
            }


# Factory function for easy instantiation
def create_coding_swarm() -> CodingSwarm:
    """Create and configure a coding swarm instance"""
    return CodingSwarm()
