from typing import Dict, Any, List, Optional
import re
import bleach
from pydantic import BaseModel, validator

class InputValidator:
    """Advanced input validation and sanitization system"""
    
    @staticmethod
    def validate_code_input(code: str) -> str:
        """Sanitize code input while preserving valid syntax"""
        # Prevent potential injection points
        safe_code = bleach.clean(
            code,
            tags=['code', 'pre', 'div'],
            attributes={'*': ['class']},
            styles=['color', 'background-color']
        )
        
        # Validate that code contains actual content (not just whitespace)
        if not safe_code.strip():
            raise ValueError("Code input cannot be empty")
            
        return safe_code
    
    @staticmethod
    def validate_api_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize API input parameters"""
        # Sanitize user inputs
        if 'prompt' in params and isinstance(params['prompt'], str):
            params['prompt'] = bleach.clean(
                params['prompt'],
                tags=[],
                attributes={},
                styles=[]
            )
        
        if 'query' in params and isinstance(params['query'], str):
            params['query'] = bleach.clean(
                params['query'],
                tags=[],
                attributes={},
                styles=[]
            )
        
        # Validate required parameters
        if 'model' not in params or not isinstance(params['model'], str):
            raise ValueError("Missing or invalid 'model' parameter")
        
        # Validate numerical constraints
        if 'temperature' in params and not (0.0 <= params['temperature'] <= 2.0):
            params['temperature'] = min(2.0, max(0.0, params['temperature']))
        
        return params

class SchemaValidator(BaseModel):
    """Pydantic model for API schema validation"""
    prompt: str
    model: str = "llama3.2:3b"
    temperature: float = 0.7
    max_tokens: int = 256

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 2.0:
            raise ValueError('Temperature must be between 0 and 2')
        return v
