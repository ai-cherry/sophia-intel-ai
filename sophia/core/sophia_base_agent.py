"""
SOPHIA V4 Base Agent
Extends the existing BaseAgent to add model router and API manager capabilities.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

# Import existing BaseAgent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.base_agent import BaseAgent, Status
from .ultimate_model_router import UltimateModelRouter, TaskType
from .api_manager import SOPHIAAPIManager
from .github_master import SOPHIAGitHubMaster, GitHubRepoInfo
from .fly_master import SOPHIAFlyMaster

logger = logging.getLogger(__name__)

class SOPHIABaseAgent(BaseAgent):
    """
    Extends the existing BaseAgent to add a model router and API manager.
    Provides unified access to AI models and external services.
    """

    def __init__(self, name: str, concurrency: int = 2, timeout_seconds: int = 300, **kwargs):
        """
        Initialize SOPHIA base agent with enhanced capabilities.
        
        Args:
            name: Agent name/identifier
            concurrency: Maximum concurrent tasks
            timeout_seconds: Task timeout in seconds
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(name, concurrency, timeout_seconds)
        
        # Initialize core SOPHIA components
        logger.info(f"Initializing SOPHIA agent: {name}")
        
        try:
            self.model_router = UltimateModelRouter()
            logger.info("Model router initialized")
        except Exception as e:
            logger.error(f"Failed to initialize model router: {e}")
            self.model_router = None
        
        try:
            self.api_manager = SOPHIAAPIManager()
            logger.info("API manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize API manager: {e}")
            self.api_manager = None
        
        # Initialize GitHub master
        try:
            repo_info = GitHubRepoInfo(owner="ai-cherry", repo="sophia-intel")
            self.github_master = SOPHIAGitHubMaster(repo_info)
            logger.info("GitHub master initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub master: {e}")
            self.github_master = None
        
        # Initialize Fly master
        try:
            self.fly_master = SOPHIAFlyMaster()
            logger.info("Fly master initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Fly master: {e}")
            self.fly_master = None
        
        # Track SOPHIA-specific metrics
        self.model_calls = 0
        self.api_calls = 0
        self.successful_model_calls = 0
        self.successful_api_calls = 0

    async def route_task(self, task_type: str, prompt: str, **kwargs) -> str:
        """
        Use the model router to select and call the best model for a task.
        
        Args:
            task_type: Type of task (code_generation, research, etc.)
            prompt: The prompt to send to the model
            **kwargs: Additional parameters (temperature, max_tokens, system_prompt, etc.)
            
        Returns:
            The model's response as a string
            
        Raises:
            RuntimeError: If model router is not available or call fails
        """
        if not self.model_router:
            raise RuntimeError("Model router not initialized")
        
        self.model_calls += 1
        
        try:
            # Select the best model for the task
            model_config = self.model_router.select_model(task_type)
            logger.info(f"Selected {model_config.provider}:{model_config.model_name} for {task_type}")
            
            # Call the model
            response = await self.model_router.call_model(model_config, prompt, **kwargs)
            
            self.successful_model_calls += 1
            logger.info(f"Model call successful for {task_type}")
            
            return response
            
        except Exception as e:
            logger.error(f"Model routing failed for {task_type}: {e}")
            raise RuntimeError(f"Model routing failed: {e}")

    async def call_service(self, service_name: str, method: str, **kwargs) -> Any:
        """
        Call a method on a configured service through the API manager.
        
        Args:
            service_name: Name of the service (e.g., 'postgres', 'qdrant', 'github')
            method: Method to call on the service
            **kwargs: Arguments to pass to the method
            
        Returns:
            Result from the service call
            
        Raises:
            RuntimeError: If API manager is not available or call fails
        """
        if not self.api_manager:
            raise RuntimeError("API manager not initialized")
        
        self.api_calls += 1
        
        try:
            # Route to appropriate service method
            if service_name == "postgres" and method == "query":
                result = await self.api_manager.query_postgres(kwargs.get("sql"), *kwargs.get("params", []))
            elif service_name == "qdrant" and method == "upsert":
                result = self.api_manager.upsert_qdrant(
                    kwargs.get("collection"),
                    kwargs.get("vectors"),
                    kwargs.get("payloads")
                )
            elif service_name == "redis" and method == "get":
                result = self.api_manager.get_redis(kwargs.get("key"))
            elif service_name == "redis" and method == "set":
                result = self.api_manager.set_redis(
                    kwargs.get("key"),
                    kwargs.get("value"),
                    kwargs.get("ex")
                )
            else:
                raise NotImplementedError(f"Service method {service_name}.{method} not implemented")
            
            self.successful_api_calls += 1
            logger.info(f"Service call successful: {service_name}.{method}")
            
            return result
            
        except Exception as e:
            logger.error(f"Service call failed {service_name}.{method}: {e}")
            raise RuntimeError(f"Service call failed: {e}")

    async def generate_code(self, prompt: str, language: str = "python", **kwargs) -> str:
        """
        Generate code using the best available coding model.
        
        Args:
            prompt: Description of what code to generate
            language: Programming language (default: python)
            **kwargs: Additional parameters
            
        Returns:
            Generated code as a string
        """
        system_prompt = kwargs.get("system_prompt", f"""You are an expert {language} developer. 
Generate clean, production-ready code following best practices.

Guidelines:
- Write clear, readable code with proper comments
- Follow {language} best practices and conventions
- Include error handling where appropriate
- Add docstrings/comments explaining the code
- Ensure code is secure and efficient
- Return only the code, no explanations unless requested""")
        
        return await self.route_task(
            TaskType.CODE_GENERATION.value,
            prompt,
            system_prompt=system_prompt,
            **kwargs
        )

    async def research_topic(self, topic: str, depth: str = "comprehensive", **kwargs) -> str:
        """
        Research a topic using the best available research model.
        
        Args:
            topic: Topic to research
            depth: Research depth (basic, comprehensive, deep)
            **kwargs: Additional parameters
            
        Returns:
            Research results as a string
        """
        system_prompt = kwargs.get("system_prompt", f"""You are an expert researcher. 
Conduct {depth} research on the given topic.

Guidelines:
- Provide accurate, well-sourced information
- Structure your response clearly
- Include key insights and analysis
- Cite sources when possible
- Be thorough but concise""")
        
        return await self.route_task(
            TaskType.RESEARCH.value,
            f"Research topic: {topic}",
            system_prompt=system_prompt,
            **kwargs
        )

    async def analyze_data(self, data_description: str, analysis_type: str = "general", **kwargs) -> str:
        """
        Analyze data using the best available analysis model.
        
        Args:
            data_description: Description of the data to analyze
            analysis_type: Type of analysis to perform
            **kwargs: Additional parameters
            
        Returns:
            Analysis results as a string
        """
        system_prompt = kwargs.get("system_prompt", f"""You are an expert data analyst.
Perform {analysis_type} analysis on the described data.

Guidelines:
- Provide clear, actionable insights
- Use appropriate analytical methods
- Explain your reasoning
- Highlight key findings
- Suggest next steps if relevant""")
        
        return await self.route_task(
            TaskType.ANALYSIS.value,
            f"Analyze: {data_description}",
            system_prompt=system_prompt,
            **kwargs
        )

    def get_sophia_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status including SOPHIA-specific metrics.
        
        Returns:
            Dictionary with agent status and metrics
        """
        base_status = {
            "name": self.name,
            "status": self.status.value,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_timeout": self.tasks_timeout,
            "total_duration": self.total_duration
        }
        
        sophia_status = {
            "model_calls": self.model_calls,
            "api_calls": self.api_calls,
            "successful_model_calls": self.successful_model_calls,
            "successful_api_calls": self.successful_api_calls,
            "model_success_rate": self.successful_model_calls / max(self.model_calls, 1),
            "api_success_rate": self.successful_api_calls / max(self.api_calls, 1)
        }
        
        # Add service status if API manager is available
        if self.api_manager:
            sophia_status["configured_services"] = self.api_manager.get_configured_services()
            sophia_status["service_status"] = self.api_manager.get_service_status()
        
        # Add model router status if available
        if self.model_router:
            sophia_status["available_models"] = {
                task_type.value: len(self.model_router.get_available_models(task_type.value))
                for task_type in TaskType
            }
        
        return {**base_status, "sophia": sophia_status}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all SOPHIA components.
        
        Returns:
            Health status of all components
        """
        health = {
            "agent": "healthy" if self.status == Status.READY else "unhealthy",
            "model_router": "healthy" if self.model_router else "unavailable",
            "api_manager": "healthy" if self.api_manager else "unavailable",
            "github_master": "healthy" if self.github_master else "unavailable",
            "fly_master": "healthy" if self.fly_master else "unavailable"
        }
        
        # Check API manager services
        if self.api_manager:
            try:
                service_health = await self.api_manager.health_check()
                health["services"] = service_health
            except Exception as e:
                health["services"] = f"health_check_failed: {e}"
        
        # Check Fly.io health
        if self.fly_master:
            try:
                fly_health = self.fly_master.health_check()
                health["fly_status"] = fly_health
            except Exception as e:
                health["fly_status"] = f"fly_health_check_failed: {e}"
        
        return health

    # GitHub Operations
    async def create_and_commit(self, branch_name: str, files: Dict[str, str], commit_message: str, create_pr: bool = False, pr_title: str = "", pr_body: str = "") -> Dict[str, Any]:
        """
        High-level method to create a branch, commit files, and optionally create a PR.
        
        Args:
            branch_name: Name of the new branch
            files: Dictionary of file paths to content
            commit_message: Commit message
            create_pr: Whether to create a pull request
            pr_title: PR title (if creating PR)
            pr_body: PR description (if creating PR)
            
        Returns:
            Dictionary with operation results
            
        Raises:
            RuntimeError: If GitHub master is not available or operation fails
        """
        if not self.github_master:
            raise RuntimeError("GitHub master not initialized")
        
        try:
            # Create branch
            branch_sha = self.github_master.create_branch(branch_name)
            logger.info(f"Created branch {branch_name}")
            
            # Commit and push files
            commit_sha = self.github_master.commit_and_push(branch_name, files, commit_message)
            logger.info(f"Committed changes to {branch_name}")
            
            result = {
                "branch_name": branch_name,
                "branch_sha": branch_sha,
                "commit_sha": commit_sha,
                "files_committed": len(files)
            }
            
            # Create PR if requested
            if create_pr:
                pr_info = self.github_master.create_pull_request(branch_name, pr_title or commit_message, pr_body)
                result["pr_info"] = {
                    "number": pr_info.number,
                    "url": pr_info.html_url,
                    "title": pr_info.title
                }
                logger.info(f"Created PR #{pr_info.number}")
            
            return result
            
        except Exception as e:
            logger.error(f"GitHub operation failed: {e}")
            raise RuntimeError(f"GitHub operation failed: {e}")

    async def deploy_to_fly(self, app_name: str, image: str, wait: bool = True) -> Dict[str, Any]:
        """
        High-level method to deploy an application to Fly.io.
        
        Args:
            app_name: Name of the Fly.io application
            image: Docker image to deploy
            wait: Whether to wait for deployment completion
            
        Returns:
            Dictionary with deployment results
            
        Raises:
            RuntimeError: If Fly master is not available or deployment fails
        """
        if not self.fly_master:
            raise RuntimeError("Fly master not initialized")
        
        try:
            # Deploy the application
            release_info = self.fly_master.deploy_app(app_name, image, wait)
            
            # Get app status after deployment
            app_status = self.fly_master.get_app_status(app_name)
            
            result = {
                "app_name": app_name,
                "image": image,
                "release": {
                    "id": release_info.id,
                    "version": release_info.version,
                    "status": release_info.status
                },
                "app_status": app_status["status"],
                "healthy_machines": app_status["healthy_machines"],
                "total_machines": app_status["machine_count"]
            }
            
            logger.info(f"Deployed {image} to {app_name} as v{release_info.version}")
            return result
            
        except Exception as e:
            logger.error(f"Fly deployment failed: {e}")
            raise RuntimeError(f"Fly deployment failed: {e}")

    async def autonomous_code_deploy(self, code_changes: Dict[str, str], app_name: str, image: str, branch_name: Optional[str] = None, commit_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Autonomous end-to-end code deployment: commit to GitHub and deploy to Fly.io.
        
        Args:
            code_changes: Dictionary of file paths to new content
            app_name: Fly.io application name
            image: Docker image to deploy
            branch_name: Git branch name (auto-generated if None)
            commit_message: Commit message (auto-generated if None)
            
        Returns:
            Dictionary with complete deployment results
            
        Raises:
            RuntimeError: If any step fails
        """
        import time
        
        # Auto-generate branch name and commit message if not provided
        if branch_name is None:
            timestamp = int(time.time())
            branch_name = f"sophia-auto-deploy-{timestamp}"
        
        if commit_message is None:
            commit_message = f"🤖 SOPHIA autonomous deployment - {len(code_changes)} files updated"
        
        try:
            # Step 1: Commit code changes to GitHub
            github_result = await self.create_and_commit(
                branch_name=branch_name,
                files=code_changes,
                commit_message=commit_message,
                create_pr=True,
                pr_title=f"SOPHIA Auto-Deploy: {app_name}",
                pr_body=f"Autonomous deployment by SOPHIA AI\n\nFiles updated: {', '.join(code_changes.keys())}\nTarget app: {app_name}\nImage: {image}"
            )
            
            # Step 2: Deploy to Fly.io
            fly_result = await self.deploy_to_fly(app_name, image, wait=True)
            
            # Combine results
            result = {
                "deployment_type": "autonomous",
                "timestamp": time.time(),
                "github": github_result,
                "fly": fly_result,
                "success": True
            }
            
            logger.info(f"Autonomous deployment completed: {branch_name} -> {app_name}")
            return result
            
        except Exception as e:
            logger.error(f"Autonomous deployment failed: {e}")
            raise RuntimeError(f"Autonomous deployment failed: {e}")

    async def initialize_mcp(self):
        """
        Initialize MCP (Model Context Protocol) integration.
        This is a placeholder for future MCP server integration.
        """
        # TODO: Implement MCP server integration
        logger.info("MCP initialization placeholder - to be implemented")
        pass

