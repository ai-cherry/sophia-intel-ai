#!/usr/bin/env python3
"""
Complete Integration Example for Sophia Intel AI Learning System
Demonstrates how to integrate learning capabilities with existing SwarmBase architecture

This example shows:
1. How to enhance existing swarms with learning
2. Different integration patterns (middleware vs direct integration)
3. Performance monitoring and optimization
4. Real-world usage patterns
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.ai_logger import logger
from app.memory.unified_memory import get_memory_store
from app.swarms.communication.message_bus import MessageBus
from app.swarms.core.swarm_base import (
    SwarmBase, SwarmConfig, SwarmType, SwarmExecutionMode, SwarmCapability, SwarmMetrics
)
from app.models.requests import SwarmResponse

# Learning system imports
from app.swarms.learning.adaptive_learning_system import create_learning_system
from app.swarms.learning.memory_integrated_learning import create_memory_integrated_learning
from app.swarms.learning.learning_middleware import (
    LearningMiddlewareFactory, inject_learning_middleware
)
from app.swarms.learning.learning_enhanced_modes import integrate_learning_with_swarm

logger = logging.getLogger(__name__)


# =============================================================================
# EXAMPLE SWARM IMPLEMENTATION (Based on existing patterns)
# =============================================================================

class ExampleCodeGenerationSwarm(SwarmBase):
    """Example swarm that generates code - demonstrates learning integration"""
    
    def __init__(self, config: SwarmConfig, agents: Optional[List[Any]] = None):
        super().__init__(config, agents)
        self.code_patterns = []
        self.quality_history = []
    
    async def solve_problem(self, problem: dict[str, Any]) -> SwarmResponse:
        """Solve a code generation problem"""
        start_time = time.time()
        
        try:
            # Validate problem
            is_valid, validation_message = await self.validate_problem(problem)
            if not is_valid:
                return SwarmResponse(
                    success=False,
                    result={'error': f'Invalid problem: {validation_message}'},
                    agent_results=[],
                    execution_time=time.time() - start_time,
                    swarm_id=self.config.swarm_id
                )
            
            # Prepare context
            context = await self.prepare_context(problem)
            
            # Apply patterns (quality gates, etc.)
            enhanced_problem, enhanced_context = await self.apply_patterns(problem, context)
            
            # Execute agents
            agent_results = await self.execute_agents(enhanced_problem, enhanced_context)
            
            # Apply quality gates
            quality_passed, filtered_results = await self.apply_quality_gates(agent_results, problem)
            
            # Reach consensus
            consensus_result = await self.reach_consensus(filtered_results)
            
            execution_time = time.time() - start_time
            
            # Update metrics
            self.metrics.record_execution(
                success=consensus_result.get('success', quality_passed),
                response_time=execution_time,
                agents_used=[f"agent_{i}" for i in range(len(self.agents))],
                patterns_used=list(self.patterns.keys())
            )
            
            # Track quality history for learning
            quality_score = consensus_result.get('quality_score', 0.0)
            self.quality_history.append(quality_score)
            
            return SwarmResponse(
                success=consensus_result.get('success', quality_passed),
                result=consensus_result,
                agent_results=filtered_results,
                execution_time=execution_time,
                swarm_id=self.config.swarm_id,
                metadata={
                    'quality_score': quality_score,
                    'patterns_applied': list(self.patterns.keys()),
                    'agent_count': len(self.agents)
                }
            )
            
        except Exception as e:
            logger.error(f"Code generation swarm execution failed: {e}")
            return SwarmResponse(
                success=False,
                result={'error': str(e)},
                agent_results=[],
                execution_time=time.time() - start_time,
                swarm_id=self.config.swarm_id
            )
    
    async def get_swarm_capabilities(self) -> List[SwarmCapability]:
        """Get swarm capabilities"""
        return [
            SwarmCapability.CODING,
            SwarmCapability.QUALITY_ASSURANCE,
            SwarmCapability.PLANNING
        ]
    
    async def validate_problem(self, problem: dict[str, Any]) -> tuple[bool, str]:
        """Validate if swarm can handle this problem"""
        if not problem.get('type') == 'coding':
            return False, "This swarm only handles coding problems"
        
        if not problem.get('description'):
            return False, "Problem must have a description"
        
        return True, "Valid coding problem"
    
    async def _execute_single_agent(self, agent: Any, problem: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single agent - simulated implementation"""
        await asyncio.sleep(0.1)  # Simulate work
        
        # Simulate code generation result
        agent_name = getattr(agent, 'name', f'agent_{id(agent)}')
        
        # Use context enhancements if available (from learning system)
        knowledge_enhancements = context.get('knowledge_enhancements', {})
        applied_knowledge = knowledge_enhancements.get('applied_knowledge', [])
        
        # Simulate better results if learning knowledge was applied
        base_quality = 0.6
        if applied_knowledge:
            # Learning boost based on knowledge confidence
            learning_boost = sum(k.get('confidence', 0.0) for k in applied_knowledge) * 0.1
            base_quality += learning_boost
        
        return {
            'success': True,
            'agent_id': agent_name,
            'code_generated': f"// Code generated by {agent_name}\nfunction solve() {{ return 'solution'; }}",
            'quality_score': min(base_quality, 1.0),
            'confidence': 0.8,
            'approach': 'standard',
            'learning_metadata': {
                'knowledge_applied': len(applied_knowledge),
                'learning_boost': len(applied_knowledge) * 0.1
            }
        }


# =============================================================================
# INTEGRATION PATTERNS
# =============================================================================

class LearningSystemIntegrator:
    """Helper class for integrating learning systems with existing swarms"""
    
    def __init__(self):
        self.memory_store = None
        self.message_bus = None
        self.learning_system = None
        self.memory_learning_system = None
        self.middleware_factory = None
    
    async def initialize(self, learning_config: Optional[Dict[str, Any]] = None):
        """Initialize all learning components"""
        # Initialize core components
        self.memory_store = get_memory_store()
        self.message_bus = MessageBus()
        await self.message_bus.initialize()
        
        # Create learning systems
        self.learning_system = await create_learning_system(
            self.memory_store, 
            self.message_bus, 
            config=learning_config
        )
        
        self.memory_learning_system = await create_memory_integrated_learning(
            self.memory_store,
            config=learning_config
        )
        
        # Create middleware factory
        self.middleware_factory = LearningMiddlewareFactory(
            self.learning_system, 
            self.memory_learning_system
        )
        
        logger.info("🧠 Learning system integrator initialized")
    
    async def enhance_swarm_with_middleware(
        self, 
        swarm: SwarmBase,
        middleware_type: str = "standard"
    ) -> SwarmBase:
        """Enhance existing swarm with learning middleware"""
        if not self.middleware_factory:
            raise RuntimeError("Learning integrator not initialized")
        
        # Create appropriate middleware chain
        if middleware_type == "lightweight":
            middleware_chain = self.middleware_factory.create_lightweight_middleware_chain()
        elif middleware_type == "research":
            middleware_chain = self.middleware_factory.create_research_middleware_chain()
        else:
            middleware_chain = self.middleware_factory.create_standard_middleware_chain()
        
        # Inject middleware into swarm
        enhanced_swarm = await inject_learning_middleware(swarm, middleware_chain)
        
        logger.info(f"✨ Enhanced swarm {swarm.config.swarm_id} with {middleware_type} learning middleware")
        return enhanced_swarm
    
    async def enhance_swarm_with_direct_integration(self, swarm: SwarmBase) -> SwarmBase:
        """Enhance swarm with direct learning integration"""
        if not self.learning_system:
            raise RuntimeError("Learning integrator not initialized")
        
        # Direct integration with learning-enhanced execution modes
        enhanced_swarm = await integrate_learning_with_swarm(swarm, self.learning_system)
        
        logger.info(f"🔗 Enhanced swarm {swarm.config.swarm_id} with direct learning integration")
        return enhanced_swarm
    
    async def cleanup(self):
        """Cleanup all learning components"""
        if self.learning_system:
            await self.learning_system.cleanup()
        if self.memory_learning_system:
            await self.memory_learning_system.cleanup()
        if self.message_bus:
            await self.message_bus.close()
        
        logger.info("🧹 Learning system integrator cleaned up")


# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

@dataclass
class LearningPerformanceMetrics:
    """Metrics for monitoring learning system performance"""
    swarm_id: str
    execution_count: int = 0
    avg_execution_time: float = 0.0
    avg_quality_improvement: float = 0.0
    knowledge_application_rate: float = 0.0
    learning_effectiveness: float = 0.0
    memory_usage_mb: float = 0.0
    
    def update(self, execution_result: Dict[str, Any]):
        """Update metrics with new execution result"""
        self.execution_count += 1
        
        # Update execution time
        execution_time = execution_result.get('execution_time', 0.0)
        self.avg_execution_time = (
            (self.avg_execution_time * (self.execution_count - 1) + execution_time) / 
            self.execution_count
        )
        
        # Update quality improvement
        quality_score = execution_result.get('quality_score', 0.0)
        baseline_quality = 0.6  # Assumed baseline
        quality_improvement = max(0, quality_score - baseline_quality)
        
        self.avg_quality_improvement = (
            (self.avg_quality_improvement * (self.execution_count - 1) + quality_improvement) /
            self.execution_count
        )


class LearningPerformanceMonitor:
    """Monitor learning system performance across multiple swarms"""
    
    def __init__(self):
        self.swarm_metrics: Dict[str, LearningPerformanceMetrics] = {}
        self.monitoring_start_time = time.time()
    
    def track_execution(self, swarm_id: str, execution_result: Dict[str, Any]):
        """Track execution result for performance monitoring"""
        if swarm_id not in self.swarm_metrics:
            self.swarm_metrics[swarm_id] = LearningPerformanceMetrics(swarm_id)
        
        self.swarm_metrics[swarm_id].update(execution_result)
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        total_executions = sum(m.execution_count for m in self.swarm_metrics.values())
        avg_quality_improvement = (
            sum(m.avg_quality_improvement for m in self.swarm_metrics.values()) /
            max(len(self.swarm_metrics), 1)
        )
        
        monitoring_duration = time.time() - self.monitoring_start_time
        
        return {
            'monitoring_duration_minutes': monitoring_duration / 60,
            'total_swarms_monitored': len(self.swarm_metrics),
            'total_executions': total_executions,
            'avg_quality_improvement': avg_quality_improvement,
            'swarm_details': {
                swarm_id: {
                    'execution_count': metrics.execution_count,
                    'avg_execution_time': metrics.avg_execution_time,
                    'avg_quality_improvement': metrics.avg_quality_improvement,
                    'learning_effectiveness': metrics.learning_effectiveness
                }
                for swarm_id, metrics in self.swarm_metrics.items()
            }
        }


# =============================================================================
# COMPLETE INTEGRATION EXAMPLES
# =============================================================================

async def example_middleware_integration():
    """Example: Integrating learning using middleware approach"""
    logger.info("🔧 Starting middleware integration example")
    
    # Create learning system integrator
    integrator = LearningSystemIntegrator()
    await integrator.initialize({
        'learning_rate': 0.1,
        'experience_buffer_size': 1000,
        'vector_dimension': 64
    })
    
    # Create standard swarm
    swarm_config = SwarmConfig(
        swarm_id="example-coding-swarm",
        swarm_type=SwarmType.CODING,
        execution_mode=SwarmExecutionMode.PARALLEL,
        agent_count=3,
        capabilities=[SwarmCapability.CODING, SwarmCapability.QUALITY_ASSURANCE]
    )
    
    # Create fake agents for demonstration
    fake_agents = [{'name': f'agent_{i}'} for i in range(3)]
    original_swarm = ExampleCodeGenerationSwarm(swarm_config, fake_agents)
    await original_swarm.initialize()
    
    # Enhance with learning middleware
    learning_swarm = await integrator.enhance_swarm_with_middleware(
        original_swarm, 
        middleware_type="standard"
    )
    
    # Test the learning-enhanced swarm
    test_problems = [
        {
            'type': 'coding',
            'description': 'Generate a sorting algorithm',
            'complexity': 'medium',
            'language': 'python'
        },
        {
            'type': 'coding',
            'description': 'Create a REST API endpoint',
            'complexity': 'high',
            'language': 'javascript'
        },
        {
            'type': 'coding',
            'description': 'Optimize database queries',
            'complexity': 'high',
            'language': 'sql'
        }
    ]
    
    results = []
    for i, problem in enumerate(test_problems):
        logger.info(f"🧪 Testing problem {i+1}: {problem['description']}")
        
        start_time = time.time()
        result = await learning_swarm.solve_problem(problem)
        execution_time = time.time() - start_time
        
        results.append({
            'problem': problem,
            'result': result,
            'execution_time': execution_time
        })
        
        logger.info(f"✅ Problem {i+1} completed in {execution_time:.2f}s (success: {result.success})")
    
    # Get learning insights
    learning_insights = await integrator.learning_system.get_learning_insights()
    memory_insights = await integrator.memory_learning_system.get_memory_insights()
    
    logger.info("📊 Learning System Insights:")
    logger.info(f"  Experiences collected: {learning_insights['metrics']['experiences_collected']}")
    logger.info(f"  Knowledge created: {learning_insights['metrics']['knowledge_created']}")
    logger.info(f"  Knowledge applied: {learning_insights['metrics']['knowledge_applied']}")
    logger.info(f"  Learning effectiveness: {learning_insights['metrics']['learning_effectiveness']:.2f}")
    
    logger.info("💾 Memory System Insights:")
    logger.info(f"  Knowledge graph size: {memory_insights['knowledge_graph_size']}")
    logger.info(f"  Vector index size: {memory_insights['vector_index_size']}")
    logger.info(f"  Working memory utilization: {memory_insights['working_memory_utilization']:.2%}")
    
    # Cleanup
    await integrator.cleanup()
    await original_swarm.cleanup()
    
    logger.info("🏁 Middleware integration example completed")
    return results


async def example_direct_integration():
    """Example: Direct integration with learning-enhanced execution modes"""
    logger.info("🔗 Starting direct integration example")
    
    # Initialize components
    memory_store = get_memory_store()
    message_bus = MessageBus()
    await message_bus.initialize()
    
    # Create learning system
    learning_system = await create_learning_system(memory_store, message_bus, config={
        'learning_rate': 0.15,  # Higher learning rate for direct integration
        'experience_buffer_size': 2000
    })
    
    # Create swarm
    swarm_config = SwarmConfig(
        swarm_id="direct-learning-swarm",
        swarm_type=SwarmType.STANDARD,
        execution_mode=SwarmExecutionMode.HIERARCHICAL,  # Test hierarchical learning
        agent_count=4
    )
    
    fake_agents = [{'name': f'agent_{i}'} for i in range(4)]
    original_swarm = ExampleCodeGenerationSwarm(swarm_config, fake_agents)
    await original_swarm.initialize()
    
    # Direct learning integration
    learning_swarm = await integrate_learning_with_swarm(original_swarm, learning_system)
    
    # Test with different execution modes to demonstrate cross-modal learning
    test_scenarios = [
        {'mode': SwarmExecutionMode.HIERARCHICAL, 'problem': 'complex architecture design'},
        {'mode': SwarmExecutionMode.PARALLEL, 'problem': 'parallel optimization tasks'},
        {'mode': SwarmExecutionMode.LINEAR, 'problem': 'sequential refactoring steps'},
    ]
    
    for scenario in test_scenarios:
        learning_swarm.config.execution_mode = scenario['mode']
        
        problem = {
            'type': 'coding',
            'description': scenario['problem'],
            'complexity': 'high'
        }
        
        logger.info(f"🧪 Testing {scenario['mode'].value} execution with learning")
        result = await learning_swarm.solve_problem(problem)
        logger.info(f"✅ {scenario['mode'].value} execution completed (success: {result.success})")
    
    # Get final insights
    insights = await learning_system.get_learning_insights()
    logger.info("📈 Final Learning Insights:")
    logger.info(f"  Total experiences: {insights['experience_buffer_size']}")
    logger.info(f"  Learning queue size: {insights['learning_queue_size']}")
    logger.info(f"  Recent activity rate: {insights['recent_activity']['success_rate_last_hour']:.2%}")
    
    # Cleanup
    await learning_system.cleanup()
    await message_bus.close()
    await original_swarm.cleanup()
    
    logger.info("🏁 Direct integration example completed")


async def example_performance_monitoring():
    """Example: Performance monitoring of learning-enhanced swarms"""
    logger.info("📊 Starting performance monitoring example")
    
    # Create performance monitor
    monitor = LearningPerformanceMonitor()
    
    # Initialize learning system
    integrator = LearningSystemIntegrator()
    await integrator.initialize({'learning_rate': 0.08})
    
    # Create multiple swarms for monitoring
    swarms = []
    for i in range(3):
        config = SwarmConfig(
            swarm_id=f"monitored-swarm-{i}",
            swarm_type=SwarmType.STANDARD,
            execution_mode=[SwarmExecutionMode.PARALLEL, SwarmExecutionMode.LINEAR, SwarmExecutionMode.DEBATE][i],
            agent_count=3 + i
        )
        
        fake_agents = [{'name': f'agent_{j}'} for j in range(3 + i)]
        swarm = ExampleCodeGenerationSwarm(config, fake_agents)
        await swarm.initialize()
        
        # Enhance with different middleware types
        middleware_types = ["lightweight", "standard", "research"]
        enhanced_swarm = await integrator.enhance_swarm_with_middleware(
            swarm, middleware_types[i]
        )
        
        swarms.append(enhanced_swarm)
    
    # Run multiple executions for each swarm
    problems = [
        {'type': 'coding', 'description': 'Simple function', 'complexity': 'low'},
        {'type': 'coding', 'description': 'Complex algorithm', 'complexity': 'high'},
        {'type': 'coding', 'description': 'System integration', 'complexity': 'medium'},
    ]
    
    for round_num in range(3):  # 3 rounds of execution
        logger.info(f"🔄 Execution round {round_num + 1}")
        
        for swarm in swarms:
            for problem in problems:
                start_time = time.time()
                result = await swarm.solve_problem(problem)
                execution_time = time.time() - start_time
                
                # Track performance
                execution_result = {
                    'execution_time': execution_time,
                    'quality_score': result.metadata.get('quality_score', 0.0) if result.metadata else 0.0,
                    'success': result.success
                }
                monitor.track_execution(swarm.config.swarm_id, execution_result)
    
    # Get performance report
    performance_report = await monitor.get_performance_report()
    
    logger.info("📈 Performance Monitoring Report:")
    logger.info(f"  Monitoring duration: {performance_report['monitoring_duration_minutes']:.1f} minutes")
    logger.info(f"  Total swarms monitored: {performance_report['total_swarms_monitored']}")
    logger.info(f"  Total executions: {performance_report['total_executions']}")
    logger.info(f"  Average quality improvement: {performance_report['avg_quality_improvement']:.3f}")
    
    for swarm_id, details in performance_report['swarm_details'].items():
        logger.info(f"  {swarm_id}:")
        logger.info(f"    Executions: {details['execution_count']}")
        logger.info(f"    Avg execution time: {details['avg_execution_time']:.2f}s")
        logger.info(f"    Avg quality improvement: {details['avg_quality_improvement']:.3f}")
    
    # Cleanup
    await integrator.cleanup()
    for swarm in swarms:
        await swarm.cleanup()
    
    logger.info("🏁 Performance monitoring example completed")


# =============================================================================
# MAIN DEMO RUNNER
# =============================================================================

async def main():
    """Run all integration examples"""
    logger.info("🚀 Starting Sophia Intel AI Learning System Integration Examples")
    
    try:
        # Run middleware integration example
        await example_middleware_integration()
        await asyncio.sleep(1)  # Brief pause between examples
        
        # Run direct integration example
        await example_direct_integration()
        await asyncio.sleep(1)
        
        # Run performance monitoring example
        await example_performance_monitoring()
        
        logger.info("✅ All integration examples completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Integration examples failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run examples
    asyncio.run(main())