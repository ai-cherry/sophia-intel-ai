#!/usr/bin/env python3
"""
SOPHIA V4 Code Generation MCP Server
Real OpenRouter integration for code generation and GitHub PR creation
"""

import os
import sys
import requests
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from github import Github, GithubException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration from environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Best models for code generation
BEST_CODING_MODELS = [
    "qwen/qwen3-coder",
    "openai/gpt-5-mini", 
    "anthropic/claude-3.7-sonnet",
    "openai/gpt-4o",
    "deepseek/deepseek-chat-v3-0324"
]

def call_openrouter(model, prompt, system_prompt=None):
    """Call OpenRouter API with specified model"""
    try:
        if not OPENROUTER_API_KEY:
            return "OpenRouter API key not configured"
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 4000
            })
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "service": "SOPHIA V4 Code Generation MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/generate",
            "/models",
            "/analyze"
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "code-gen-mcp",
        "version": "1.0.0",
        "available_models": BEST_CODING_MODELS,
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "github_configured": bool(GITHUB_TOKEN)
    })

@app.route('/generate', methods=['POST'])
def generate_code():
    """Generate code using OpenRouter models"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        language = data.get('language', 'python')
        model = data.get('model', BEST_CODING_MODELS[0])
        
        if not prompt:
            return jsonify({"error": "prompt is required"}), 400
        
        if model not in BEST_CODING_MODELS:
            model = BEST_CODING_MODELS[0]
        
        # Create system prompt for code generation
        system_prompt = f"""You are an expert {language} developer. Generate clean, well-documented, production-ready code.
        
Guidelines:
- Write clear, readable code with proper comments
- Follow best practices and conventions for {language}
- Include error handling where appropriate
- Add docstrings/comments explaining the code
- Ensure code is secure and efficient
- Return only the code, no explanations unless requested"""

        # Generate code
        generated_code = call_openrouter(model, prompt, system_prompt)
        
        if generated_code:
            return jsonify({
                "status": "success",
                "prompt": prompt,
                "language": language,
                "model": model,
                "generated_code": generated_code
            })
        else:
            return jsonify({"error": "Failed to generate code"}), 500
            
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/models', methods=['GET'])
def get_available_models():
    """Get list of available coding models"""
    return jsonify({
        "status": "success",
        "models": BEST_CODING_MODELS,
        "default_model": BEST_CODING_MODELS[0]
    })

@app.route('/analyze', methods=['POST'])
def analyze_code():
    """Analyze existing code and suggest improvements"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language', 'python')
        analysis_type = data.get('analysis_type', 'general')
        
        if not code:
            return jsonify({"error": "code is required"}), 400
        
        # Create analysis prompt
        analysis_prompts = {
            'general': f"Analyze this {language} code and provide suggestions for improvement:",
            'security': f"Perform a security analysis of this {language} code and identify potential vulnerabilities:",
            'performance': f"Analyze this {language} code for performance issues and optimization opportunities:",
            'style': f"Review this {language} code for style and best practices compliance:"
        }
        
        system_prompt = f"""You are an expert {language} code reviewer. Provide detailed analysis and actionable suggestions.

Format your response as:
1. **Summary**: Brief overview of the code
2. **Issues Found**: List specific problems
3. **Suggestions**: Concrete improvement recommendations
4. **Improved Code**: If applicable, provide corrected version"""

        prompt = f"{analysis_prompts.get(analysis_type, analysis_prompts['general'])}\n\n```{language}\n{code}\n```"
        
        # Use best model for code analysis
        analysis = call_openrouter(BEST_CODING_MODELS[0], prompt, system_prompt)
        
        if analysis:
            return jsonify({
                "status": "success",
                "analysis_type": analysis_type,
                "language": language,
                "analysis": analysis
            })
        else:
            return jsonify({"error": "Failed to analyze code"}), 500
            
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

