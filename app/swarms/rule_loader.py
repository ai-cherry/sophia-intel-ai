"""
AI Rules Loader for Swarm Agents
Loads and enforces rules from the .ai directory structure
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RuleLoader:
    """Loads and manages AI agent rules for swarm coordination"""
    
    def __init__(self, rules_dir: str = ".ai"):
        self.rules_dir = Path(rules_dir)
        self.master_rules = self._load_master_rules()
        self.agent_rules = self._load_agent_rules()
        self.workflows = self._load_workflows()
        self._validation_cache: Dict[str, bool] = {}
    
    def _load_master_rules(self) -> Dict[str, Any]:
        """Load the master rules configuration"""
        master_path = self.rules_dir / "MASTER_RULES.yaml"
        if not master_path.exists():
            logger.warning(f"Master rules not found at {master_path}")
            return {}
        
        try:
            with open(master_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load master rules: {e}")
            return {}
    
    def _load_agent_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load all agent-specific rules"""
        agent_rules = {}
        agents_dir = self.rules_dir / "agents"
        
        if not agents_dir.exists():
            logger.warning(f"Agents directory not found at {agents_dir}")
            return {}
        
        # Load MDC files
        for mdc_file in agents_dir.rglob("*.mdc"):
            try:
                agent_name, rules = self._parse_mdc_file(mdc_file)
                if agent_name:
                    agent_rules[agent_name] = rules
                    logger.info(f"Loaded rules for agent: {agent_name}")
            except Exception as e:
                logger.error(f"Failed to load {mdc_file}: {e}")
        
        return agent_rules
    
    def _parse_mdc_file(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Parse an MDC (Markdown with metadata) file"""
        content = file_path.read_text()
        
        # Extract frontmatter
        if not content.startswith("---"):
            raise ValueError(f"MDC file {file_path} missing frontmatter")
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid MDC format in {file_path}")
        
        # Parse metadata
        metadata = yaml.safe_load(parts[1])
        agent_name = metadata.get("agent")
        
        # Add the content as well
        metadata["content"] = parts[2].strip()
        
        return agent_name, metadata
    
    def _load_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load workflow definitions"""
        workflows = {}
        workflows_dir = self.rules_dir / "workflows"
        
        if not workflows_dir.exists():
            logger.warning(f"Workflows directory not found at {workflows_dir}")
            return {}
        
        for yaml_file in workflows_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    workflow = yaml.safe_load(f)
                    workflow_name = workflow.get("workflow", yaml_file.stem)
                    workflows[workflow_name] = workflow
                    logger.info(f"Loaded workflow: {workflow_name}")
            except Exception as e:
                logger.error(f"Failed to load workflow {yaml_file}: {e}")
        
        return workflows
    
    def get_agent_rules(self, agent_name: str) -> Dict[str, Any]:
        """Get rules for a specific agent"""
        # Check direct agent rules
        if agent_name in self.agent_rules:
            return self.agent_rules[agent_name]
        
        # Check swarm agents
        if agent_name.startswith("swarm:"):
            return self.agent_rules.get(agent_name, {})
        
        # Check master rules for agent definition
        agents = self.master_rules.get("agents", {})
        if agent_name in agents:
            return agents[agent_name]
        
        # Check swarm agents in master rules
        swarm_agents = agents.get("swarm_agents", {})
        swarm_type = agent_name.replace("swarm:", "")
        if swarm_type in swarm_agents:
            return swarm_agents[swarm_type]
        
        logger.warning(f"No rules found for agent: {agent_name}")
        return {}
    
    def get_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Get a specific workflow definition"""
        return self.workflows.get(workflow_name, {})
    
    def validate_output(self, output: str, agent_name: str) -> Tuple[bool, List[str]]:
        """
        Validate agent output against rules
        Returns (is_valid, list_of_violations)
        """
        violations = []
        
        # Get enforcement rules
        enforcement = self.master_rules.get("enforcement", {})
        
        # Check forbidden phrases
        forbidden_phrases = enforcement.get("truth_verification", {}).get("forbidden_phrases", [])
        for phrase in forbidden_phrases:
            if phrase.lower() in output.lower():
                violations.append(f"Forbidden phrase detected: '{phrase}'")
        
        # Check for mock patterns
        prohibited_patterns = enforcement.get("anti_mock_policy", {}).get("prohibited_patterns", [])
        for pattern in prohibited_patterns:
            regex = pattern.replace("*", ".*")
            if re.search(regex, output, re.IGNORECASE):
                violations.append(f"Prohibited pattern detected: '{pattern}'")
        
        # Agent-specific validation
        agent_rules = self.get_agent_rules(agent_name)
        if "forbidden_actions" in agent_rules:
            for action in agent_rules["forbidden_actions"]:
                if action.lower() in output.lower():
                    violations.append(f"Agent {agent_name} performed forbidden action: '{action}'")
        
        return len(violations) == 0, violations
    
    def enforce_tech_stack(self, dependency: str) -> bool:
        """Check if a dependency is approved"""
        approved = self.master_rules.get("tech_stack", {}).get("approved", {})
        
        # Check each category
        for category, items in approved.items():
            if isinstance(items, list):
                for item in items:
                    # Simple check - can be made more sophisticated
                    if dependency.lower() in item.lower() or item.lower() in dependency.lower():
                        return True
        
        return False
    
    def get_quality_gates(self) -> Dict[str, Any]:
        """Get quality gate requirements"""
        return self.master_rules.get("quality_gates", {})
    
    def get_agent_priority(self, agent_name: str) -> int:
        """Get priority for an agent (higher = more important)"""
        rules = self.get_agent_rules(agent_name)
        return rules.get("priority", 50)
    
    def get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get capabilities for an agent"""
        rules = self.get_agent_rules(agent_name)
        return rules.get("capabilities", [])
    
    def match_agent_to_task(self, task: str) -> Optional[str]:
        """Find the best agent for a given task"""
        best_agent = None
        best_score = 0
        
        for agent_name, rules in self.agent_rules.items():
            capabilities = rules.get("capabilities", [])
            task_scope = rules.get("task_scope", [])
            
            # Simple scoring: count matching keywords
            score = 0
            task_lower = task.lower()
            
            for capability in capabilities:
                if capability.lower() in task_lower:
                    score += 2
            
            for scope_item in task_scope:
                if scope_item.lower() in task_lower:
                    score += 1
            
            # Add priority as a tie-breaker
            score += rules.get("priority", 0) / 100
            
            if score > best_score:
                best_score = score
                best_agent = agent_name
        
        return best_agent
    
    def get_orchestration_config(self) -> Dict[str, Any]:
        """Get orchestration configuration"""
        return self.master_rules.get("orchestration", {})
    
    def should_rollback(self, error: Exception, agent_name: str) -> bool:
        """Determine if we should rollback on error"""
        orchestration = self.get_orchestration_config()
        error_handling = orchestration.get("error_handling", {})
        
        # Check if rollback is enabled
        if error_handling.get("on_failure") != "rollback":
            return False
        
        # Check agent-specific rules
        agent_rules = self.get_agent_rules(agent_name)
        if "no_rollback" in agent_rules:
            return False
        
        return True
    
    def get_communication_channel(self, channel_type: str) -> str:
        """Get communication channel configuration"""
        orchestration = self.get_orchestration_config()
        channels = orchestration.get("communication_channels", {})
        return channels.get(channel_type, "")
    
    def validate_workflow_stage(self, workflow_name: str, stage_name: str, outputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate outputs from a workflow stage"""
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return False, [f"Workflow {workflow_name} not found"]
        
        stages = workflow.get("stages", {})
        stage = stages.get(stage_name, {})
        
        if not stage:
            return False, [f"Stage {stage_name} not found in workflow"]
        
        violations = []
        validation = stage.get("validation", {})
        
        for key, expected in validation.items():
            if key not in outputs:
                violations.append(f"Missing required output: {key}")
            elif isinstance(expected, bool):
                if bool(outputs[key]) != expected:
                    violations.append(f"Validation failed for {key}: expected {expected}")
            elif isinstance(expected, str):
                if expected.startswith(">"):
                    # Numeric comparison
                    try:
                        threshold = float(expected[1:])
                        if float(outputs[key]) <= threshold:
                            violations.append(f"Value {key}={outputs[key]} not > {threshold}")
                    except (ValueError, TypeError):
                        violations.append(f"Cannot compare {key} numerically")
        
        return len(violations) == 0, violations
    
    def get_cleanup_commands(self) -> List[str]:
        """Get cleanup commands from rules"""
        zero_debris = self.master_rules.get("enforcement", {}).get("zero_debris", {})
        
        commands = []
        if pre_task := zero_debris.get("pre_task_cleanup"):
            commands.extend(pre_task.split("\n"))
        if post_task := zero_debris.get("post_task_cleanup"):
            commands.extend(post_task.split("\n"))
        
        return [cmd.strip() for cmd in commands if cmd.strip()]


class RuleEnforcer:
    """Enforces rules during swarm execution"""
    
    def __init__(self, rule_loader: RuleLoader):
        self.rule_loader = rule_loader
        self.violations: List[str] = []
    
    def pre_execution_check(self, agent_name: str, task: str) -> bool:
        """Check if an agent can execute a task"""
        # Check if agent exists
        rules = self.rule_loader.get_agent_rules(agent_name)
        if not rules:
            self.violations.append(f"Agent {agent_name} has no rules defined")
            return False
        
        # Check capabilities
        capabilities = rules.get("capabilities", [])
        task_scope = rules.get("task_scope", [])
        
        # Simple check - task should match capabilities or scope
        task_lower = task.lower()
        matched = False
        
        for capability in capabilities + task_scope:
            if capability.lower() in task_lower or task_lower in capability.lower():
                matched = True
                break
        
        if not matched:
            self.violations.append(f"Agent {agent_name} not capable of task: {task}")
            return False
        
        return True
    
    def post_execution_check(self, agent_name: str, output: str) -> bool:
        """Validate agent output"""
        is_valid, violations = self.rule_loader.validate_output(output, agent_name)
        
        if not is_valid:
            self.violations.extend(violations)
        
        return is_valid
    
    def enforce_quality_gates(self, metrics: Dict[str, Any]) -> bool:
        """Check if quality gates are met"""
        gates = self.rule_loader.get_quality_gates()
        
        for category, requirements in gates.items():
            if isinstance(requirements, dict):
                for metric, threshold in requirements.items():
                    if metric in metrics:
                        # Simple comparison
                        if isinstance(threshold, (int, float)):
                            if metrics[metric] < threshold:
                                self.violations.append(f"Quality gate failed: {metric}={metrics[metric]} < {threshold}")
                                return False
        
        return True
    
    def get_violations(self) -> List[str]:
        """Get list of all violations"""
        return self.violations
    
    def clear_violations(self):
        """Clear violations list"""
        self.violations = []