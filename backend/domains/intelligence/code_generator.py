"""
AI Code Generator for SOPHIA Intel
Intelligent code generation and architecture adaptation
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AICodeGenerator:
    """AI-powered code generation system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.generation_history: List[Dict[str, Any]] = []
        
    async def generate_code(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate code based on request and context"""
        
        generation_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Extract request details
            code_type = request.get('type', 'general')
            requirements = request.get('requirements', [])
            language = request.get('language', 'python')
            
            # Generate code based on type
            if code_type == 'api_endpoint':
                generated_code = self._generate_api_endpoint(requirements, language)
            elif code_type == 'data_model':
                generated_code = self._generate_data_model(requirements, language)
            elif code_type == 'service_class':
                generated_code = self._generate_service_class(requirements, language)
            else:
                generated_code = self._generate_general_code(requirements, language)
            
            result = {
                'generation_id': generation_id,
                'code': generated_code,
                'language': language,
                'type': code_type,
                'status': 'success',
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'requirements_count': len(requirements),
                    'context_provided': bool(context)
                }
            }
            
            # Store in history
            self.generation_history.append(result)
            
            logger.info(f"✅ Code generation completed: {generation_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return {
                'generation_id': generation_id,
                'status': 'error',
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_api_endpoint(self, requirements: List[str], language: str) -> str:
        """Generate API endpoint code"""
        if language.lower() == 'python':
            return '''
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class RequestModel(BaseModel):
    data: dict

class ResponseModel(BaseModel):
    result: dict
    status: str

@router.post("/endpoint", response_model=ResponseModel)
async def generated_endpoint(request: RequestModel):
    """Generated API endpoint"""
    try:
        # Process request
        result = {"processed": True, "data": request.data}
        return ResponseModel(result=result, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
        return f"// Generated {language} API endpoint code"
    
    def _generate_data_model(self, requirements: List[str], language: str) -> str:
        """Generate data model code"""
        if language.lower() == 'python':
            return '''
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GeneratedModel(BaseModel):
    """Generated data model"""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Model name")
    data: dict = Field(default_factory=dict, description="Model data")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
'''
        return f"// Generated {language} data model code"
    
    def _generate_service_class(self, requirements: List[str], language: str) -> str:
        """Generate service class code"""
        if language.lower() == 'python':
            return '''
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GeneratedService:
    """Generated service class"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        
    async def initialize(self) -> None:
        """Initialize the service"""
        if self.initialized:
            return
            
        logger.info("Initializing generated service")
        self.initialized = True
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through the service"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Process the data
            result = {
                "processed_at": datetime.now().isoformat(),
                "input_data": data,
                "status": "processed"
            }
            
            logger.info("Data processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
'''
        return f"// Generated {language} service class code"
    
    def _generate_general_code(self, requirements: List[str], language: str) -> str:
        """Generate general purpose code"""
        return f"""
# Generated {language} code
# Requirements: {', '.join(requirements)}

def generated_function():
    \"\"\"Generated function based on requirements\"\"\"
    return {{"status": "generated", "language": "{language}"}}

if __name__ == "__main__":
    result = generated_function()
    print(f"Generated code result: {{result}}")
"""
    
    def get_generation_history(self) -> List[Dict[str, Any]]:
        """Get code generation history"""
        return self.generation_history
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        total_generations = len(self.generation_history)
        successful_generations = len([g for g in self.generation_history if g.get('status') == 'success'])
        
        return {
            'total_generations': total_generations,
            'successful_generations': successful_generations,
            'success_rate': successful_generations / total_generations if total_generations > 0 else 0,
            'languages_used': list(set(g.get('language', 'unknown') for g in self.generation_history)),
            'types_generated': list(set(g.get('type', 'unknown') for g in self.generation_history))
        }

