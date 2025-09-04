#!/usr/bin/env python3
"""
Learning Middleware for Sophia Intel AI Swarms
Middleware components that can be injected into any execution mode for learning enhancement

Features:
- Pre-execution knowledge application
- Real-time learning during execution  
- Post-execution experience capture
- Cross-execution mode learning transfer
- Minimal performance overhead
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from uuid import uuid4

import numpy as np
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from app.core.ai_logger import logger
from app.swarms.core.swarm_base import SwarmBase, SwarmExecutionMode, SwarmMetrics
from app.swarms.learning.adaptive_learning_system import AdaptiveLearningSystem, LearningExperience, LearnedKnowledge
from app.swarms.learning.memory_integrated_learning import MemoryIntegratedLearningSystem

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# =============================================================================
# LEARNING MIDDLEWARE INTERFACES
# =============================================================================

class LearningMiddleware(ABC):
    """Abstract base class for learning middleware components"""
    
    @abstractmethod
    async def before_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process before swarm execution"""
        pass
    
    @abstractmethod
    async def during_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        partial_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process during swarm execution (for real-time learning)"""
        pass
    
    @abstractmethod
    async def after_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process after swarm execution"""
        pass


@dataclass
class MiddlewareChain:
    """Chain of learning middleware components"""
    middleware_components: List[LearningMiddleware] = field(default_factory=list)
    
    def add_middleware(self, middleware: LearningMiddleware):
        """Add middleware to the chain"""
        self.middleware_components.append(middleware)
    
    async def process_before_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process all middleware components before execution"""
        combined_enhancements = {}
        
        for middleware in self.middleware_components:
            try:
                enhancements = await middleware.before_execution(swarm, problem, context)
                if enhancements:
                    combined_enhancements.update(enhancements)
            except Exception as e:
                logger.warning(f"Middleware {type(middleware).__name__} before_execution failed: {e}")
        
        return combined_enhancements
    
    async def process_during_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        partial_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process all middleware components during execution"""
        combined_updates = {}
        
        for middleware in self.middleware_components:
            try:
                updates = await middleware.during_execution(swarm, problem, context, partial_results)
                if updates:
                    combined_updates.update(updates)
            except Exception as e:
                logger.warning(f"Middleware {type(middleware).__name__} during_execution failed: {e}")
        
        return combined_updates
    
    async def process_after_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process all middleware components after execution"""
        combined_insights = {}
        
        for middleware in self.middleware_components:
            try:
                insights = await middleware.after_execution(swarm, problem, context, results, execution_metadata)
                if insights:
                    combined_insights.update(insights)
            except Exception as e:
                logger.warning(f"Middleware {type(middleware).__name__} after_execution failed: {e}")
        
        return combined_insights


# =============================================================================
# CORE LEARNING MIDDLEWARE IMPLEMENTATIONS
# =============================================================================

class KnowledgeApplicationMiddleware(LearningMiddleware):
    """Middleware for applying learned knowledge before execution"""
    
    def __init__(self, learning_system: AdaptiveLearningSystem, max_knowledge_items: int = 5):
        self.learning_system = learning_system
        self.max_knowledge_items = max_knowledge_items
        self.applied_knowledge_history: List[Dict[str, Any]] = []
    
    async def before_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply relevant learned knowledge before execution"""
        with tracer.start_span("knowledge_application", kind=SpanKind.INTERNAL) as span:
            # Build knowledge query context
            knowledge_context = {
                'execution_mode': swarm.config.execution_mode,
                'problem_type': problem.get('type', 'general'),
                'agent_count': len(swarm.agents),
                'swarm_type': swarm.config.swarm_type.value,
                'capabilities': [cap.value for cap in swarm.config.capabilities]
            }
            
            # Get applicable knowledge
            applicable_knowledge = await self.learning_system.get_applicable_knowledge(
                knowledge_context, limit=self.max_knowledge_items
            )
            
            # Apply each piece of knowledge
            applied_modifications = {}
            knowledge_metadata = []
            
            for knowledge in applicable_knowledge:
                try:
                    application_result = await self.learning_system.apply_knowledge(
                        knowledge, knowledge_context
                    )
                    
                    # Merge modifications
                    modifications = application_result.get('modifications', {})
                    applied_modifications.update(modifications)
                    
                    # Track metadata
                    knowledge_metadata.append({
                        'knowledge_id': knowledge.id,
                        'knowledge_type': knowledge.knowledge_type.value,
                        'confidence': knowledge.confidence,
                        'expected_improvement': application_result.get('expected_improvement', 0.0),
                        'modifications': modifications
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to apply knowledge {knowledge.id}: {e}")
            
            # Track application history
            application_record = {
                'timestamp': datetime.now(timezone.utc),
                'swarm_id': swarm.config.swarm_id,
                'problem_type': problem.get('type', 'general'),
                'knowledge_applied': len(knowledge_metadata),
                'modifications': applied_modifications
            }
            self.applied_knowledge_history.append(application_record)
            
            span.set_attribute("knowledge.applied_count", len(knowledge_metadata))
            span.set_attribute("modifications.count", len(applied_modifications))
            
            logger.debug(f"🎯 Applied {len(knowledge_metadata)} knowledge items with {len(applied_modifications)} modifications")
            
            return {
                'knowledge_enhancements': {
                    'applied_knowledge': knowledge_metadata,
                    'execution_modifications': applied_modifications,
                    'expected_improvements': [km['expected_improvement'] for km in knowledge_metadata]
                }
            }
    
    async def during_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        partial_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Monitor knowledge application effectiveness during execution"""
        # Real-time monitoring could be implemented here
        return {}
    
    async def after_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate knowledge application effectiveness after execution"""
        knowledge_enhancements = context.get('knowledge_enhancements', {})
        applied_knowledge = knowledge_enhancements.get('applied_knowledge', [])
        
        if not applied_knowledge:
            return {}
        
        # Calculate effectiveness
        success_rate = sum(1 for r in results if r.get('success', False)) / max(len(results), 1)
        avg_quality = np.mean([r.get('quality_score', 0.0) for r in results]) if results else 0.0
        
        # Compare with expected improvements
        expected_improvements = knowledge_enhancements.get('expected_improvements', [])
        avg_expected = np.mean(expected_improvements) if expected_improvements else 0.0
        
        effectiveness_score = min((avg_quality / max(avg_expected, 0.1)), 2.0) if avg_expected > 0 else 1.0
        
        logger.debug(f"📊 Knowledge application effectiveness: {effectiveness_score:.2f}")
        
        return {
            'knowledge_application_insights': {
                'effectiveness_score': effectiveness_score,
                'knowledge_count': len(applied_knowledge),
                'success_rate': success_rate,
                'quality_improvement': max(0, avg_quality - 0.5)  # Baseline assumption
            }
        }


class ExperienceCaptureMiddleware(LearningMiddleware):
    """Middleware for capturing learning experiences"""
    
    def __init__(
        self,
        learning_system: AdaptiveLearningSystem,
        memory_system: Optional[MemoryIntegratedLearningSystem] = None
    ):
        self.learning_system = learning_system
        self.memory_system = memory_system
        self.execution_start_times: Dict[str, float] = {}
        self.captured_experiences: List[str] = []
    
    async def before_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record execution start time"""
        execution_id = f"exec_{uuid4().hex[:8]}"
        self.execution_start_times[execution_id] = time.time()
        
        return {
            'experience_capture': {
                'execution_id': execution_id,
                'start_time': self.execution_start_times[execution_id]
            }
        }
    
    async def during_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        partial_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Capture intermediate learning data during execution"""
        # Could capture partial experiences for real-time learning
        return {}
    
    async def after_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture complete learning experience after execution"""
        with tracer.start_span("experience_capture", kind=SpanKind.INTERNAL) as span:
            experience_capture = context.get('experience_capture', {})
            execution_id = experience_capture.get('execution_id', 'unknown')
            start_time = self.execution_start_times.get(execution_id, time.time())
            
            execution_time = time.time() - start_time
            
            # Calculate execution quality
            success_count = sum(1 for r in results if r.get('success', False))
            success_rate = success_count / max(len(results), 1)
            avg_quality = np.mean([r.get('quality_score', 0.0) for r in results]) if results else 0.0
            
            # Create comprehensive solution summary
            solution_summary = {
                'success': success_rate > 0.5,
                'quality_score': avg_quality,
                'confidence': success_rate,
                'execution_time': execution_time,
                'agent_results': results,
                'success_rate': success_rate
            }
            
            # Capture learning experience
            experience_id = await self.learning_system.capture_experience(
                swarm_id=swarm.config.swarm_id,
                execution_mode=swarm.config.execution_mode,
                problem_context=problem,
                execution_context={
                    'agent_count': len(swarm.agents),
                    'execution_time': execution_time,
                    'swarm_type': swarm.config.swarm_type.value,
                    'patterns_used': list(swarm.patterns.keys()) if swarm.patterns else [],
                    **execution_metadata
                },
                agent_states={f"agent_{i}": {} for i in range(len(swarm.agents))},
                solution=solution_summary,
                metrics=swarm.metrics
            )
            
            self.captured_experiences.append(experience_id)
            
            # Store in memory system if available
            if self.memory_system:
                await self.memory_system.store_learning_episode(
                    LearningExperience(
                        id=experience_id,
                        swarm_id=swarm.config.swarm_id,
                        execution_mode=swarm.config.execution_mode,
                        problem_type=problem.get('type', 'general'),
                        success=solution_summary['success'],
                        quality_score=avg_quality,
                        confidence=success_rate
                    ),
                    context=context,
                    outcome=solution_summary
                )
            
            # Cleanup execution tracking
            if execution_id in self.execution_start_times:
                del self.execution_start_times[execution_id]
            
            span.set_attribute("experience.id", experience_id)
            span.set_attribute("experience.success", solution_summary['success'])
            span.set_attribute("experience.quality_score", avg_quality)
            
            logger.debug(f"📊 Captured learning experience: {experience_id}")
            
            return {
                'experience_insights': {
                    'experience_id': experience_id,
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'quality_score': avg_quality,
                    'success_rate': success_rate,
                    'execution_time': execution_time
                }
            }


class RealTimeLearningMiddleware(LearningMiddleware):
    """Middleware for real-time learning during execution"""
    
    def __init__(
        self,
        learning_system: AdaptiveLearningSystem,
        learning_interval: float = 5.0,  # seconds
        min_partial_results: int = 2
    ):
        self.learning_system = learning_system
        self.learning_interval = learning_interval
        self.min_partial_results = min_partial_results
        self.last_learning_times: Dict[str, float] = {}
        self.real_time_adjustments: List[Dict[str, Any]] = []
    
    async def before_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initialize real-time learning tracking"""
        execution_id = context.get('experience_capture', {}).get('execution_id', f"rt_{uuid4().hex[:8]}")
        self.last_learning_times[execution_id] = time.time()
        
        return {
            'real_time_learning': {
                'enabled': True,
                'execution_id': execution_id,
                'learning_interval': self.learning_interval
            }
        }
    
    async def during_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        partial_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform real-time learning adjustments during execution"""
        real_time_config = context.get('real_time_learning', {})
        
        if not real_time_config.get('enabled', False):
            return {}
        
        execution_id = real_time_config.get('execution_id', 'unknown')
        current_time = time.time()
        last_learning_time = self.last_learning_times.get(execution_id, current_time)
        
        # Check if it's time for learning update
        if (current_time - last_learning_time < self.learning_interval or 
            len(partial_results) < self.min_partial_results):
            return {}
        
        # Analyze partial results for real-time insights
        successful_results = [r for r in partial_results if r.get('success', False)]
        
        if len(successful_results) >= 2:
            # Extract patterns from successful partial results
            success_patterns = await self._extract_success_patterns(successful_results, problem)
            
            # Generate real-time adjustments
            adjustments = await self._generate_real_time_adjustments(
                success_patterns, swarm, problem, context
            )
            
            if adjustments:
                adjustment_record = {
                    'timestamp': datetime.now(timezone.utc),
                    'execution_id': execution_id,
                    'partial_results_count': len(partial_results),
                    'successful_count': len(successful_results),
                    'adjustments': adjustments
                }
                self.real_time_adjustments.append(adjustment_record)
                
                logger.debug(f"⚡ Real-time learning adjustment: {len(adjustments)} modifications")
                
                return {
                    'real_time_adjustments': adjustments,
                    'learning_trigger': 'partial_results_analysis'
                }
        
        # Update last learning time
        self.last_learning_times[execution_id] = current_time
        return {}
    
    async def after_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of real-time learning"""
        real_time_config = context.get('real_time_learning', {})
        execution_id = real_time_config.get('execution_id', 'unknown')
        
        # Find adjustments made during this execution
        execution_adjustments = [
            adj for adj in self.real_time_adjustments
            if adj['execution_id'] == execution_id
        ]
        
        if not execution_adjustments:
            return {}
        
        # Analyze impact of real-time adjustments
        final_success_rate = sum(1 for r in results if r.get('success', False)) / max(len(results), 1)
        final_quality = np.mean([r.get('quality_score', 0.0) for r in results]) if results else 0.0
        
        # Clean up tracking
        if execution_id in self.last_learning_times:
            del self.last_learning_times[execution_id]
        
        logger.debug(f"📈 Real-time learning impact analysis: {len(execution_adjustments)} adjustments")
        
        return {
            'real_time_learning_insights': {
                'adjustments_made': len(execution_adjustments),
                'final_success_rate': final_success_rate,
                'final_quality': final_quality,
                'learning_effectiveness': min(final_quality / 0.5, 2.0)  # Normalized score
            }
        }
    
    async def _extract_success_patterns(
        self,
        successful_results: List[Dict[str, Any]],
        problem: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract patterns from successful partial results"""
        patterns = {
            'common_approaches': [],
            'quality_indicators': [],
            'timing_patterns': []
        }
        
        # Find common approaches
        approaches = [r.get('approach', 'unknown') for r in successful_results]
        from collections import Counter
        common_approaches = Counter(approaches).most_common(3)
        patterns['common_approaches'] = [approach for approach, count in common_approaches]
        
        # Analyze quality indicators
        quality_scores = [r.get('quality_score', 0.0) for r in successful_results]
        if quality_scores:
            patterns['quality_indicators'] = {
                'avg_quality': np.mean(quality_scores),
                'min_quality': min(quality_scores),
                'max_quality': max(quality_scores),
                'quality_trend': 'improving' if len(quality_scores) > 1 and quality_scores[-1] > quality_scores[0] else 'stable'
            }
        
        return patterns
    
    async def _generate_real_time_adjustments(
        self,
        success_patterns: Dict[str, Any],
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate real-time execution adjustments based on patterns"""
        adjustments = {}
        
        # Quality-based adjustments
        quality_indicators = success_patterns.get('quality_indicators', {})
        avg_quality = quality_indicators.get('avg_quality', 0.0)
        
        if avg_quality > 0.8:
            # High quality - maintain current approach
            adjustments['quality_threshold'] = avg_quality * 0.9
            adjustments['confidence_boost'] = 0.1
        elif avg_quality < 0.5:
            # Low quality - suggest more exploration
            adjustments['exploration_factor'] = 1.2
            adjustments['quality_threshold'] = 0.6
        
        # Approach-based adjustments
        common_approaches = success_patterns.get('common_approaches', [])
        if common_approaches:
            most_successful_approach = common_approaches[0]
            adjustments['recommended_approach'] = most_successful_approach
            adjustments['approach_confidence'] = 0.8
        
        return adjustments


class CrossModalLearningMiddleware(LearningMiddleware):
    """Middleware for transferring learning between execution modes"""
    
    def __init__(
        self,
        learning_system: AdaptiveLearningSystem,
        memory_system: Optional[MemoryIntegratedLearningSystem] = None
    ):
        self.learning_system = learning_system
        self.memory_system = memory_system
        self.mode_transfer_cache: Dict[SwarmExecutionMode, Dict[str, Any]] = {}
        self.transfer_effectiveness: Dict[Tuple[SwarmExecutionMode, SwarmExecutionMode], float] = {}
    
    async def before_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply cross-modal learning from other execution modes"""
        current_mode = swarm.config.execution_mode
        
        # Search for successful experiences from other execution modes
        if self.memory_system:
            similar_episodes = await self.memory_system.replay_similar_episodes(
                {
                    'problem_type': problem.get('type', 'general'),
                    'agent_count': len(swarm.agents),
                    'complexity': problem.get('complexity', 'medium')
                },
                limit=10
            )
            
            # Filter for different execution modes
            cross_modal_episodes = [
                episode for episode in similar_episodes
                if episode['metadata'].get('execution_mode') != current_mode.value
            ]
            
            if cross_modal_episodes:
                # Extract transferable patterns
                transfer_patterns = await self._extract_transfer_patterns(
                    cross_modal_episodes, current_mode, problem
                )
                
                if transfer_patterns:
                    logger.debug(f"🔄 Found {len(transfer_patterns)} cross-modal transfer patterns")
                    return {
                        'cross_modal_learning': {
                            'transfer_patterns': transfer_patterns,
                            'source_episodes': len(cross_modal_episodes),
                            'target_mode': current_mode.value
                        }
                    }
        
        return {}
    
    async def during_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        partial_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Monitor cross-modal transfer effectiveness during execution"""
        return {}
    
    async def after_execution(
        self,
        swarm: SwarmBase,
        problem: Dict[str, Any],
        context: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate cross-modal learning transfer effectiveness"""
        cross_modal_config = context.get('cross_modal_learning', {})
        
        if not cross_modal_config:
            return {}
        
        transfer_patterns = cross_modal_config.get('transfer_patterns', [])
        
        if transfer_patterns:
            # Calculate transfer effectiveness
            final_success_rate = sum(1 for r in results if r.get('success', False)) / max(len(results), 1)
            final_quality = np.mean([r.get('quality_score', 0.0) for r in results]) if results else 0.0
            
            # Compare with baseline expectations
            baseline_success = 0.6  # Assumed baseline
            baseline_quality = 0.5  # Assumed baseline
            
            success_improvement = max(0, final_success_rate - baseline_success)
            quality_improvement = max(0, final_quality - baseline_quality)
            
            transfer_effectiveness = (success_improvement + quality_improvement) / 2.0
            
            logger.debug(f"🔄 Cross-modal transfer effectiveness: {transfer_effectiveness:.2f}")
            
            return {
                'cross_modal_insights': {
                    'patterns_applied': len(transfer_patterns),
                    'transfer_effectiveness': transfer_effectiveness,
                    'success_improvement': success_improvement,
                    'quality_improvement': quality_improvement
                }
            }
        
        return {}
    
    async def _extract_transfer_patterns(
        self,
        cross_modal_episodes: List[Dict[str, Any]],
        target_mode: SwarmExecutionMode,
        problem: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract transferable patterns from cross-modal episodes"""
        patterns = []
        
        # Group episodes by source execution mode
        mode_groups = {}
        for episode in cross_modal_episodes:
            source_mode = episode['metadata'].get('execution_mode', 'unknown')
            if source_mode not in mode_groups:
                mode_groups[source_mode] = []
            mode_groups[source_mode].append(episode)
        
        # Extract patterns from each source mode
        for source_mode, episodes in mode_groups.items():
            if len(episodes) < 2:  # Need multiple examples for pattern extraction
                continue
            
            # Find common success factors
            successful_episodes = [
                ep for ep in episodes
                if ep['metadata'].get('success', False) and ep['metadata'].get('quality_score', 0) > 0.7
            ]
            
            if successful_episodes:
                # Extract common patterns
                pattern = {
                    'source_mode': source_mode,
                    'target_mode': target_mode.value,
                    'episode_count': len(successful_episodes),
                    'avg_quality': np.mean([ep['metadata'].get('quality_score', 0) for ep in successful_episodes]),
                    'transfer_confidence': min(len(successful_episodes) / 5.0, 1.0)
                }
                
                # Add transferable strategies (simplified)
                if successful_episodes:
                    pattern['strategies'] = {
                        'approach': 'adaptive',  # Simplified
                        'coordination': 'optimized',
                        'quality_focus': True
                    }
                
                patterns.append(pattern)
        
        return patterns


# =============================================================================
# LEARNING MIDDLEWARE FACTORY
# =============================================================================

class LearningMiddlewareFactory:
    """Factory for creating and configuring learning middleware"""
    
    def __init__(
        self,
        learning_system: AdaptiveLearningSystem,
        memory_system: Optional[MemoryIntegratedLearningSystem] = None
    ):
        self.learning_system = learning_system
        self.memory_system = memory_system
    
    def create_standard_middleware_chain(
        self,
        include_real_time: bool = True,
        include_cross_modal: bool = True
    ) -> MiddlewareChain:
        """Create a standard middleware chain with common components"""
        chain = MiddlewareChain()
        
        # Always include knowledge application and experience capture
        chain.add_middleware(KnowledgeApplicationMiddleware(self.learning_system))
        chain.add_middleware(ExperienceCaptureMiddleware(self.learning_system, self.memory_system))
        
        # Optional components
        if include_real_time:
            chain.add_middleware(RealTimeLearningMiddleware(self.learning_system))
        
        if include_cross_modal and self.memory_system:
            chain.add_middleware(CrossModalLearningMiddleware(self.learning_system, self.memory_system))
        
        return chain
    
    def create_lightweight_middleware_chain(self) -> MiddlewareChain:
        """Create a lightweight middleware chain with minimal overhead"""
        chain = MiddlewareChain()
        
        # Only basic knowledge application and experience capture
        chain.add_middleware(KnowledgeApplicationMiddleware(self.learning_system, max_knowledge_items=3))
        chain.add_middleware(ExperienceCaptureMiddleware(self.learning_system))
        
        return chain
    
    def create_research_middleware_chain(self) -> MiddlewareChain:
        """Create a comprehensive middleware chain for research/experimentation"""
        chain = MiddlewareChain()
        
        # All available middleware components
        chain.add_middleware(KnowledgeApplicationMiddleware(self.learning_system, max_knowledge_items=10))
        chain.add_middleware(ExperienceCaptureMiddleware(self.learning_system, self.memory_system))
        chain.add_middleware(RealTimeLearningMiddleware(self.learning_system, learning_interval=2.0))
        
        if self.memory_system:
            chain.add_middleware(CrossModalLearningMiddleware(self.learning_system, self.memory_system))
        
        return chain


# =============================================================================
# SWARM INTEGRATION HELPER
# =============================================================================

async def inject_learning_middleware(
    swarm: SwarmBase,
    middleware_chain: MiddlewareChain
) -> SwarmBase:
    """Inject learning middleware into an existing swarm"""
    
    # Store original methods
    original_solve_problem = swarm.solve_problem
    
    async def middleware_enhanced_solve_problem(problem: dict[str, Any]):
        """Enhanced solve_problem with middleware integration"""
        context = await swarm.prepare_context(problem)
        
        try:
            # Before execution middleware
            middleware_enhancements = await middleware_chain.process_before_execution(
                swarm, problem, context
            )
            
            # Merge middleware enhancements into context
            enhanced_context = {**context, **middleware_enhancements}
            
            # Execute with enhanced context
            start_time = time.time()
            
            # Apply patterns and execute agents with enhanced context
            enhanced_problem, enhanced_context = await swarm.apply_patterns(problem, enhanced_context)
            results = await swarm.execute_agents(enhanced_problem, enhanced_context)
            
            execution_time = time.time() - start_time
            execution_metadata = {'execution_time': execution_time}
            
            # After execution middleware
            middleware_insights = await middleware_chain.process_after_execution(
                swarm, problem, enhanced_context, results, execution_metadata
            )
            
            # Apply quality gates
            quality_passed, filtered_results = await swarm.apply_quality_gates(results, problem)
            
            # Build final response with learning insights
            final_result = await swarm.reach_consensus(filtered_results)
            
            # Add middleware insights to metrics
            if middleware_insights:
                swarm.metrics.record_execution(
                    success=final_result.get('success', quality_passed),
                    response_time=execution_time,
                    agents_used=[agent.__class__.__name__ for agent in swarm.agents],
                    patterns_used=list(swarm.patterns.keys())
                )
            
            # Return enhanced result (would need to match SwarmResponse format)
            return final_result
            
        except Exception as e:
            logger.error(f"Middleware-enhanced execution failed: {e}")
            # Fallback to original method
            return await original_solve_problem(problem)
    
    # Replace the solve_problem method
    swarm.solve_problem = middleware_enhanced_solve_problem
    
    logger.info(f"🔧 Injected learning middleware chain with {len(middleware_chain.middleware_components)} components")
    return swarm


if __name__ == "__main__":
    # Example usage demonstration
    async def demo():
        from app.memory.unified_memory import get_memory_store
        from app.swarms.communication.message_bus import MessageBus
        from app.swarms.learning.adaptive_learning_system import create_learning_system
        from app.swarms.learning.memory_integrated_learning import create_memory_integrated_learning
        
        # Initialize components
        memory_store = get_memory_store()
        message_bus = MessageBus()
        await message_bus.initialize()
        
        # Create learning systems
        learning_system = await create_learning_system(memory_store, message_bus)
        memory_learning_system = await create_memory_integrated_learning(memory_store)
        
        # Create middleware factory
        factory = LearningMiddlewareFactory(learning_system, memory_learning_system)
        
        # Create different middleware chains
        standard_chain = factory.create_standard_middleware_chain()
        lightweight_chain = factory.create_lightweight_middleware_chain()
        research_chain = factory.create_research_middleware_chain()
        
        print("🔧 Learning middleware chains created:")
        print(f"  Standard chain: {len(standard_chain.middleware_components)} components")
        print(f"  Lightweight chain: {len(lightweight_chain.middleware_components)} components")
        print(f"  Research chain: {len(research_chain.middleware_components)} components")
        
        # Cleanup
        await learning_system.cleanup()
        await memory_learning_system.cleanup()
        await message_bus.close()
        
        print("✅ Demo completed")
    
    asyncio.run(demo())