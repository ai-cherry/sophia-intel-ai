"""
Enhanced Orchestrator Mixin
============================
Adds memory and repository awareness to orchestrators
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
from datetime import datetime

from app.orchestrators.memory.tiered_memory_system import (
    MemorySystem,
    MemoryTier,
    ConversationContext
)
from app.orchestrators.repository.code_intelligence import CodeIntelligence
from app.orchestrators.memory.memory_config import memory_config
from app.orchestrators.memory.storage_adapter import StorageFactory

logger = logging.getLogger(__name__)


class EnhancedOrchestratorMixin:
    """
    Mixin to add memory and intelligence capabilities to orchestrators
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_system: Optional[MemorySystem] = None
        self.code_intelligence: Optional[CodeIntelligence] = None
        self.session_id: Optional[str] = None
        self.project_path: Optional[str] = None
        self._memory_initialized = False
        self._code_intel_initialized = False
        
    async def initialize_memory(self, session_id: str, project_path: Optional[str] = None):
        """Initialize memory system for the session"""
        try:
            self.session_id = session_id
            self.project_path = project_path or str(Path.cwd())
            
            # Create memory system with appropriate configuration
            redis_url = memory_config.redis_url if memory_config.redis_url else None
            self.memory_system = MemorySystem(
                session_id=session_id,
                project_path=self.project_path,
                redis_url=redis_url
            )
            
            await self.memory_system.initialize()
            self._memory_initialized = True
            
            # Initialize code intelligence if project path provided
            if project_path and Path(project_path).exists():
                await self.initialize_code_intelligence(project_path)
                
            logger.info(f"Memory system initialized for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            self._memory_initialized = False
            
    async def initialize_code_intelligence(self, project_path: str):
        """Initialize code intelligence for repository awareness"""
        try:
            self.code_intelligence = CodeIntelligence(project_path)
            
            # Perform initial repository analysis in background
            asyncio.create_task(self._analyze_repository_background())
            
            self._code_intel_initialized = True
            logger.info(f"Code intelligence initialized for {project_path}")
            
        except Exception as e:
            logger.error(f"Error initializing code intelligence: {e}")
            self._code_intel_initialized = False
            
    async def _analyze_repository_background(self):
        """Analyze repository in background"""
        if self.code_intelligence:
            try:
                analysis = await self.code_intelligence.analyze_repository()
                
                # Store analysis in project memory
                if self.memory_system and self.memory_system.project:
                    self.memory_system.project.architecture_map = analysis.get('structure', {})
                    self.memory_system.project.tech_stack = analysis.get('tech_stack', {})
                    
                logger.info("Repository analysis completed")
                
            except Exception as e:
                logger.error(f"Error analyzing repository: {e}")
                
    async def process_with_memory(self, message: str, role: str = "user",
                                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a message with memory context"""
        if not self._memory_initialized:
            return {
                "error": "Memory system not initialized",
                "response": "Memory system is not available"
            }
            
        try:
            # Add interaction to memory
            await self.memory_system.add_interaction(role, message, metadata)
            
            # Get relevant context
            context = await self.memory_system.get_context(
                query=message,
                include_tiers=[
                    MemoryTier.WORKING,
                    MemoryTier.SESSION,
                    MemoryTier.PROJECT
                ]
            )
            
            # Add code context if relevant files mentioned
            if self.code_intelligence:
                file_context = await self._get_file_context_from_message(message)
                if file_context:
                    context['code_context'] = file_context
                    
            # Get recommendations from global memory
            recommendations = self.memory_system.global_memory.get_recommendations(context)
            if recommendations:
                context['recommendations'] = recommendations
                
            return context
            
        except Exception as e:
            logger.error(f"Error processing with memory: {e}")
            return {"error": str(e)}
            
    async def _get_file_context_from_message(self, message: str) -> Optional[Dict]:
        """Extract and get context for files mentioned in message"""
        if not self.code_intelligence:
            return None
            
        import re
        
        # Extract file paths from message
        file_pattern = r'(?:[./][\w/.-]+\.(?:py|js|ts|jsx|tsx|md|json|yaml|yml))'
        files = re.findall(file_pattern, message)
        
        if not files:
            return None
            
        file_contexts = {}
        for file_ref in files[:3]:  # Limit to 3 files
            # Resolve to full path
            if file_ref.startswith('./'):
                full_path = str(Path(self.project_path) / file_ref[2:])
            elif file_ref.startswith('/'):
                full_path = file_ref
            else:
                full_path = str(Path(self.project_path) / file_ref)
                
            if Path(full_path).exists():
                context = await self.code_intelligence.get_file_context(full_path)
                if context:
                    file_contexts[file_ref] = context
                    
        return file_contexts if file_contexts else None
        
    async def get_contextual_response(self, query: str) -> str:
        """Generate a contextual response based on memory and patterns"""
        if not self._memory_initialized:
            return self._get_default_response(query)
            
        try:
            # Get context
            context = await self.process_with_memory(query)
            
            # Build response with context awareness
            response_parts = []
            
            # Check if this is a follow-up question
            working_memory = context.get('working_memory', {})
            recent_messages = working_memory.get('messages', [])
            
            if recent_messages and self._is_related_query(query, recent_messages):
                response_parts.append("Building on our previous discussion")
                
            # Add project-specific context
            if 'code_context' in context:
                files = list(context['code_context'].keys())
                response_parts.append(f"Looking at {', '.join(files)}")
                
            # Add recommendations if available
            if 'recommendations' in context:
                for rec in context['recommendations'][:2]:
                    if rec['type'] == 'best_practice':
                        response_parts.append(
                            f"Based on successful patterns (confidence: {rec['confidence']:.0%})"
                        )
                        
            # Learn from this interaction
            await self.memory_system.learn_from_outcome(
                action="query_response",
                outcome={"query": query, "context_used": bool(response_parts)},
                success=True
            )
            
            if response_parts:
                return f"{'. '.join(response_parts)}..."
            else:
                return self._get_default_response(query)
                
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return self._get_default_response(query)
            
    def _is_related_query(self, query: str, recent_messages: List[Dict]) -> bool:
        """Check if query is related to recent messages"""
        query_lower = query.lower()
        
        # Check for pronouns indicating continuation
        pronouns = ["it", "that", "this", "them", "those", "the same"]
        if any(pronoun in query_lower for pronoun in pronouns):
            return True
            
        # Check for topic continuation
        recent_content = " ".join(msg.get("content", "") for msg in recent_messages[-3:])
        
        # Simple keyword overlap check
        query_words = set(query_lower.split())
        recent_words = set(recent_content.lower().split())
        
        overlap = len(query_words & recent_words)
        if overlap > min(3, len(query_words) // 2):
            return True
            
        return False
        
    def _get_default_response(self, query: str) -> str:
        """Get default response when memory is not available"""
        return "Processing your request"
        
    async def save_memory_state(self):
        """Save current memory state"""
        if self.memory_system:
            try:
                await self.memory_system.session.save_to_redis()
                if self.memory_system.project:
                    self.memory_system.project.save_to_cache()
                self.memory_system.global_memory.save_global_knowledge()
                logger.debug("Memory state saved")
            except Exception as e:
                logger.error(f"Error saving memory state: {e}")
                
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if not self.memory_system:
            return {"status": "not_initialized"}
            
        stats = self.memory_system.get_memory_stats()
        stats['code_intelligence'] = {
            'initialized': self._code_intel_initialized,
            'files_analyzed': len(self.code_intelligence.file_cache) if self.code_intelligence else 0,
            'modules_found': len(self.code_intelligence.module_cache) if self.code_intelligence else 0
        }
        
        return stats
        
    async def cleanup_memory(self):
        """Clean up memory resources"""
        if self.memory_system:
            try:
                await self.memory_system.cleanup()
                logger.info("Memory system cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up memory: {e}")
                
                
class ProactiveAssistant:
    """
    Provides proactive suggestions based on context
    """
    
    def __init__(self, memory_system: MemorySystem, 
                 code_intelligence: Optional[CodeIntelligence] = None):
        self.memory = memory_system
        self.code_intel = code_intelligence
        
    async def get_suggestions(self, current_context: Dict) -> List[Dict]:
        """Generate proactive suggestions based on context"""
        suggestions = []
        
        # Suggest based on current task
        if self.memory.working.current_task:
            task_suggestions = await self._get_task_suggestions(
                self.memory.working.current_task
            )
            suggestions.extend(task_suggestions)
            
        # Suggest based on active files
        if self.memory.working.active_files and self.code_intel:
            file_suggestions = await self._get_file_suggestions(
                self.memory.working.active_files
            )
            suggestions.extend(file_suggestions)
            
        # Suggest based on patterns
        pattern_suggestions = await self._get_pattern_suggestions(current_context)
        suggestions.extend(pattern_suggestions)
        
        # Rank and filter suggestions
        ranked = self._rank_suggestions(suggestions, current_context)
        
        return ranked[:5]  # Return top 5 suggestions
        
    async def _get_task_suggestions(self, task: str) -> List[Dict]:
        """Get suggestions based on current task"""
        suggestions = []
        
        task_lower = task.lower()
        
        if "test" in task_lower:
            suggestions.append({
                "type": "action",
                "text": "Run the test suite",
                "command": "pytest",
                "confidence": 0.8
            })
            
        if "refactor" in task_lower:
            suggestions.append({
                "type": "insight",
                "text": "Check for code smells and complexity",
                "action": "analyze_code_quality",
                "confidence": 0.7
            })
            
        if "debug" in task_lower:
            suggestions.append({
                "type": "action",
                "text": "Enable debug logging",
                "command": "set_log_level('DEBUG')",
                "confidence": 0.6
            })
            
        return suggestions
        
    async def _get_file_suggestions(self, files: List[str]) -> List[Dict]:
        """Get suggestions based on active files"""
        suggestions = []
        
        for file in files[:3]:  # Check top 3 files
            if self.code_intel:
                file_context = await self.code_intel.get_file_context(file)
                
                if file_context:
                    # Suggest related files
                    related = file_context.get('related_files', [])
                    if related:
                        suggestions.append({
                            "type": "navigation",
                            "text": f"Related file: {Path(related[0]).name}",
                            "file": related[0],
                            "confidence": 0.7
                        })
                        
                    # Suggest based on complexity
                    complexity = file_context.get('file_info', {}).get('complexity')
                    if complexity and complexity > 10:
                        suggestions.append({
                            "type": "refactor",
                            "text": f"Consider refactoring {Path(file).name} (complexity: {complexity})",
                            "file": file,
                            "confidence": 0.6
                        })
                        
        return suggestions
        
    async def _get_pattern_suggestions(self, context: Dict) -> List[Dict]:
        """Get suggestions based on learned patterns"""
        suggestions = []
        
        # Get recommendations from global memory
        recommendations = self.memory.global_memory.get_recommendations(context)
        
        for rec in recommendations[:3]:
            if rec['type'] == 'best_practice':
                suggestions.append({
                    "type": "best_practice",
                    "text": f"Apply {rec['category']} best practice",
                    "details": rec['recommendation'],
                    "confidence": rec['confidence']
                })
            elif rec['type'] == 'design_pattern':
                suggestions.append({
                    "type": "pattern",
                    "text": f"Consider {rec['pattern']} pattern",
                    "success_rate": rec['success_rate'],
                    "confidence": rec['success_rate']
                })
                
        return suggestions
        
    def _rank_suggestions(self, suggestions: List[Dict], 
                         context: Dict) -> List[Dict]:
        """Rank suggestions by relevance"""
        # Sort by confidence
        sorted_suggestions = sorted(
            suggestions,
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )
        
        # Remove duplicates
        seen = set()
        unique = []
        for sug in sorted_suggestions:
            key = sug.get('text', '')
            if key not in seen:
                seen.add(key)
                unique.append(sug)
                
        return unique