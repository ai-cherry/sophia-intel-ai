"""
Enhanced Swarm Multi-Agent System with Advanced LLM Integration
Linear deterministic workflow: architect → builder → tester → operator
Now with intelligent model selection, performance tracking, and cost optimization
"""
import asyncio
import json
import time
import os
from typing import Dict, List, Any, Optional
from loguru import logger

from .ai_integration import EnhancedAIIntegration, SwarmStage
from rag.pipeline import get_rag_pipeline


class SwarmWorkflowStage:
    """Enhanced base class for Swarm workflow stages with AI integration"""
    
    def __init__(self, name: str, stage_enum: SwarmStage):
        self.name = name
        self.stage_enum = stage_enum
        self.ai_integration = None
        self.rag_pipeline = None
        self.stage_context = {}
        self.performance_metrics = {
            "executions": 0,
            "successes": 0,
            "avg_execution_time": 0.0,
            "total_cost": 0.0
        }
    
    async def _get_ai_integration(self):
        """Get or initialize the enhanced AI integration"""
        if self.ai_integration is None:
            self.ai_integration = EnhancedAIIntegration()
        return self.ai_integration
    
    async def _get_rag_pipeline(self):
        """Get or initialize the RAG pipeline"""
        if self.rag_pipeline is None:
            self.rag_pipeline = await get_rag_pipeline()
        return self.rag_pipeline
    
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this stage of the workflow with enhanced AI capabilities"""
        logger.info(f"[{self.name}] Starting enhanced stage execution")
        start_time = time.time()
        
        try:
            # Update performance tracking
            self.performance_metrics["executions"] += 1
            
            # Get RAG pipeline and enhance context
            rag_pipeline = await self._get_rag_pipeline()
            rag_results = await rag_pipeline.search_multi_service(
                query=task,
                swarm_stage=self.name
            )
            
            # Prepare enhanced context
            enhanced_context = {
                **context,
                "rag_results": rag_results,
                "stage": self.name,
                "timestamp": time.time(),
                "stage_metrics": self.performance_metrics.copy()
            }
            
            # Check for stage-specific model override
            override_model = os.getenv(f"SWARM_{self.name.upper()}_MODEL")
            
            # Get AI integration and execute with intelligent model selection
            ai_integration = await self._get_ai_integration()
            
            # Set stage-specific environment context
            os.environ["SWARM_CURRENT_AGENT"] = self.name
            
            result = await ai_integration.invoke(
                task=task,
                context=enhanced_context,
                stage=self.name,
                override_model=override_model
            )
            
            execution_time = time.time() - start_time
            
            # Update success metrics
            self.performance_metrics["successes"] += 1
            self._update_performance_metrics(execution_time, success=True)
            
            logger.info(f"[{self.name}] Enhanced stage completed successfully in {execution_time:.2f}s")
            
            return {
                "success": True,
                "stage": self.name,
                "result": result.content if hasattr(result, 'content') else str(result),
                "context": enhanced_context,
                "execution_time": execution_time,
                "ai_metrics": ai_integration.get_performance_summary()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, success=False)
            
            logger.error(f"[{self.name}] Enhanced stage failed: {e}")
            return {
                "success": False,
                "stage": self.name,
                "error": str(e),
                "context": context,
                "execution_time": execution_time
            }
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update stage performance metrics"""
        total_executions = self.performance_metrics["executions"]
        current_avg = self.performance_metrics["avg_execution_time"]
        
        # Update average execution time
        self.performance_metrics["avg_execution_time"] = (
            (current_avg * (total_executions - 1) + execution_time) / total_executions
        )
        
        # Estimate and track cost (rough approximation)
        estimated_cost = execution_time * 0.001  # Very rough estimate
        self.performance_metrics["total_cost"] += estimated_cost
    
    def get_stage_summary(self) -> Dict[str, Any]:
        """Get summary of stage performance"""
        success_rate = 0.0
        if self.performance_metrics["executions"] > 0:
            success_rate = self.performance_metrics["successes"] / self.performance_metrics["executions"]
        
        return {
            "stage": self.name,
            "executions": self.performance_metrics["executions"],
            "success_rate": success_rate,
            "avg_execution_time": self.performance_metrics["avg_execution_time"],
            "total_cost": self.performance_metrics["total_cost"]
        }


class ArchitectStage(SwarmWorkflowStage):
    """Enhanced Architect stage - Plans and designs solutions with advanced reasoning models"""
    
    def __init__(self):
        super().__init__("architect", SwarmStage.ARCHITECT)


class BuilderStage(SwarmWorkflowStage):
    """Enhanced Builder stage - Implements solutions with code-specialized models"""
    
    def __init__(self):
        super().__init__("builder", SwarmStage.BUILDER)


class TesterStage(SwarmWorkflowStage):
    """Enhanced Tester stage - Tests and validates with code analysis models"""
    
    def __init__(self):
        super().__init__("tester", SwarmStage.TESTER)


class OperatorStage(SwarmWorkflowStage):
    """Enhanced Operator stage - Deploys and documents with efficient models"""
    
    def __init__(self):
        super().__init__("operator", SwarmStage.OPERATOR)


class EnhancedSwarmOrchestrator:
    """
    Enhanced Swarm orchestrator with advanced AI integration
    
    Features:
    - Intelligent model selection per stage
    - Performance tracking and optimization
    - Cost monitoring and control
    - Circuit breaker patterns
    - Adaptive model weights
    - Comprehensive telemetry
    """
    
    def __init__(self):
        self.ai_integration = EnhancedAIIntegration()
        
        # Initialize enhanced workflow stages
        self.stages = [
            ArchitectStage(),
            BuilderStage(),
            TesterStage(),
            OperatorStage()
        ]
        
        # Enhanced configuration
        self.config = {
            "max_hops": int(os.getenv("SWARM_MAX_HOPS", "12")),
            "max_timeout": int(os.getenv("SWARM_MAX_TIMEOUT", "600")),  # 10 minutes
            "max_errors": int(os.getenv("SWARM_MAX_ERRORS", "3")),
            "max_total_cost": float(os.getenv("SWARM_MAX_TOTAL_COST", "2.00")),
            "enable_cost_tracking": os.getenv("SWARM_ENABLE_COST_TRACKING", "1") == "1",
            "enable_performance_logging": os.getenv("SWARM_ENABLE_PERF_LOGGING", "1") == "1"
        }
        
        # Workflow metrics
        self.workflow_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "total_cost": 0.0,
            "avg_workflow_time": 0.0,
            "stage_performance": {}
        }
    
    async def initialize(self):
        """Initialize the enhanced Swarm system"""
        logger.info("Initializing Enhanced Swarm system with advanced AI integration")
        
        try:
            # Load any existing metrics
            self._load_workflow_metrics()
            
            logger.info("Enhanced Swarm system initialized successfully")
            logger.info(f"Available models: {len(self.ai_integration.registry.models)}")
            logger.info(f"Configuration: {self.config}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Swarm system: {e}")
            return False
    
    async def execute_workflow(self, task: str) -> Dict[str, Any]:
        """Execute the complete enhanced Swarm workflow"""
        logger.info(f"Starting Enhanced Swarm workflow for task: {task}")
        
        start_time = time.time()
        workflow_id = f"swarm_{int(time.time())}_{hash(task) % 10000}"
        
        workflow_context = {
            "original_task": task,
            "workflow_id": workflow_id,
            "start_time": start_time,
            "stage_results": [],
            "total_cost": 0.0,
            "config": self.config.copy()
        }
        
        errors = 0
        current_cost = 0.0
        
        # Update workflow metrics
        self.workflow_metrics["total_workflows"] += 1
        
        try:
            # Execute each stage in sequence with enhanced monitoring
            for i, stage in enumerate(self.stages):
                stage_start_time = time.time()
                
                # Check timeout
                if time.time() - start_time > self.config["max_timeout"]:
                    raise TimeoutError(f"Workflow timeout after {self.config['max_timeout']}s")
                
                # Check error limit
                if errors >= self.config["max_errors"]:
                    raise RuntimeError(f"Max errors ({self.config['max_errors']}) exceeded")
                
                # Check cost limit
                if current_cost > self.config["max_total_cost"]:
                    raise RuntimeError(f"Max cost (${self.config['max_total_cost']}) exceeded")
                
                logger.info(f"Executing stage {i+1}/{len(self.stages)}: {stage.name}")
                
                # Execute stage with enhanced context
                stage_result = await stage.execute(task, workflow_context)
                workflow_context["stage_results"].append(stage_result)
                
                # Track costs and performance
                stage_time = time.time() - stage_start_time
                if stage_result.get("success"):
                    # Extract cost information if available
                    ai_metrics = stage_result.get("ai_metrics", {})
                    stage_cost = ai_metrics.get("total_cost", stage_time * 0.001)  # Rough estimate
                    current_cost += stage_cost
                    workflow_context["total_cost"] = current_cost
                    
                    # Update context with results for next stages
                    if "result" in stage_result:
                        workflow_context[f"{stage.name}_result"] = stage_result["result"]
                    
                    logger.info(f"Stage {stage.name} completed successfully "
                               f"(${stage_cost:.4f}, {stage_time:.2f}s)")
                else:
                    errors += 1
                    logger.warning(f"Stage {stage.name} failed, error count: {errors}")
                    
                    # For critical failures in architect stage, abort early
                    if stage.name == "architect" and errors >= 2:
                        logger.error("Architect stage failed multiple times, aborting workflow")
                        break
                
                # Log intermediate progress
                if self.config["enable_performance_logging"]:
                    self._log_stage_completion(workflow_id, stage, stage_result, stage_time)
            
            # Calculate final results
            execution_time = time.time() - start_time
            successful_stages = sum(1 for result in workflow_context["stage_results"] 
                                  if result.get("success"))
            
            # Determine overall success (allow some flexibility)
            min_required_stages = max(1, len(self.stages) - 1)  # Allow 1 failure
            overall_success = successful_stages >= min_required_stages
            
            # Update metrics
            if overall_success:
                self.workflow_metrics["successful_workflows"] += 1
            
            self._update_workflow_metrics(execution_time, current_cost)
            
            # Prepare final result (JSON serializable)
            final_result = {
                "success": overall_success,
                "workflow_id": workflow_id,
                "task": task,
                "execution_time": execution_time,
                "stages_completed": successful_stages,
                "total_stages": len(self.stages),
                "errors": errors,
                "total_cost": current_cost,
                "stage_results": self._make_serializable(workflow_context["stage_results"]),
                "ai_integration_summary": self._summarize_ai_metrics(),
                "workflow_metrics": self.workflow_metrics.copy()
            }
            
            # Add final output from the last successful stage
            if overall_success:
                # Try to get output from operator -> tester -> builder -> architect
                for stage_name in ["operator", "tester", "builder", "architect"]:
                    if workflow_context.get(f"{stage_name}_result"):
                        final_result["output"] = workflow_context[f"{stage_name}_result"]
                        break
            
            # Save metrics periodically
            if self.workflow_metrics["total_workflows"] % 10 == 0:
                self._save_workflow_metrics()
            
            logger.info(f"Enhanced Swarm workflow completed: "
                       f"{'SUCCESS' if overall_success else 'FAILED'} "
                       f"({successful_stages}/{len(self.stages)} stages, "
                       f"${current_cost:.4f}, {execution_time:.2f}s)")
            
            return final_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Enhanced Swarm workflow failed: {e}")
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "task": task,
                "error": str(e),
                "execution_time": execution_time,
                "errors": errors,
                "total_cost": current_cost,
                "stage_results": self._make_serializable(workflow_context.get("stage_results", [])),
                "partial_results": True
            }
    
    def _update_workflow_metrics(self, execution_time: float, cost: float):
        """Update overall workflow metrics"""
        total_workflows = self.workflow_metrics["total_workflows"]
        current_avg = self.workflow_metrics["avg_workflow_time"]
        
        # Update average execution time
        self.workflow_metrics["avg_workflow_time"] = (
            (current_avg * (total_workflows - 1) + execution_time) / total_workflows
        )
        
        # Update total cost
        self.workflow_metrics["total_cost"] += cost
    
    def _log_stage_completion(self, workflow_id: str, stage: SwarmWorkflowStage, 
                             result: Dict[str, Any], execution_time: float):
        """Log stage completion for telemetry"""
        try:
            log_data = {
                "timestamp": time.time(),
                "workflow_id": workflow_id,
                "stage": stage.name,
                "success": result.get("success", False),
                "execution_time": execution_time,
                "error": result.get("error"),
                "event_type": "stage_completion"
            }
            
            # Write to stage log
            log_file = os.getenv("SWARM_STAGE_LOG_FILE", ".swarm_stages.log")
            with open(log_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")
                
        except Exception as e:
            logger.warning(f"Failed to log stage completion: {e}")
    
    def _load_workflow_metrics(self):
        """Load workflow metrics from disk"""
        try:
            metrics_file = os.getenv("SWARM_METRICS_FILE", ".swarm_workflow_metrics.json")
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    self.workflow_metrics.update(saved_metrics)
                    logger.info(f"Loaded workflow metrics: {saved_metrics}")
        except Exception as e:
            logger.warning(f"Failed to load workflow metrics: {e}")
    
    def _save_workflow_metrics(self):
        """Save workflow metrics to disk"""
        try:
            metrics_file = os.getenv("SWARM_METRICS_FILE", ".swarm_workflow_metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump(self.workflow_metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow metrics: {e}")
    
    def _make_serializable(self, obj: Any, _seen=None) -> Any:
        """Make object JSON serializable by removing circular references"""
        if _seen is None:
            _seen = set()
        
        # Prevent infinite recursion
        obj_id = id(obj)
        if obj_id in _seen:
            return "<circular_reference>"
        
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            _seen.add(obj_id)
            result = {}
            for k, v in obj.items():
                if k in ['ai_integration', 'rag_pipeline', 'session', 'client_manager']:
                    continue  # Skip objects that might have circular refs
                try:
                    result[k] = self._make_serializable(v, _seen)
                except (TypeError, ValueError, RecursionError):
                    result[k] = str(type(v).__name__)  # Just show the type name
            _seen.remove(obj_id)
            return result
        elif isinstance(obj, (list, tuple)):
            _seen.add(obj_id)
            result = [self._make_serializable(item, _seen) for item in obj[:10]]  # Limit to 10 items
            _seen.remove(obj_id)
            return result
        else:
            return str(type(obj).__name__)  # Just return the type name for complex objects
    
    def _summarize_ai_metrics(self) -> Dict[str, Any]:
        """Get summarized AI metrics that are JSON serializable"""
        try:
            full_metrics = self.ai_integration.get_performance_summary()
            return {
                "total_models": full_metrics.get("total_models", 0),
                "available_models": full_metrics.get("available_models", 0),
                "total_requests": full_metrics.get("total_requests", 0),
                "total_cost": full_metrics.get("total_cost", 0.0),
                "avg_success_rate": full_metrics.get("avg_success_rate", 0.0)
            }
        except Exception:
            return {"error": "metrics_unavailable"}

    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get comprehensive system summary"""
        return {
            "workflow_metrics": self.workflow_metrics,
            "ai_integration_summary": self._summarize_ai_metrics(),
            "stage_summaries": [stage.get_stage_summary() for stage in self.stages],
            "configuration": self.config,
            "system_status": "operational"
        }


# Global orchestrator instance
_orchestrator = None

async def get_orchestrator():
    """Get or create the global enhanced orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancedSwarmOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator

def run(task: str) -> Dict[str, Any]:
    """
    Enhanced main entry point for Swarm workflow execution
    Now with advanced AI integration and intelligent model selection
    """
    logger.info(f"Enhanced Swarm run initiated for task: {task}")
    
    try:
        # Create new event loop for synchronous call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get orchestrator and run workflow
            orchestrator = loop.run_until_complete(get_orchestrator())
            result = loop.run_until_complete(orchestrator.execute_workflow(task))
            
            logger.info(f"Enhanced Swarm run completed: success={result.get('success', False)}, "
                       f"cost=${result.get('total_cost', 0.0):.4f}")
            
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Enhanced Swarm run failed: {e}")
        return {
            "success": False,
            "task": task,
            "error": str(e),
            "timestamp": time.time(),
            "enhanced": True
        }

# For backwards compatibility and async usage
async def run_async(task: str) -> Dict[str, Any]:
    """Enhanced async version of the run function"""
    orchestrator = await get_orchestrator()
    return await orchestrator.execute_workflow(task)


# Utility functions for monitoring and management
def get_system_status() -> Dict[str, Any]:
    """Get current system status"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            orchestrator = loop.run_until_complete(get_orchestrator())
            return orchestrator.get_comprehensive_summary()
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "status": "error"}

def reset_metrics():
    """Reset all performance metrics"""
    global _orchestrator
    if _orchestrator:
        _orchestrator.workflow_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "total_cost": 0.0,
            "avg_workflow_time": 0.0,
            "stage_performance": {}
        }
        logger.info("Swarm metrics reset")
