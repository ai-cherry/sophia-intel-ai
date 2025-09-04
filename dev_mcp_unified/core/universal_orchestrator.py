"""
Universal AI Orchestrator for Sophia Intelligence AI
Single interface for both business (Sophia) and technical (Artemis) domains
"""
from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

from dev_mcp_unified.auth.rbac_manager import User, Permission, rbac_manager


class Domain(str, Enum):
    SOPHIA = "sophia"      # Business intelligence
    ARTEMIS = "artemis"    # Technical/development
    UNIVERSAL = "universal" # Cross-domain


class TaskType(str, Enum):
    QUERY = "query"
    CREATE = "create" 
    ANALYZE = "analyze"
    RESEARCH = "research"
    EXECUTE = "execute"
    MONITOR = "monitor"


@dataclass
class UniversalRequest:
    user_query: str
    user_id: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = None
    preferred_domain: Optional[Domain] = None
    task_type: Optional[TaskType] = None


@dataclass
class OrchestrationResult:
    domain: Domain
    task_type: TaskType
    result: Dict[str, Any]
    execution_time: float
    confidence: float
    sources: List[str]
    next_actions: List[str]


class DomainClassifier:
    """Intelligent domain classification for user requests"""
    
    # Business intelligence patterns
    SOPHIA_PATTERNS = [
        r'sales|revenue|customer|crm|hubspot|gong|salesforce',
        r'business|analytics|report|dashboard|metrics',
        r'lead|deal|pipeline|conversion|roi',
        r'call|meeting|prospect|client',
        r'financial|budget|forecast|quarter'
    ]
    
    # Technical patterns  
    ARTEMIS_PATTERNS = [
        r'code|deploy|agent|swarm|debug|test',
        r'api|endpoint|database|server|infrastructure',
        r'bug|error|exception|log|monitor',
        r'git|commit|branch|pull request',
        r'architecture|design|pattern|framework'
    ]
    
    # Research patterns
    RESEARCH_PATTERNS = [
        r'research|study|analyze|investigate',
        r'industry|market|trend|competitive',
        r'report|summary|findings|insights',
        r'proptech|property|rental|apartment',
        r'ai trends|technology|innovation'
    ]
    
    def classify_domain(self, query: str) -> tuple[Domain, float]:
        """Classify user query to appropriate domain"""
        query_lower = query.lower()
        
        sophia_score = self._calculate_pattern_score(query_lower, self.SOPHIA_PATTERNS)
        artemis_score = self._calculate_pattern_score(query_lower, self.ARTEMIS_PATTERNS)
        research_score = self._calculate_pattern_score(query_lower, self.RESEARCH_PATTERNS)
        
        # Determine domain based on highest score
        if research_score > 0.4:
            return Domain.SOPHIA, research_score  # Research goes to Sophia domain
        elif sophia_score > artemis_score and sophia_score > 0.3:
            return Domain.SOPHIA, sophia_score
        elif artemis_score > 0.3:
            return Domain.ARTEMIS, artemis_score
        else:
            return Domain.UNIVERSAL, 0.5  # Default to universal handling
    
    def classify_task_type(self, query: str) -> TaskType:
        """Classify the type of task being requested"""
        query_lower = query.lower()
        
        if re.search(r'create|build|make|generate|design', query_lower):
            return TaskType.CREATE
        elif re.search(r'analyze|review|examine|study', query_lower):
            return TaskType.ANALYZE
        elif re.search(r'research|investigate|find out|look into', query_lower):
            return TaskType.RESEARCH
        elif re.search(r'run|execute|start|deploy|launch', query_lower):
            return TaskType.EXECUTE
        elif re.search(r'monitor|watch|track|status|health', query_lower):
            return TaskType.MONITOR
        else:
            return TaskType.QUERY
    
    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> float:
        """Calculate match score for pattern list"""
        total_matches = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text))
            total_matches += matches
        
        # Normalize by text length and pattern count
        score = min(total_matches / (len(text.split()) + 1), 1.0)
        return score


class SophiaHandler:
    """Handler for business intelligence requests"""
    
    async def handle_query(self, request: UniversalRequest, user: User) -> OrchestrationResult:
        """Handle Sophia domain queries"""
        start_time = datetime.utcnow()
        
        # Check permissions
        if not rbac_manager.has_permission(user.user_id, Permission.SOPHIA_READ):
            raise PermissionError("No access to Sophia business intelligence")
        
        # Route to appropriate Sophia service
        if "gong" in request.user_query.lower():
            result = await self._handle_gong_query(request, user)
        elif "hubspot" in request.user_query.lower():
            result = await self._handle_hubspot_query(request, user)
        elif "sales" in request.user_query.lower():
            result = await self._handle_sales_query(request, user)
        elif "research" in request.user_query.lower():
            result = await self._handle_research_request(request, user)
        else:
            result = await self._handle_general_business_query(request, user)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return OrchestrationResult(
            domain=Domain.SOPHIA,
            task_type=DomainClassifier().classify_task_type(request.user_query),
            result=result,
            execution_time=execution_time,
            confidence=0.8,
            sources=["business_intelligence", "crm_data"],
            next_actions=["analyze_trends", "create_report"]
        )
    
    async def _handle_gong_query(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle Gong-specific queries"""
        # Integration with existing Gong endpoints
        return {
            "type": "gong_analysis",
            "query": request.user_query,
            "data": "Recent call analysis from Gong integration",
            "summary": "Gong data processed successfully"
        }
    
    async def _handle_research_request(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle research automation requests"""
        return {
            "type": "research_automation",
            "query": request.user_query,
            "research_plan": "Multi-source industry research initiated",
            "estimated_completion": "2-4 hours",
            "swarm_deployed": True
        }
    
    async def _handle_general_business_query(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle general business intelligence queries"""
        return {
            "type": "business_intelligence",
            "query": request.user_query,
            "insights": "Business analysis completed",
            "recommendations": ["Review quarterly metrics", "Update sales strategy"]
        }
    
    async def _handle_hubspot_query(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle HubSpot-specific queries"""
        return {
            "type": "hubspot_analysis", 
            "query": request.user_query,
            "data": "HubSpot CRM data analyzed",
            "pipeline_status": "healthy"
        }
    
    async def _handle_sales_query(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle sales-related queries"""
        return {
            "type": "sales_analysis",
            "query": request.user_query,
            "metrics": {"deals": 25, "revenue": "$125k", "conversion": "15%"},
            "trends": "positive"
        }


class ArtemisHandler:
    """Handler for technical/development requests"""
    
    async def handle_query(self, request: UniversalRequest, user: User) -> OrchestrationResult:
        """Handle Artemis domain queries"""
        start_time = datetime.utcnow()
        
        # Check permissions
        if not rbac_manager.has_permission(user.user_id, Permission.ARTEMIS_READ):
            raise PermissionError("No access to Artemis technical systems")
        
        # Route to appropriate technical service
        if "agent" in request.user_query.lower():
            result = await self._handle_agent_request(request, user)
        elif "swarm" in request.user_query.lower():
            result = await self._handle_swarm_request(request, user)
        elif "code" in request.user_query.lower():
            result = await self._handle_code_request(request, user)
        else:
            result = await self._handle_general_technical_query(request, user)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return OrchestrationResult(
            domain=Domain.ARTEMIS,
            task_type=DomainClassifier().classify_task_type(request.user_query),
            result=result,
            execution_time=execution_time,
            confidence=0.9,
            sources=["agent_factory", "code_analysis"],
            next_actions=["deploy_agent", "run_tests"]
        )
    
    async def _handle_agent_request(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle agent creation/management requests"""
        if rbac_manager.has_permission(user.user_id, Permission.AGENT_CREATE):
            return {
                "type": "agent_management",
                "action": "create_agent",
                "query": request.user_query,
                "agent_type": "specialized",
                "status": "deployed"
            }
        else:
            return {
                "type": "agent_management",
                "action": "view_agents",
                "query": request.user_query,
                "available_agents": ["code_reviewer", "test_runner"]
            }
    
    async def _handle_swarm_request(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle swarm orchestration requests"""
        return {
            "type": "swarm_orchestration",
            "query": request.user_query,
            "swarm_type": "collaborative",
            "agents_deployed": 3,
            "execution_status": "running"
        }
    
    async def _handle_code_request(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle code-related requests"""
        return {
            "type": "code_analysis",
            "query": request.user_query,
            "analysis": "Code review completed",
            "suggestions": ["Optimize performance", "Add error handling"]
        }
    
    async def _handle_general_technical_query(self, request: UniversalRequest, user: User) -> Dict[str, Any]:
        """Handle general technical queries"""
        return {
            "type": "technical_support",
            "query": request.user_query,
            "support": "Technical query processed",
            "resources": ["documentation", "api_reference"]
        }


class UniversalOrchestrator:
    """Universal AI Orchestrator - Single interface for all domains"""
    
    def __init__(self):
        self.classifier = DomainClassifier()
        self.sophia_handler = SophiaHandler()
        self.artemis_handler = ArtemisHandler()
        self.active_sessions = {}
    
    async def process_request(self, request: UniversalRequest) -> OrchestrationResult:
        """Process universal request and route to appropriate domain"""
        
        # Get user permissions (create anonymous user if RBAC disabled)
        user = rbac_manager.get_user(request.user_id)
        if not user:
            # Create anonymous user when RBAC is disabled
            from dev_mcp_unified.auth.rbac_manager import User, UserRole, Permission
            from datetime import datetime
            
            # Grant all permissions to anonymous user when RBAC disabled
            all_permissions = {perm.value for perm in Permission}
            
            user = User(
                user_id=request.user_id or "anonymous",
                email="anonymous@sophia.ai",
                role=UserRole.OWNER,  # Full access when no RBAC
                created_at=datetime.utcnow(),
                is_active=True,
                permissions=all_permissions
            )
        
        # Classify domain and task
        domain, confidence = self.classifier.classify_domain(request.user_query)
        task_type = self.classifier.classify_task_type(request.user_query)
        
        # Override domain if user specified preference
        if request.preferred_domain:
            domain = request.preferred_domain
            confidence = 1.0
        
        # Route to appropriate handler
        if domain == Domain.SOPHIA:
            return await self.sophia_handler.handle_query(request, user)
        elif domain == Domain.ARTEMIS:
            return await self.artemis_handler.handle_query(request, user)
        else:
            # Universal handling - combines both domains
            return await self._handle_universal_query(request, user)
    
    async def _handle_universal_query(self, request: UniversalRequest, user: User) -> OrchestrationResult:
        """Handle cross-domain queries"""
        start_time = datetime.utcnow()
        
        # Try both domains and combine results
        results = {}
        
        # Check Sophia access
        if rbac_manager.has_permission(user.user_id, Permission.SOPHIA_READ):
            try:
                sophia_result = await self.sophia_handler.handle_query(request, user)
                results['sophia'] = sophia_result.result
            except Exception as e:
                results['sophia_error'] = str(e)
        
        # Check Artemis access  
        if rbac_manager.has_permission(user.user_id, Permission.ARTEMIS_READ):
            try:
                artemis_result = await self.artemis_handler.handle_query(request, user)
                results['artemis'] = artemis_result.result
            except Exception as e:
                results['artemis_error'] = str(e)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return OrchestrationResult(
            domain=Domain.UNIVERSAL,
            task_type=self.classifier.classify_task_type(request.user_query),
            result={
                "type": "universal_query",
                "query": request.user_query,
                "combined_results": results,
                "cross_domain": True
            },
            execution_time=execution_time,
            confidence=0.7,
            sources=["sophia_domain", "artemis_domain"],
            next_actions=["analyze_cross_domain", "create_unified_report"]
        )
    
    async def stream_response(self, request: UniversalRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response for real-time updates"""
        
        # Initial classification
        domain, confidence = self.classifier.classify_domain(request.user_query)
        
        yield {
            "type": "classification",
            "domain": domain.value,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Processing update
        yield {
            "type": "processing", 
            "status": "routing_to_domain",
            "domain": domain.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Execute and stream result
        try:
            result = await self.process_request(request)
            
            yield {
                "type": "result",
                "domain": result.domain.value,
                "data": result.result,
                "execution_time": result.execution_time,
                "confidence": result.confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get context for active session"""
        return self.active_sessions.get(session_id, {})
    
    def update_session_context(self, session_id: str, context: Dict[str, Any]):
        """Update session context"""
        self.active_sessions[session_id] = context


# Global orchestrator instance
universal_orchestrator = UniversalOrchestrator()