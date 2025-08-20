#!/usr/bin/env python3
"""
SOPHIA V4 MCP Integration
Real MCP server functionality integrated into main SOPHIA system
"""

import os
import json
import hashlib
import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Best models for different tasks
CODING_MODELS = [
    "qwen/qwen3-coder",
    "openai/gpt-4o",
    "anthropic/claude-3.5-sonnet-20241022"
]

# In-memory storage (production would use Neon database)
code_index = {}
security_scans = {}
analytics_data = {}

class MCPServices:
    """Real MCP Services for SOPHIA V4"""
    
    @staticmethod
    async def generate_code(prompt: str, language: str = "python", model: str = None) -> Dict[str, Any]:
        """Generate code using OpenRouter"""
        try:
            if not OPENROUTER_API_KEY:
                return {"error": "OpenRouter API key not configured", "success": False}
            
            if not model or model not in CODING_MODELS:
                model = CODING_MODELS[0]
            
            system_prompt = f"""You are an expert {language} developer. Generate clean, production-ready code.

Guidelines:
- Write clear, readable code with proper comments
- Follow best practices for {language}
- Include error handling where appropriate
- Add docstrings/comments explaining the code
- Ensure code is secure and efficient
- Return only the code, no explanations unless requested"""

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                generated_code = data["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "code": generated_code,
                    "model": model,
                    "language": language,
                    "prompt": prompt
                }
            else:
                return {
                    "error": f"OpenRouter API error: {response.status_code}",
                    "success": False
                }

        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return {"error": str(e), "success": False}

    @staticmethod
    def index_code(content: str, filename: str, language: str = "python") -> Dict[str, Any]:
        """Index code for semantic search"""
        try:
            code_id = hashlib.md5(content.encode()).hexdigest()
            
            # Extract functions (simplified)
            functions = []
            lines = content.split('\n')
            
            if language.lower() == 'python':
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('def ') or stripped.startswith('class '):
                        func_name = stripped.split('(')[0].replace('def ', '').replace('class ', '').strip()
                        functions.append({
                            'name': func_name,
                            'line': i + 1,
                            'type': 'class' if stripped.startswith('class') else 'function',
                            'signature': stripped
                        })
            
            # Store in index
            code_index[code_id] = {
                'content': content,
                'filename': filename,
                'language': language,
                'functions': functions,
                'indexed_at': str(os.times().elapsed)
            }
            
            return {
                "success": True,
                "code_id": code_id,
                "filename": filename,
                "functions_found": len(functions),
                "functions": functions
            }
            
        except Exception as e:
            logger.error(f"Code indexing error: {e}")
            return {"error": str(e), "success": False}

    @staticmethod
    def search_code(query: str, language: str = None) -> Dict[str, Any]:
        """Search indexed code"""
        try:
            results = []
            query_lower = query.lower()
            
            for code_id, data in code_index.items():
                score = 0
                
                # Search in content
                if query_lower in data['content'].lower():
                    score += 10
                
                # Search in functions
                for func in data['functions']:
                    if query_lower in func['name'].lower():
                        score += 20
                
                # Search in filename
                if query_lower in data['filename'].lower():
                    score += 25
                
                if language and data['language'].lower() == language.lower():
                    score += 5
                
                if score > 0:
                    results.append({
                        'code_id': code_id,
                        'filename': data['filename'],
                        'language': data['language'],
                        'score': score,
                        'functions': data['functions'],
                        'preview': data['content'][:200] + '...'
                    })
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "results": results[:10]
            }
            
        except Exception as e:
            logger.error(f"Code search error: {e}")
            return {"error": str(e), "success": False}

    @staticmethod
    async def analyze_security(code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code for security vulnerabilities"""
        try:
            if not OPENROUTER_API_KEY:
                return {"error": "OpenRouter API key not configured", "success": False}
            
            system_prompt = f"""You are a security expert. Analyze this {language} code for vulnerabilities.

Focus on:
- SQL injection risks
- XSS vulnerabilities  
- Authentication/authorization issues
- Input validation problems
- Cryptographic weaknesses
- Dependency vulnerabilities

Provide specific, actionable security recommendations."""

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "anthropic/claude-3.5-sonnet-20241022",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this {language} code for security issues:\n\n```{language}\n{code}\n```"}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                analysis = data["choices"][0]["message"]["content"]
                
                # Store scan result
                scan_id = hashlib.md5(code.encode()).hexdigest()
                security_scans[scan_id] = {
                    'code': code,
                    'language': language,
                    'analysis': analysis,
                    'scanned_at': str(os.times().elapsed)
                }
                
                return {
                    "success": True,
                    "scan_id": scan_id,
                    "analysis": analysis,
                    "language": language
                }
            else:
                return {
                    "error": f"Security analysis API error: {response.status_code}",
                    "success": False
                }

        except Exception as e:
            logger.error(f"Security analysis error: {e}")
            return {"error": str(e), "success": False}

    @staticmethod
    def get_analytics() -> Dict[str, Any]:
        """Get system analytics"""
        try:
            return {
                "success": True,
                "analytics": {
                    "indexed_files": len(code_index),
                    "total_functions": sum(len(data['functions']) for data in code_index.values()),
                    "security_scans": len(security_scans),
                    "languages": list(set(data['language'] for data in code_index.values())),
                    "recent_activity": {
                        "code_generations": 0,  # Would track in production
                        "searches": 0,
                        "scans": len(security_scans)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {"error": str(e), "success": False}

# Initialize MCP services
mcp = MCPServices()

