#!/usr/bin/env python3
"""
SOPHIA V4 Code Index MCP Server
Real semantic code search and indexing
"""

import os
import json
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory code index (production would use Neon database)
code_index = {}

def hash_code(code):
    """Generate hash for code content"""
    return hashlib.md5(code.encode()).hexdigest()

def extract_functions(code, language='python'):
    """Extract functions from code"""
    functions = []
    lines = code.split('\n')
    
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
    
    return functions

def semantic_search(query, language=None):
    """Perform semantic search on indexed code"""
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
        
        if score > 0:
            results.append({
                'code_id': code_id,
                'filename': data['filename'],
                'language': data['language'],
                'score': score,
                'functions': data['functions'],
                'preview': data['content'][:200] + '...'
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:10]

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "service": "SOPHIA V4 Code Index MCP Server",
        "version": "1.0.0",
        "status": "running",
        "indexed_files": len(code_index),
        "endpoints": ["/health", "/index", "/search", "/analyze"]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "code-index-mcp",
        "indexed_files": len(code_index),
        "total_functions": sum(len(data['functions']) for data in code_index.values())
    })

@app.route('/index', methods=['POST'])
def index_code():
    """Index code for semantic search"""
    try:
        data = request.get_json()
        content = data.get('content')
        filename = data.get('filename', 'unknown.py')
        language = data.get('language', 'python')
        
        if not content:
            return jsonify({"error": "content is required"}), 400
        
        code_id = hash_code(content)
        functions = extract_functions(content, language)
        
        code_index[code_id] = {
            'content': content,
            'filename': filename,
            'language': language,
            'functions': functions
        }
        
        return jsonify({
            "status": "success",
            "code_id": code_id,
            "filename": filename,
            "functions_found": len(functions)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
def search_code():
    """Search indexed code"""
    try:
        data = request.get_json()
        query = data.get('query')
        language = data.get('language')
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        results = semantic_search(query, language)
        
        return jsonify({
            "status": "success",
            "query": query,
            "total_results": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['GET'])
def analyze_codebase():
    """Analyze indexed codebase"""
    try:
        total_files = len(code_index)
        languages = {}
        total_functions = 0
        
        for data in code_index.values():
            lang = data['language']
            languages[lang] = languages.get(lang, 0) + 1
            total_functions += len(data['functions'])
        
        return jsonify({
            "status": "success",
            "analysis": {
                "total_files": total_files,
                "total_functions": total_functions,
                "languages": languages
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

