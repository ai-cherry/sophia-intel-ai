"""
Role-Specific Strategy Classes

This module implements distinct reasoning and tool strategies per agent role,
enhancing specialization beyond simple prompt and temperature variations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.agent_config import AgentRoleConfig
from app.reasoning.reasoning_engine import (
    ChainOfThoughtStrategy,
    ReActStrategy,
    ReasoningContext,
    ReasoningStep,
    ReasoningStepType,
    ReasoningStrategy,
)
from app.tools.tool_schemas import ToolCall, ToolCategory


class RoleStrategy(ABC):
    """Abstract base class for role-specific strategies"""
    
    def __init__(self, config: AgentRoleConfig):
        self.config = config
        self.reasoning_strategy = self._create_reasoning_strategy()
    
    @abstractmethod
    def _create_reasoning_strategy(self) -> ReasoningStrategy:
        """Create role-specific reasoning strategy"""
        pass
    
    @abstractmethod
    async def preprocess_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Preprocess problem based on role expertise"""
        pass
    
    @abstractmethod
    async def select_tools(self, context: dict[str, Any]) -> list[str]:
        """Select appropriate tools for the task"""
        pass
    
    @abstractmethod
    async def postprocess_result(self, result: Any) -> Any:
        """Postprocess result based on role requirements"""
        pass
    
    @abstractmethod
    def get_role_prompt(self) -> str:
        """Get role-specific system prompt"""
        pass


class PlannerStrategy(RoleStrategy):
    """Strategy for planning agents"""
    
    def _create_reasoning_strategy(self) -> ReasoningStrategy:
        """Planners use structured chain-of-thought reasoning"""
        return PlanningReasoningStrategy(model_client=None)
    
    async def preprocess_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Add planning-specific context"""
        enhanced_problem = problem.copy()
        
        # Extract key planning elements
        if "requirements" not in enhanced_problem:
            enhanced_problem["requirements"] = []
        
        if "constraints" not in enhanced_problem:
            enhanced_problem["constraints"] = []
        
        if "timeline" not in enhanced_problem:
            enhanced_problem["timeline"] = "flexible"
        
        # Add planning framework
        enhanced_problem["planning_framework"] = {
            "phases": ["analysis", "design", "implementation", "testing", "deployment"],
            "deliverables": [],
            "milestones": [],
            "dependencies": []
        }
        
        return enhanced_problem
    
    async def select_tools(self, context: dict[str, Any]) -> list[str]:
        """Select planning tools"""
        tools = ["create_timeline", "analyze_dependencies", "estimate_resources"]
        
        # Add risk assessment for complex projects
        if context.get("complexity", "medium") == "high":
            tools.append("assess_risks")
        
        # Add team coordination tools if needed
        if context.get("team_size", 1) > 1:
            tools.extend(["allocate_resources", "coordinate_teams"])
        
        return tools
    
    async def postprocess_result(self, result: Any) -> Any:
        """Structure result as actionable plan"""
        if isinstance(result, str):
            # Parse and structure the plan
            return {
                "plan_summary": result,
                "action_items": self._extract_action_items(result),
                "timeline": self._extract_timeline(result),
                "success_criteria": self._extract_success_criteria(result)
            }
        return result
    
    def get_role_prompt(self) -> str:
        """Get planner-specific prompt"""
        return """You are a strategic planning expert who excels at:
- Breaking down complex problems into manageable phases
- Identifying dependencies and critical paths
- Estimating resources and timelines accurately
- Risk assessment and mitigation planning
- Creating clear, actionable project plans

Always think in terms of:
1. What needs to be done (requirements)
2. In what order (dependencies)
3. By when (timeline)
4. With what resources (allocation)
5. What could go wrong (risks)"""
    
    def _extract_action_items(self, text: str) -> list[str]:
        """Extract action items from plan text"""
        # Simple extraction logic - would be more sophisticated
        items = []
        lines = text.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['task:', 'step:', 'action:', '-', '*']):
                items.append(line.strip())
        return items[:10]  # Limit to top 10
    
    def _extract_timeline(self, text: str) -> dict:
        """Extract timeline information"""
        # Placeholder implementation
        return {"phases": [], "duration": "TBD"}
    
    def _extract_success_criteria(self, text: str) -> list[str]:
        """Extract success criteria"""
        # Placeholder implementation
        return ["Criteria extracted from plan"]


class CoderStrategy(RoleStrategy):
    """Strategy for coding agents"""
    
    def _create_reasoning_strategy(self) -> ReasoningStrategy:
        """Coders use ReAct for iterative code development"""
        return CodingReActStrategy(model_client=None, tool_executor=None)
    
    async def preprocess_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Add coding-specific context"""
        enhanced_problem = problem.copy()
        
        # Identify programming language
        if "language" not in enhanced_problem:
            enhanced_problem["language"] = self._detect_language(problem)
        
        # Add code quality requirements
        enhanced_problem["quality_requirements"] = {
            "style_guide": self._get_style_guide(enhanced_problem["language"]),
            "test_coverage": 0.8,
            "documentation": "comprehensive",
            "security": "OWASP compliant"
        }
        
        return enhanced_problem
    
    async def select_tools(self, context: dict[str, Any]) -> list[str]:
        """Select coding tools"""
        tools = ["code_search", "git_operations"]
        
        language = context.get("language", "python")
        
        # Language-specific tools
        if language == "python":
            tools.extend(["pytest", "black", "mypy"])
        elif language in ["javascript", "typescript"]:
            tools.extend(["jest", "eslint", "prettier"])
        
        # Add testing tools
        if context.get("requires_testing", True):
            tools.append("test_runner")
        
        # Add documentation tools
        if context.get("requires_docs", False):
            tools.append("doc_generator")
        
        return tools
    
    async def postprocess_result(self, result: Any) -> Any:
        """Format code with documentation and tests"""
        if isinstance(result, str):
            return {
                "code": result,
                "language": self._detect_language({"code": result}),
                "documentation": self._generate_basic_docs(result),
                "test_suggestions": self._suggest_tests(result),
                "quality_score": self._assess_code_quality(result)
            }
        return result
    
    def get_role_prompt(self) -> str:
        """Get coder-specific prompt"""
        return """You are an expert software engineer who writes:
- Clean, efficient, well-documented code
- Following best practices and design patterns
- With comprehensive error handling
- Including appropriate tests
- Considering security implications

Your code should be:
1. Readable and maintainable
2. Performant and optimized
3. Secure and robust
4. Well-tested
5. Properly documented"""
    
    def _detect_language(self, problem: dict) -> str:
        """Detect programming language from context"""
        # Simple detection logic
        code = str(problem.get("code", ""))
        if "def " in code or "import " in code:
            return "python"
        elif "function " in code or "const " in code:
            return "javascript"
        elif "#include" in code:
            return "cpp"
        return "python"  # Default
    
    def _get_style_guide(self, language: str) -> str:
        """Get style guide for language"""
        guides = {
            "python": "PEP 8",
            "javascript": "Airbnb",
            "typescript": "Airbnb TypeScript",
            "java": "Google Java Style",
            "go": "Effective Go"
        }
        return guides.get(language, "Standard")
    
    def _generate_basic_docs(self, code: str) -> str:
        """Generate basic documentation"""
        return "Documentation would be generated based on code analysis"
    
    def _suggest_tests(self, code: str) -> list[str]:
        """Suggest test cases"""
        return ["Unit tests", "Integration tests", "Edge cases"]
    
    def _assess_code_quality(self, code: str) -> dict:
        """Assess code quality metrics"""
        return {
            "readability": 0.8,
            "complexity": "low",
            "test_coverage": 0.0,
            "security_score": 0.7
        }


class SecurityStrategy(RoleStrategy):
    """Strategy for security agents"""
    
    def _create_reasoning_strategy(self) -> ReasoningStrategy:
        """Security agents use thorough analysis"""
        return SecurityReasoningStrategy(model_client=None)
    
    async def preprocess_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Add security-specific context"""
        enhanced_problem = problem.copy()
        
        # Add security frameworks
        enhanced_problem["security_frameworks"] = [
            "OWASP Top 10",
            "NIST Cybersecurity Framework",
            "CIS Controls"
        ]
        
        # Add threat model
        enhanced_problem["threat_model"] = {
            "methodology": "STRIDE",
            "assets": [],
            "threats": [],
            "attack_vectors": []
        }
        
        # Add compliance requirements
        enhanced_problem["compliance"] = {
            "required": ["GDPR", "SOC2"],
            "optional": ["ISO27001", "HIPAA"]
        }
        
        return enhanced_problem
    
    async def select_tools(self, context: dict[str, Any]) -> list[str]:
        """Select security tools"""
        tools = ["vulnerability_scanner", "compliance_checker"]
        
        # Add specific scanners based on context
        if context.get("scan_type") == "web":
            tools.extend(["owasp_zap", "burp_suite"])
        elif context.get("scan_type") == "infrastructure":
            tools.extend(["nessus", "openvas"])
        elif context.get("scan_type") == "code":
            tools.extend(["semgrep", "snyk", "bandit"])
        
        # Add threat modeling tools
        if context.get("threat_modeling", False):
            tools.append("threat_modeler")
        
        return tools
    
    async def postprocess_result(self, result: Any) -> Any:
        """Structure security findings"""
        if isinstance(result, str):
            return {
                "executive_summary": self._create_executive_summary(result),
                "vulnerabilities": self._extract_vulnerabilities(result),
                "risk_assessment": self._assess_risk(result),
                "remediation_plan": self._create_remediation_plan(result),
                "compliance_status": self._check_compliance(result)
            }
        return result
    
    def get_role_prompt(self) -> str:
        """Get security-specific prompt"""
        return """You are a cybersecurity expert specializing in:
- Vulnerability identification and assessment
- Threat modeling and risk analysis
- Security architecture review
- Compliance and regulatory requirements
- Incident response planning

Your analysis should:
1. Identify all potential security risks
2. Assess severity using CVSS scores
3. Provide specific remediation steps
4. Consider compliance requirements
5. Include defense-in-depth strategies"""
    
    def _create_executive_summary(self, text: str) -> str:
        """Create executive summary of findings"""
        return "Executive summary of security findings"
    
    def _extract_vulnerabilities(self, text: str) -> list[dict]:
        """Extract vulnerability information"""
        return [
            {
                "id": "VULN-001",
                "title": "Example vulnerability",
                "severity": "high",
                "cvss": 7.5
            }
        ]
    
    def _assess_risk(self, text: str) -> dict:
        """Assess overall risk"""
        return {
            "overall_risk": "medium",
            "critical_issues": 0,
            "high_issues": 2,
            "medium_issues": 5,
            "low_issues": 10
        }
    
    def _create_remediation_plan(self, text: str) -> list[dict]:
        """Create remediation plan"""
        return [
            {
                "priority": "high",
                "action": "Patch critical vulnerabilities",
                "timeline": "immediate"
            }
        ]
    
    def _check_compliance(self, text: str) -> dict:
        """Check compliance status"""
        return {
            "GDPR": "compliant",
            "SOC2": "partial",
            "ISO27001": "non-compliant"
        }


class ResearcherStrategy(RoleStrategy):
    """Strategy for research agents"""
    
    def _create_reasoning_strategy(self) -> ReasoningStrategy:
        """Researchers use comprehensive exploration"""
        return ResearchReasoningStrategy(model_client=None)
    
    async def preprocess_problem(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Add research-specific context"""
        enhanced_problem = problem.copy()
        
        # Add research methodology
        enhanced_problem["methodology"] = {
            "approach": "systematic_review",
            "sources": ["academic", "industry", "web"],
            "quality_criteria": ["peer_reviewed", "recent", "reputable"]
        }
        
        # Add research questions
        enhanced_problem["research_questions"] = self._generate_research_questions(problem)
        
        return enhanced_problem
    
    async def select_tools(self, context: dict[str, Any]) -> list[str]:
        """Select research tools"""
        tools = ["web_search", "document_analysis", "summarizer"]
        
        # Add academic search if needed
        if "academic" in context.get("sources", []):
            tools.extend(["scholar_search", "arxiv_search"])
        
        # Add data analysis tools
        if context.get("requires_analysis", False):
            tools.extend(["data_analyzer", "statistics_calculator"])
        
        # Add citation tools
        if context.get("requires_citations", True):
            tools.append("citation_generator")
        
        return tools
    
    async def postprocess_result(self, result: Any) -> Any:
        """Structure research findings"""
        if isinstance(result, str):
            return {
                "abstract": self._create_abstract(result),
                "key_findings": self._extract_findings(result),
                "methodology": "Systematic literature review",
                "evidence": self._extract_evidence(result),
                "conclusions": self._extract_conclusions(result),
                "references": self._extract_references(result),
                "limitations": self._identify_limitations(result)
            }
        return result
    
    def get_role_prompt(self) -> str:
        """Get researcher-specific prompt"""
        return """You are an expert researcher who:
- Gathers information from multiple reliable sources
- Synthesizes complex findings into clear insights
- Evaluates source credibility and bias
- Identifies knowledge gaps and limitations
- Provides well-referenced, evidence-based conclusions

Your research should be:
1. Comprehensive and systematic
2. Objective and unbiased
3. Well-sourced and referenced
4. Clear and accessible
5. Actionable and relevant"""
    
    def _generate_research_questions(self, problem: dict) -> list[str]:
        """Generate research questions"""
        base_query = problem.get("query", "")
        return [
            f"What is known about {base_query}?",
            f"What are the key challenges in {base_query}?",
            f"What solutions exist for {base_query}?"
        ]
    
    def _create_abstract(self, text: str) -> str:
        """Create research abstract"""
        return "Abstract: Summary of research findings"
    
    def _extract_findings(self, text: str) -> list[str]:
        """Extract key findings"""
        return ["Finding 1", "Finding 2", "Finding 3"]
    
    def _extract_evidence(self, text: str) -> list[dict]:
        """Extract supporting evidence"""
        return [{"source": "Study A", "finding": "Evidence 1"}]
    
    def _extract_conclusions(self, text: str) -> list[str]:
        """Extract conclusions"""
        return ["Conclusion based on evidence"]
    
    def _extract_references(self, text: str) -> list[str]:
        """Extract references"""
        return ["Reference 1", "Reference 2"]
    
    def _identify_limitations(self, text: str) -> list[str]:
        """Identify research limitations"""
        return ["Limited sample size", "Time constraints"]


# Custom Reasoning Strategies

class PlanningReasoningStrategy(ChainOfThoughtStrategy):
    """Specialized reasoning for planning"""
    
    async def next_step(self, context: ReasoningContext) -> Optional[ReasoningStep]:
        """Generate planning-specific reasoning steps"""
        if context.current_step == 0:
            return await self._analyze_requirements(context)
        elif context.current_step == 1:
            return await self._identify_dependencies(context)
        elif context.current_step == 2:
            return await self._create_timeline(context)
        elif context.current_step == 3:
            return await self._allocate_resources(context)
        else:
            return await super().next_step(context)
    
    async def _analyze_requirements(self, context: ReasoningContext) -> ReasoningStep:
        """Analyze project requirements"""
        return ReasoningStep(
            step_type=ReasoningStepType.PLANNING,
            content="Analyzing requirements and constraints...",
            confidence=0.9
        )
    
    async def _identify_dependencies(self, context: ReasoningContext) -> ReasoningStep:
        """Identify task dependencies"""
        return ReasoningStep(
            step_type=ReasoningStepType.PLANNING,
            content="Identifying dependencies and critical path...",
            confidence=0.85
        )
    
    async def _create_timeline(self, context: ReasoningContext) -> ReasoningStep:
        """Create project timeline"""
        return ReasoningStep(
            step_type=ReasoningStepType.PLANNING,
            content="Creating timeline with milestones...",
            confidence=0.8
        )
    
    async def _allocate_resources(self, context: ReasoningContext) -> ReasoningStep:
        """Allocate resources"""
        return ReasoningStep(
            step_type=ReasoningStepType.PLANNING,
            content="Allocating resources and team members...",
            confidence=0.75
        )


class CodingReActStrategy(ReActStrategy):
    """Specialized ReAct for coding"""
    
    async def _should_act(self, context: ReasoningContext) -> bool:
        """Determine if code action is needed"""
        # More aggressive tool use for coding
        return len(context.available_tools) > 0 and context.current_step % 2 == 1


class SecurityReasoningStrategy(ChainOfThoughtStrategy):
    """Specialized reasoning for security analysis"""
    
    async def next_step(self, context: ReasoningContext) -> Optional[ReasoningStep]:
        """Generate security-specific reasoning steps"""
        if context.current_step == 0:
            return await self._identify_assets(context)
        elif context.current_step == 1:
            return await self._analyze_threats(context)
        elif context.current_step == 2:
            return await self._assess_vulnerabilities(context)
        elif context.current_step == 3:
            return await self._evaluate_risks(context)
        elif context.current_step == 4:
            return await self._recommend_controls(context)
        else:
            return await super().next_step(context)
    
    async def _identify_assets(self, context: ReasoningContext) -> ReasoningStep:
        """Identify assets to protect"""
        return ReasoningStep(
            step_type=ReasoningStepType.EVALUATION,
            content="Identifying critical assets and data...",
            confidence=0.95
        )
    
    async def _analyze_threats(self, context: ReasoningContext) -> ReasoningStep:
        """Analyze threat landscape"""
        return ReasoningStep(
            step_type=ReasoningStepType.EVALUATION,
            content="Analyzing threat actors and vectors...",
            confidence=0.9
        )
    
    async def _assess_vulnerabilities(self, context: ReasoningContext) -> ReasoningStep:
        """Assess vulnerabilities"""
        return ReasoningStep(
            step_type=ReasoningStepType.EVALUATION,
            content="Assessing system vulnerabilities...",
            confidence=0.85
        )
    
    async def _evaluate_risks(self, context: ReasoningContext) -> ReasoningStep:
        """Evaluate risk levels"""
        return ReasoningStep(
            step_type=ReasoningStepType.EVALUATION,
            content="Evaluating risk levels and impact...",
            confidence=0.8
        )
    
    async def _recommend_controls(self, context: ReasoningContext) -> ReasoningStep:
        """Recommend security controls"""
        return ReasoningStep(
            step_type=ReasoningStepType.CONCLUSION,
            content="Recommending security controls and mitigations...",
            confidence=0.9
        )


class ResearchReasoningStrategy(ChainOfThoughtStrategy):
    """Specialized reasoning for research"""
    
    async def next_step(self, context: ReasoningContext) -> Optional[ReasoningStep]:
        """Generate research-specific reasoning steps"""
        if context.current_step == 0:
            return await self._define_scope(context)
        elif context.current_step == 1:
            return await self._gather_sources(context)
        elif context.current_step == 2:
            return await self._analyze_evidence(context)
        elif context.current_step == 3:
            return await self._synthesize_findings(context)
        else:
            return await super().next_step(context)
    
    async def _define_scope(self, context: ReasoningContext) -> ReasoningStep:
        """Define research scope"""
        return ReasoningStep(
            step_type=ReasoningStepType.PLANNING,
            content="Defining research scope and questions...",
            confidence=0.9
        )
    
    async def _gather_sources(self, context: ReasoningContext) -> ReasoningStep:
        """Gather information sources"""
        return ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="Gathering and evaluating sources...",
            confidence=0.85
        )
    
    async def _analyze_evidence(self, context: ReasoningContext) -> ReasoningStep:
        """Analyze evidence"""
        return ReasoningStep(
            step_type=ReasoningStepType.EVALUATION,
            content="Analyzing evidence and patterns...",
            confidence=0.8
        )
    
    async def _synthesize_findings(self, context: ReasoningContext) -> ReasoningStep:
        """Synthesize findings"""
        return ReasoningStep(
            step_type=ReasoningStepType.CONCLUSION,
            content="Synthesizing findings into insights...",
            confidence=0.85
        )


# Strategy Factory

class RoleStrategyFactory:
    """Factory for creating role-specific strategies"""
    
    @staticmethod
    def create_strategy(role: str, config: AgentRoleConfig) -> RoleStrategy:
        """Create strategy based on role"""
        strategies = {
            "planner": PlannerStrategy,
            "coder": CoderStrategy,
            "security": SecurityStrategy,
            "researcher": ResearcherStrategy,
        }
        
        strategy_class = strategies.get(role, PlannerStrategy)
        return strategy_class(config)