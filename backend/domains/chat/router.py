"""
Chat Router for intelligent backend selection
"""

from typing import Dict, Any, Optional
import re
import asyncio
from datetime import datetime

from backend.config.settings import SophiaConfig, config


class ChatRouter:
    """Intelligent chat router for backend selection"""
    
    def __init__(self, settings: SophiaConfig = None):
        self.settings = settings or config
        
        # Keywords that suggest Swarm usage
        self.swarm_keywords = {
            'project', 'build', 'architecture', 'test', 'analyze', 'comprehensive',
            'workflow', 'system', 'design', 'implement', 'create', 'develop',
            'complex', 'multi-step', 'detailed', 'thorough', 'complete'
        }
        
        # Keywords that suggest Orchestrator usage
        self.orchestrator_keywords = {
            'what', 'how', 'why', 'when', 'where', 'explain', 'define',
            'help', 'assist', 'quick', 'simple', 'basic', 'tell', 'show'
        }
    
    async def analyze_message_for_backend(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze message to determine optimal backend"""
        try:
            message_lower = message.lower()
            words = set(re.findall(r'\b\w+\b', message_lower))
            
            # Count keyword matches
            swarm_score = len(words.intersection(self.swarm_keywords))
            orchestrator_score = len(words.intersection(self.orchestrator_keywords))
            
            # Message length factor (longer messages often need Swarm)
            length_factor = len(message) / 100  # Normalize to 0-10 range
            if length_factor > 5:
                swarm_score += 2
            
            # Question count (multiple questions suggest Swarm)
            question_count = message.count('?')
            if question_count > 1:
                swarm_score += 1
            
            # Step-by-step indicators
            if any(indicator in message_lower for indicator in ['step by step', 'first', 'then', 'next', 'finally']):
                swarm_score += 2
            
            # Context factor
            if context:
                recent_backend = context.get('recent_backend')
                if recent_backend == 'swarm':
                    swarm_score += 1
                elif recent_backend == 'orchestrator':
                    orchestrator_score += 1
            
            # Determine recommendation
            if swarm_score > orchestrator_score:
                recommended_backend = 'swarm'
                confidence = min(0.9, 0.5 + (swarm_score - orchestrator_score) * 0.1)
            elif orchestrator_score > swarm_score:
                recommended_backend = 'orchestrator'
                confidence = min(0.9, 0.5 + (orchestrator_score - swarm_score) * 0.1)
            else:
                # Default to orchestrator for ties
                recommended_backend = 'orchestrator'
                confidence = 0.5
            
            return {
                'recommended_backend': recommended_backend,
                'confidence': confidence,
                'swarm_score': swarm_score,
                'orchestrator_score': orchestrator_score,
                'analysis': {
                    'message_length': len(message),
                    'question_count': question_count,
                    'swarm_keywords_found': list(words.intersection(self.swarm_keywords)),
                    'orchestrator_keywords_found': list(words.intersection(self.orchestrator_keywords))
                }
            }
            
        except Exception as e:
            # Default to orchestrator on error
            return {
                'recommended_backend': 'orchestrator',
                'confidence': 0.5,
                'error': str(e),
                'analysis': {}
            }
    
    async def select_backend(self, message: str, explicit_backend: Optional[str] = None, context: Optional[Dict] = None) -> str:
        """Select the appropriate backend for processing"""
        try:
            # Use explicit backend if provided
            if explicit_backend in ['swarm', 'orchestrator']:
                return explicit_backend
            
            # Analyze message for backend recommendation
            analysis = await self.analyze_message_for_backend(message, context)
            return analysis['recommended_backend']
            
        except Exception:
            # Default to orchestrator on any error
            return 'orchestrator'
    
    async def get_backend_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for backend selection optimization"""
        try:
            # This would typically come from observability service
            return {
                'orchestrator': {
                    'avg_response_time': 1.2,
                    'success_rate': 0.98,
                    'last_24h_requests': 150
                },
                'swarm': {
                    'avg_response_time': 3.5,
                    'success_rate': 0.95,
                    'last_24h_requests': 45
                }
            }
        except Exception:
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for chat router"""
        try:
            # Test backend analysis
            test_message = "What is machine learning?"
            analysis = await self.analyze_message_for_backend(test_message)
            
            return {
                'status': 'healthy',
                'test_analysis': analysis,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

