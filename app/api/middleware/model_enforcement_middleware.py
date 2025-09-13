"""
Model Enforcement Middleware
Intercepts all API requests and enforces approved model usage
"""

import json
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from app.core.model_enforcement import model_enforcer

logger = logging.getLogger(__name__)

class ModelEnforcementMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Only intercept POST requests that might contain model specifications
        request = Request(scope, receive)
        
        if request.method == "POST" and any(endpoint in str(request.url) for endpoint in [
            "/chat", "/complete", "/generate", "/api/v1", "/openai", "/anthropic", "/v1/chat"
        ]):
            
            try:
                # Get request body
                body = await request.body()
                if body:
                    try:
                        payload = json.loads(body.decode())
                        
                        # Check for model parameter
                        if "model" in payload:
                            requested_model = payload["model"]
                            logger.info(f"Model enforcement check: {requested_model}")
                            
                            # Enforce model choice
                            try:
                                enforced_model = model_enforcer.enforce_model_choice(requested_model, fallback=True)
                                
                                if enforced_model != requested_model:
                                    logger.warning(f"Model replaced: {requested_model} -> {enforced_model}")
                                    payload["model"] = enforced_model
                                    
                                    # Update request body
                                    new_body = json.dumps(payload).encode()
                                    scope["_body"] = new_body
                                    
                            except ValueError as e:
                                # Model is blocked and no fallback allowed
                                logger.error(f"Model request blocked: {e}")
                                response = JSONResponse(
                                    status_code=400,
                                    content={
                                        "error": "model_not_approved",
                                        "message": str(e),
                                        "requested_model": requested_model,
                                        "approved_models": [model.name for model in model_enforcer.get_approved_models()]
                                    }
                                )
                                await response(scope, receive, send)
                                return
                                
                    except json.JSONDecodeError:
                        # Not JSON, continue
                        pass
                        
            except Exception as e:
                logger.error(f"Error in model enforcement middleware: {e}")
                # Continue processing on error
                pass

        # Continue to the application
        await self.app(scope, receive, send)


async def model_enforcement_middleware(request: Request, call_next: Callable) -> Response:
    """FastAPI middleware function for model enforcement"""
    
    # Only check POST requests that might contain LLM calls
    if request.method == "POST":
        try:
            # Get the raw body
            body = await request.body()
            
            if body:
                try:
                    payload = json.loads(body.decode())
                    
                    # Check for model parameter
                    if "model" in payload:
                        requested_model = payload["model"]
                        
                        # Validate the model
                        if not model_enforcer.is_model_approved(requested_model):
                            # Try to get replacement
                            try:
                                enforced_model = model_enforcer.enforce_model_choice(requested_model, fallback=True)
                                logger.warning(f"Model enforcement: {requested_model} -> {enforced_model}")
                                
                                # We can't easily modify the request body in FastAPI middleware
                                # So we'll log the enforcement but let the downstream handle it
                                
                            except ValueError as e:
                                # Block the request
                                return JSONResponse(
                                    status_code=400,
                                    content={
                                        "error": "model_not_approved", 
                                        "message": f"Model '{requested_model}' is not approved for use",
                                        "details": str(e),
                                        "approved_models": [model.name for model in model_enforcer.get_approved_models()]
                                    }
                                )
                                
                except json.JSONDecodeError:
                    pass  # Not JSON, continue
                    
        except Exception as e:
            logger.error(f"Model enforcement middleware error: {e}")
    
    # Continue processing
    response = await call_next(request)
    return response