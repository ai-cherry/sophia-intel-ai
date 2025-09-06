"""
FastAPI Routes for Swarm Template Management
Provides endpoints for listing, generating, validating, deploying and monitoring swarms
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.swarms.templates.swarm_generator import swarm_code_generator
from app.swarms.templates.swarm_templates import (
    SwarmTemplate,
    SwarmTopology,
    TemplateCategory,
    TemplateDomain,
    swarm_template_catalog,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================


class TemplateListRequest(BaseModel):
    domain: Optional[TemplateDomain] = None
    category: Optional[TemplateCategory] = None
    topology: Optional[SwarmTopology] = None
    pay_ready_only: bool = False
    max_complexity: int = Field(5, ge=1, le=5)


class CodeGenerationRequest(BaseModel):
    template_id: str
    swarm_name: Optional[str] = None
    custom_config: Dict[str, Any] = Field(default_factory=dict)
    save_to_file: bool = False


class SwarmDeploymentRequest(BaseModel):
    template_id: str
    swarm_name: str
    custom_config: Dict[str, Any] = Field(default_factory=dict)
    agent_overrides: Dict[str, Any] = Field(default_factory=dict)
    auto_deploy: bool = False
    monitoring_enabled: bool = True
    notifications_enabled: bool = True


class SwarmStatusRequest(BaseModel):
    swarm_id: str


class TemplateValidationRequest(BaseModel):
    template_id: str
    custom_config: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# RESPONSE MODELS
# ==============================================================================


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    topology: str
    domain: str
    category: str
    agent_count: int
    estimated_duration: str
    complexity_level: int
    pay_ready_optimized: bool
    resource_limits: Dict[str, Any]
    success_criteria: Dict[str, Any]
    example_use_cases: List[str]


class CodeGenerationResponse(BaseModel):
    success: bool
    code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


class DeploymentResponse(BaseModel):
    success: bool
    swarm_id: Optional[str] = None
    deployment_status: str
    metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)


class SwarmStatusResponse(BaseModel):
    swarm_id: str
    status: str
    metadata: Dict[str, Any]
    created_at: str
    last_updated: str


# ==============================================================================
# GLOBAL STATE
# ==============================================================================

# Track active swarm deployments
active_deployments: Dict[str, Dict[str, Any]] = {}
websocket_connections: List[WebSocket] = []

# ==============================================================================
# ROUTER SETUP
# ==============================================================================

router = APIRouter(prefix="/api/swarm-templates", tags=["swarm-templates"])

# ==============================================================================
# TEMPLATE MANAGEMENT ENDPOINTS
# ==============================================================================


@router.get("/list", response_model=List[TemplateResponse])
async def list_templates(
    domain: Optional[str] = None,
    category: Optional[str] = None,
    topology: Optional[str] = None,
    pay_ready_only: bool = False,
    max_complexity: int = 5,
):
    """List available swarm templates with optional filtering"""
    try:
        # Convert string parameters to enums if provided
        domain_filter = TemplateDomain(domain) if domain else None
        category_filter = TemplateCategory(category) if category else None
        topology_filter = SwarmTopology(topology) if topology else None

        # Get filtered templates
        if pay_ready_only:
            templates = [
                t for t in swarm_template_catalog.list_templates() if t.pay_ready_optimized
            ]
        else:
            templates = swarm_template_catalog.list_templates(
                domain=domain_filter, category=category_filter, topology=topology_filter
            )

        # Apply complexity filter
        templates = [t for t in templates if t.complexity_level <= max_complexity]

        # Convert to response format
        response_templates = []
        for template in templates:
            response_templates.append(
                TemplateResponse(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    topology=template.topology.value,
                    domain=template.domain.value,
                    category=template.category.value,
                    agent_count=len(template.agents),
                    estimated_duration=template.estimated_duration,
                    complexity_level=template.complexity_level,
                    pay_ready_optimized=template.pay_ready_optimized,
                    resource_limits=template.resource_limits,
                    success_criteria=template.success_criteria,
                    example_use_cases=template.example_use_cases,
                )
            )

        logger.info(f"Listed {len(response_templates)} templates")
        return response_templates

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.get("/template/{template_id}")
async def get_template(template_id: str):
    """Get detailed information about a specific template"""
    try:
        template = swarm_template_catalog.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

        return {
            "template": TemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                topology=template.topology.value,
                domain=template.domain.value,
                category=template.category.value,
                agent_count=len(template.agents),
                estimated_duration=template.estimated_duration,
                complexity_level=template.complexity_level,
                pay_ready_optimized=template.pay_ready_optimized,
                resource_limits=template.resource_limits,
                success_criteria=template.success_criteria,
                example_use_cases=template.example_use_cases,
            ),
            "agents": [
                {
                    "template_name": agent.template_name,
                    "role": agent.role,
                    "factory_type": agent.factory_type,
                    "weight": agent.weight,
                    "required": agent.required,
                    "custom_config": agent.custom_config,
                }
                for agent in template.agents
            ],
            "coordination_config": template.coordination_config,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")


@router.get("/summary")
async def get_template_summary():
    """Get summary statistics about available templates"""
    try:
        summary = swarm_template_catalog.get_template_summary()
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get template summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template summary")


# ==============================================================================
# CODE GENERATION ENDPOINTS
# ==============================================================================


@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_swarm_code(request: CodeGenerationRequest):
    """Generate Python code from a swarm template"""
    try:
        # Validate and generate code
        success, code, metadata, errors = swarm_code_generator.validate_and_generate(
            template_id=request.template_id,
            custom_config=request.custom_config,
            swarm_name=request.swarm_name,
        )

        if not success:
            return CodeGenerationResponse(success=False, errors=errors)

        file_path = None
        if request.save_to_file:
            try:
                file_path = swarm_code_generator.save_generated_swarm(
                    swarm_name=metadata["swarm_name"], code=code, metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to save generated code: {e}")
                errors.append(f"Failed to save code: {str(e)}")

        return CodeGenerationResponse(
            success=True, code=code, metadata=metadata, file_path=file_path, errors=errors
        )

    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return CodeGenerationResponse(success=False, errors=[f"Code generation failed: {str(e)}"])


@router.post("/validate", response_model=Dict[str, Any])
async def validate_template_configuration(request: TemplateValidationRequest):
    """Validate template configuration without generating code"""
    try:
        template = swarm_template_catalog.get_template(request.template_id)
        if not template:
            raise HTTPException(
                status_code=404, detail=f"Template '{request.template_id}' not found"
            )

        # Validate template itself
        is_valid, errors = swarm_template_catalog.validate_template(template)

        # Additional validation for custom config
        validation_results = {
            "template_valid": is_valid,
            "template_errors": errors,
            "resource_compliance": True,
            "configuration_issues": [],
        }

        # Check resource limits
        max_tasks = template.resource_limits.get("max_concurrent_tasks", 8)
        if max_tasks > 8:
            validation_results["resource_compliance"] = False
            validation_results["configuration_issues"].append(
                f"Template requests {max_tasks} concurrent tasks, system limit is 8"
            )

        # Validate custom config structure
        if request.custom_config:
            try:
                # Basic JSON validation (already done by Pydantic, but double-check)
                json.dumps(request.custom_config)
            except Exception as e:
                validation_results["configuration_issues"].append(
                    f"Invalid custom config: {str(e)}"
                )

        overall_valid = (
            validation_results["template_valid"]
            and validation_results["resource_compliance"]
            and not validation_results["configuration_issues"]
        )

        return {
            "success": True,
            "valid": overall_valid,
            "validation_results": validation_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail="Validation failed")


# ==============================================================================
# DEPLOYMENT ENDPOINTS
# ==============================================================================


@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_swarm(request: SwarmDeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy a swarm from template configuration"""
    try:
        # Generate unique deployment ID
        deployment_id = f"deploy_{request.template_id}_{uuid4().hex[:8]}"

        # Validate template exists
        template = swarm_template_catalog.get_template(request.template_id)
        if not template:
            return DeploymentResponse(
                success=False,
                deployment_status="template_not_found",
                errors=[f"Template '{request.template_id}' not found"],
            )

        # Validate configuration
        is_valid, errors = swarm_code_generator.validate_and_generate(
            template_id=request.template_id,
            custom_config=request.custom_config,
            swarm_name=request.swarm_name,
        )[
            :2
        ]  # Only get success and errors

        if not is_valid:
            return DeploymentResponse(
                success=False, deployment_status="validation_failed", errors=errors
            )

        # Create deployment record
        deployment_metadata = {
            "deployment_id": deployment_id,
            "template_id": request.template_id,
            "swarm_name": request.swarm_name,
            "status": "initializing",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "auto_deploy": request.auto_deploy,
            "monitoring_enabled": request.monitoring_enabled,
            "notifications_enabled": request.notifications_enabled,
            "custom_config": request.custom_config,
            "agent_overrides": request.agent_overrides,
        }

        active_deployments[deployment_id] = deployment_metadata

        # Schedule background deployment
        background_tasks.add_task(execute_deployment, deployment_id, request)

        return DeploymentResponse(
            success=True,
            swarm_id=deployment_id,
            deployment_status="initializing",
            metadata=deployment_metadata,
        )

    except Exception as e:
        logger.error(f"Deployment initiation failed: {e}")
        return DeploymentResponse(
            success=False,
            deployment_status="initialization_failed",
            errors=[f"Deployment failed: {str(e)}"],
        )


async def execute_deployment(deployment_id: str, request: SwarmDeploymentRequest):
    """Background task to execute swarm deployment"""
    try:
        # Update status
        active_deployments[deployment_id]["status"] = "generating_code"
        await broadcast_deployment_update(deployment_id, "generating_code")

        # Generate code
        success, code, metadata, errors = swarm_code_generator.validate_and_generate(
            template_id=request.template_id,
            custom_config=request.custom_config,
            swarm_name=request.swarm_name,
        )

        if not success:
            active_deployments[deployment_id]["status"] = "code_generation_failed"
            active_deployments[deployment_id]["errors"] = errors
            await broadcast_deployment_update(deployment_id, "code_generation_failed")
            return

        # Save generated code
        active_deployments[deployment_id]["status"] = "saving_code"
        await broadcast_deployment_update(deployment_id, "saving_code")

        file_path = swarm_code_generator.save_generated_swarm(
            swarm_name=request.swarm_name, code=code, metadata=metadata
        )

        active_deployments[deployment_id]["file_path"] = file_path
        active_deployments[deployment_id]["code_metadata"] = metadata

        if request.auto_deploy:
            # Simulate actual deployment (would integrate with real deployment system)
            active_deployments[deployment_id]["status"] = "deploying"
            await broadcast_deployment_update(deployment_id, "deploying")

            # Simulate deployment time
            await asyncio.sleep(5)

            active_deployments[deployment_id]["status"] = "deployed"
            active_deployments[deployment_id]["deployed_at"] = datetime.now(
                timezone.utc
            ).isoformat()
        else:
            active_deployments[deployment_id]["status"] = "ready_for_deployment"

        # Final status update
        await broadcast_deployment_update(
            deployment_id, active_deployments[deployment_id]["status"]
        )

        logger.info(f"Deployment {deployment_id} completed successfully")

    except Exception as e:
        logger.error(f"Deployment {deployment_id} failed: {e}")
        active_deployments[deployment_id]["status"] = "deployment_failed"
        active_deployments[deployment_id]["error"] = str(e)
        await broadcast_deployment_update(deployment_id, "deployment_failed")


@router.get("/deployment/{deployment_id}/status", response_model=SwarmStatusResponse)
async def get_deployment_status(deployment_id: str):
    """Get status of a swarm deployment"""
    try:
        if deployment_id not in active_deployments:
            raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

        deployment = active_deployments[deployment_id]

        return SwarmStatusResponse(
            swarm_id=deployment_id,
            status=deployment["status"],
            metadata=deployment,
            created_at=deployment["created_at"],
            last_updated=deployment.get("last_updated", deployment["created_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get deployment status")


@router.get("/deployments")
async def list_deployments():
    """List all active deployments"""
    try:
        deployments = []
        for deployment_id, deployment in active_deployments.items():
            deployments.append(
                {
                    "deployment_id": deployment_id,
                    "swarm_name": deployment["swarm_name"],
                    "template_id": deployment["template_id"],
                    "status": deployment["status"],
                    "created_at": deployment["created_at"],
                }
            )

        return {
            "success": True,
            "deployments": deployments,
            "total": len(deployments),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list deployments")


# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================


@router.websocket("/ws/deployments")
async def deployment_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time deployment updates"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        # Send initial deployment status
        initial_status = {
            "type": "deployment_list",
            "deployments": [
                {"deployment_id": dep_id, "status": dep["status"], "swarm_name": dep["swarm_name"]}
                for dep_id, dep in active_deployments.items()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_json(initial_status)

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back for keepalive
            await websocket.send_json(
                {"type": "keepalive", "timestamp": datetime.now(timezone.utc).isoformat()}
            )

    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


async def broadcast_deployment_update(deployment_id: str, status: str):
    """Broadcast deployment status update to all connected WebSocket clients"""
    if not websocket_connections:
        return

    update = {
        "type": "deployment_update",
        "deployment_id": deployment_id,
        "status": status,
        "metadata": active_deployments.get(deployment_id, {}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Update last_updated timestamp
    if deployment_id in active_deployments:
        active_deployments[deployment_id]["last_updated"] = update["timestamp"]

    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(update)
        except Exception:
            disconnected.append(websocket)

    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)


# ==============================================================================
# UTILITY ENDPOINTS
# ==============================================================================


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "templates_available": len(swarm_template_catalog.templates),
        "active_deployments": len(active_deployments),
        "websocket_connections": len(websocket_connections),
    }


@router.delete("/deployment/{deployment_id}")
async def cancel_deployment(deployment_id: str):
    """Cancel an active deployment"""
    try:
        if deployment_id not in active_deployments:
            raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

        deployment = active_deployments[deployment_id]

        if deployment["status"] in ["deployed", "deployment_failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel deployment in status '{deployment['status']}'",
            )

        # Update status
        active_deployments[deployment_id]["status"] = "cancelled"
        active_deployments[deployment_id]["cancelled_at"] = datetime.now(timezone.utc).isoformat()

        await broadcast_deployment_update(deployment_id, "cancelled")

        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "cancelled",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel deployment: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel deployment")
