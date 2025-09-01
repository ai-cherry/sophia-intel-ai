"""
QuickNLP - Simple Natural Language Processing for System Commands
Uses pattern matching and prompt engineering with Ollama backend
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

import requests

logger = logging.getLogger(__name__)


class CommandIntent(Enum):
    """Supported command intents"""
    SYSTEM_STATUS = "system_status"
    RUN_AGENT = "run_agent"
    SCALE_SERVICE = "scale_service"
    EXECUTE_WORKFLOW = "execute_workflow"
    QUERY_DATA = "query_data"
    STOP_SERVICE = "stop_service"
    LIST_AGENTS = "list_agents"
    GET_METRICS = "get_metrics"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Structured representation of a parsed command"""
    intent: CommandIntent
    entities: Dict[str, Any]
    raw_text: str
    confidence: float
    workflow_trigger: Optional[str] = None


class QuickNLP:
    """
    Simple Natural Language Processor using pattern matching
    and Ollama for intent extraction when patterns don't match
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.patterns = self._initialize_patterns()
        self.entity_extractors = self._initialize_extractors()
        
    def _initialize_patterns(self) -> Dict[CommandIntent, List[re.Pattern]]:
        """Initialize regex patterns for intent detection"""
        return {
            CommandIntent.SYSTEM_STATUS: [
                re.compile(r"(show|get|display|check).*system.*status", re.IGNORECASE),
                re.compile(r"system\s+status", re.IGNORECASE),
                re.compile(r"status\s+of\s+(system|services?)", re.IGNORECASE),
                re.compile(r"how.*system.*doing", re.IGNORECASE),
            ],
            CommandIntent.RUN_AGENT: [
                re.compile(r"(run|start|execute|launch)\s+agent\s+(\w+)", re.IGNORECASE),
                re.compile(r"agent\s+(\w+)\s+(run|start|execute)", re.IGNORECASE),
                re.compile(r"activate\s+(\w+)\s+agent", re.IGNORECASE),
            ],
            CommandIntent.SCALE_SERVICE: [
                re.compile(r"scale\s+(service\s+)?(\w+)\s+to\s+(\d+)", re.IGNORECASE),
                re.compile(r"(increase|decrease)\s+(\w+)\s+(instances?|replicas?)", re.IGNORECASE),
                re.compile(r"set\s+(\w+)\s+(instances?|replicas?)\s+to\s+(\d+)", re.IGNORECASE),
            ],
            CommandIntent.EXECUTE_WORKFLOW: [
                re.compile(r"(run|execute|trigger)\s+workflow\s+(\w+)", re.IGNORECASE),
                re.compile(r"workflow\s+(\w+)\s+(run|execute|trigger)", re.IGNORECASE),
                re.compile(r"start\s+(\w+)\s+workflow", re.IGNORECASE),
            ],
            CommandIntent.QUERY_DATA: [
                re.compile(r"(query|search|find|get)\s+.*data", re.IGNORECASE),
                re.compile(r"search\s+for\s+(.*)", re.IGNORECASE),
                re.compile(r"find\s+(documents?|records?|items?)", re.IGNORECASE),
            ],
            CommandIntent.STOP_SERVICE: [
                re.compile(r"(stop|halt|shutdown)\s+(service\s+)?(\w+)", re.IGNORECASE),
                re.compile(r"(service\s+)?(\w+)\s+(stop|halt|shutdown)", re.IGNORECASE),
            ],
            CommandIntent.LIST_AGENTS: [
                re.compile(r"(list|show|display)\s+(all\s+)?agents?", re.IGNORECASE),
                re.compile(r"what\s+agents?\s+(are\s+)?(available|running)", re.IGNORECASE),
            ],
            CommandIntent.GET_METRICS: [
                re.compile(r"(show|get|display)\s+metrics?", re.IGNORECASE),
                re.compile(r"metrics?\s+for\s+(\w+)", re.IGNORECASE),
                re.compile(r"performance\s+(metrics?|stats?)", re.IGNORECASE),
            ],
            CommandIntent.HELP: [
                re.compile(r"^help$", re.IGNORECASE),
                re.compile(r"what\s+can\s+you\s+do", re.IGNORECASE),
                re.compile(r"show\s+commands?", re.IGNORECASE),
            ],
        }
    
    def _initialize_extractors(self) -> Dict[CommandIntent, callable]:
        """Initialize entity extraction functions for each intent"""
        return {
            CommandIntent.RUN_AGENT: self._extract_agent_name,
            CommandIntent.SCALE_SERVICE: self._extract_scale_params,
            CommandIntent.EXECUTE_WORKFLOW: self._extract_workflow_name,
            CommandIntent.STOP_SERVICE: self._extract_service_name,
            CommandIntent.QUERY_DATA: self._extract_query_params,
            CommandIntent.GET_METRICS: self._extract_metric_target,
        }
    
    def process(self, text: str) -> ParsedCommand:
        """
        Process natural language text into structured command
        """
        # First try pattern matching
        intent, entities, confidence = self._match_patterns(text)
        
        # If no pattern matched, use Ollama for intent extraction
        if intent == CommandIntent.UNKNOWN:
            intent, entities, confidence = self._extract_with_ollama(text)
        
        # Determine workflow trigger based on intent
        workflow_trigger = self._get_workflow_trigger(intent)
        
        return ParsedCommand(
            intent=intent,
            entities=entities,
            raw_text=text,
            confidence=confidence,
            workflow_trigger=workflow_trigger
        )
    
    def _match_patterns(self, text: str) -> Tuple[CommandIntent, Dict[str, Any], float]:
        """
        Match text against predefined patterns
        """
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Extract entities if extractor exists
                    entities = {}
                    if intent in self.entity_extractors:
                        entities = self.entity_extractors[intent](text, match)
                    return intent, entities, 0.9
        
        return CommandIntent.UNKNOWN, {}, 0.0
    
    def _extract_agent_name(self, text: str, match: re.Match) -> Dict[str, Any]:
        """Extract agent name from text"""
        groups = match.groups()
        agent_name = None
        
        for group in groups:
            if group and group.lower() not in ['run', 'start', 'execute', 'launch', 'agent']:
                agent_name = group
                break
        
        return {"agent_name": agent_name or "default"}
    
    def _extract_scale_params(self, text: str, match: re.Match) -> Dict[str, Any]:
        """Extract scaling parameters"""
        # Look for service name and count
        service_match = re.search(r"scale\s+(?:service\s+)?(\w+)", text, re.IGNORECASE)
        count_match = re.search(r"to\s+(\d+)", text, re.IGNORECASE)
        
        service = service_match.group(1) if service_match else "unknown"
        count = int(count_match.group(1)) if count_match else 1
        
        return {"service": service, "replicas": count}
    
    def _extract_workflow_name(self, text: str, match: re.Match) -> Dict[str, Any]:
        """Extract workflow name"""
        groups = match.groups()
        workflow_name = None
        
        for group in groups:
            if group and group.lower() not in ['run', 'execute', 'trigger', 'workflow', 'start']:
                workflow_name = group
                break
        
        return {"workflow_name": workflow_name or "default"}
    
    def _extract_service_name(self, text: str, match: re.Match) -> Dict[str, Any]:
        """Extract service name"""
        groups = match.groups()
        service_name = None
        
        for group in groups:
            if group and group.lower() not in ['stop', 'halt', 'shutdown', 'service']:
                service_name = group
                break
        
        return {"service_name": service_name or "unknown"}
    
    def _extract_query_params(self, text: str, match: re.Match) -> Dict[str, Any]:
        """Extract query parameters"""
        # Simple extraction of query terms
        query_terms = re.sub(r"(query|search|find|get|for|data)", "", text, flags=re.IGNORECASE)
        query_terms = query_terms.strip()
        
        return {"query": query_terms}
    
    def _extract_metric_target(self, text: str, match: re.Match) -> Dict[str, Any]:
        """Extract metric target"""
        target_match = re.search(r"for\s+(\w+)", text, re.IGNORECASE)
        target = target_match.group(1) if target_match else "all"
        
        return {"target": target}
    
    def _extract_with_ollama(self, text: str) -> Tuple[CommandIntent, Dict[str, Any], float]:
        """
        Use Ollama to extract intent when patterns don't match
        """
        try:
            prompt = f"""
            Analyze this command and extract the intent and entities.
            Command: "{text}"
            
            Respond with JSON only:
            {{
                "intent": "one of: system_status, run_agent, scale_service, execute_workflow, query_data, stop_service, list_agents, get_metrics, help, unknown",
                "entities": {{}}
            }}
            """
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                parsed = json.loads(result.get("response", "{}"))
                
                intent_str = parsed.get("intent", "unknown")
                intent = CommandIntent[intent_str.upper()] if intent_str.upper() in CommandIntent.__members__ else CommandIntent.UNKNOWN
                entities = parsed.get("entities", {})
                
                return intent, entities, 0.7
                
        except Exception as e:
            logger.error(f"Ollama extraction failed: {e}")
        
        return CommandIntent.UNKNOWN, {}, 0.0
    
    def _get_workflow_trigger(self, intent: CommandIntent) -> Optional[str]:
        """
        Map intent to n8n workflow trigger
        """
        workflow_map = {
            CommandIntent.SYSTEM_STATUS: "system-status-workflow",
            CommandIntent.RUN_AGENT: "agent-execution-workflow",
            CommandIntent.SCALE_SERVICE: "service-scaling-workflow",
            CommandIntent.EXECUTE_WORKFLOW: "custom-workflow",
            CommandIntent.QUERY_DATA: "data-query-workflow",
            CommandIntent.STOP_SERVICE: "service-control-workflow",
            CommandIntent.LIST_AGENTS: "agent-listing-workflow",
            CommandIntent.GET_METRICS: "metrics-collection-workflow",
        }
        
        return workflow_map.get(intent)
    
    def get_available_commands(self) -> List[Dict[str, str]]:
        """
        Get list of available commands with examples
        """
        return [
            {
                "intent": "system_status",
                "description": "Check system status",
                "examples": ["show system status", "how is the system doing"]
            },
            {
                "intent": "run_agent",
                "description": "Run a specific agent",
                "examples": ["run agent researcher", "start coding agent"]
            },
            {
                "intent": "scale_service",
                "description": "Scale a service",
                "examples": ["scale ollama to 3", "increase redis instances"]
            },
            {
                "intent": "execute_workflow",
                "description": "Execute a workflow",
                "examples": ["run workflow data-pipeline", "execute backup workflow"]
            },
            {
                "intent": "query_data",
                "description": "Query data",
                "examples": ["search for user documents", "find recent logs"]
            },
            {
                "intent": "stop_service",
                "description": "Stop a service",
                "examples": ["stop redis", "shutdown ollama service"]
            },
            {
                "intent": "list_agents",
                "description": "List available agents",
                "examples": ["list all agents", "show available agents"]
            },
            {
                "intent": "get_metrics",
                "description": "Get performance metrics",
                "examples": ["show metrics", "get metrics for ollama"]
            },
            {
                "intent": "help",
                "description": "Show help",
                "examples": ["help", "what can you do"]
            }
        ]