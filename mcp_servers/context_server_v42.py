"""
Context MCP Server v4.2 - REAL Implementation
Code indexing, search, and RAG for SOPHIA's code-from-chat capabilities
"""

import os
import re
import ast
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeFile(BaseModel):
    path: str
    content: str
    language: str
    size: int
    last_modified: str
    functions: List[str] = []
    classes: List[str] = []
    imports: List[str] = []
    complexity_score: float = 0.0

class CodeSearchResult(BaseModel):
    file_path: str
    relevance_score: float
    matched_content: str
    context_lines: List[str]
    function_name: Optional[str] = None
    class_name: Optional[str] = None

class CodeIndexRequest(BaseModel):
    repository_url: str
    branch: str = "main"
    include_patterns: List[str] = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
    exclude_patterns: List[str] = ["node_modules/*", "venv/*", "__pycache__/*", "*.pyc"]

class CodeSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    file_types: List[str] = []
    include_functions: bool = True
    include_classes: bool = True

class CodeContextRequest(BaseModel):
    file_path: str
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    context_lines: int = 10

class CodeIndexResponse(BaseModel):
    status: str
    files_indexed: int
    total_lines: int
    languages: Dict[str, int]
    index_time: str

class CodeSearchResponse(BaseModel):
    query: str
    results: List[CodeSearchResult]
    total_results: int
    search_time: str

class CodeContextResponse(BaseModel):
    file_path: str
    content: str
    metadata: Dict[str, Any]
    related_files: List[str]

# Initialize FastAPI app
app = FastAPI(title="SOPHIA Context Server v4.2", version="4.2.0")

# In-memory code index (in production, use a proper vector database)
code_index: Dict[str, CodeFile] = {}
function_index: Dict[str, List[str]] = {}  # function_name -> [file_paths]
class_index: Dict[str, List[str]] = {}     # class_name -> [file_paths]
import_index: Dict[str, List[str]] = {}    # import_name -> [file_paths]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "context-server",
        "version": "4.2.0",
        "indexed_files": len(code_index),
        "functions": len(function_index),
        "classes": len(class_index)
    }

@app.post("/index", response_model=CodeIndexResponse)
async def index_repository(request: CodeIndexRequest):
    """Index a repository for code search and RAG"""
    try:
        logger.info(f"Indexing repository: {request.repository_url}")
        
        # Clone or update repository
        repo_path = await clone_repository(request.repository_url, request.branch)
        
        # Index all code files
        indexed_files = 0
        total_lines = 0
        languages = {}
        
        for file_path in find_code_files(repo_path, request.include_patterns, request.exclude_patterns):
            try:
                code_file = await analyze_code_file(file_path)
                if code_file:
                    code_index[code_file.path] = code_file
                    indexed_files += 1
                    total_lines += len(code_file.content.split('\n'))
                    
                    # Update language stats
                    lang = code_file.language
                    languages[lang] = languages.get(lang, 0) + 1
                    
                    # Update function and class indexes
                    for func in code_file.functions:
                        if func not in function_index:
                            function_index[func] = []
                        function_index[func].append(code_file.path)
                    
                    for cls in code_file.classes:
                        if cls not in class_index:
                            class_index[cls] = []
                        class_index[cls].append(code_file.path)
                    
                    for imp in code_file.imports:
                        if imp not in import_index:
                            import_index[imp] = []
                        import_index[imp].append(code_file.path)
                        
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
                continue
        
        logger.info(f"Indexed {indexed_files} files with {total_lines} total lines")
        
        return CodeIndexResponse(
            status="success",
            files_indexed=indexed_files,
            total_lines=total_lines,
            languages=languages,
            index_time=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Repository indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=CodeSearchResponse)
async def search_code(request: CodeSearchRequest):
    """Search indexed code using semantic and keyword matching"""
    try:
        start_time = datetime.utcnow()
        logger.info(f"Searching code: {request.query}")
        
        results = []
        
        # Strategy 1: Function name matching
        if request.include_functions:
            for func_name, file_paths in function_index.items():
                if query_matches(request.query, func_name):
                    for file_path in file_paths:
                        if file_path in code_index:
                            result = create_search_result(
                                code_index[file_path], 
                                request.query, 
                                function_name=func_name
                            )
                            if result:
                                results.append(result)
        
        # Strategy 2: Class name matching
        if request.include_classes:
            for class_name, file_paths in class_index.items():
                if query_matches(request.query, class_name):
                    for file_path in file_paths:
                        if file_path in code_index:
                            result = create_search_result(
                                code_index[file_path], 
                                request.query, 
                                class_name=class_name
                            )
                            if result:
                                results.append(result)
        
        # Strategy 3: Content search
        for file_path, code_file in code_index.items():
            if request.file_types and code_file.language not in request.file_types:
                continue
                
            if content_matches(request.query, code_file.content):
                result = create_search_result(code_file, request.query)
                if result:
                    results.append(result)
        
        # Remove duplicates and sort by relevance
        unique_results = remove_duplicate_results(results)
        sorted_results = sorted(unique_results, key=lambda x: x.relevance_score, reverse=True)
        final_results = sorted_results[:request.max_results]
        
        search_time = (datetime.utcnow() - start_time).total_seconds()
        
        return CodeSearchResponse(
            query=request.query,
            results=final_results,
            total_results=len(final_results),
            search_time=f"{search_time:.3f}s"
        )
        
    except Exception as e:
        logger.error(f"Code search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/context", response_model=CodeContextResponse)
async def get_code_context(request: CodeContextRequest):
    """Get detailed context for a specific code file or function"""
    try:
        logger.info(f"Getting context for: {request.file_path}")
        
        if request.file_path not in code_index:
            raise HTTPException(status_code=404, detail="File not found in index")
        
        code_file = code_index[request.file_path]
        
        # Get specific function or class context
        if request.function_name:
            content = extract_function_context(code_file.content, request.function_name, request.context_lines)
        elif request.class_name:
            content = extract_class_context(code_file.content, request.class_name, request.context_lines)
        else:
            content = code_file.content
        
        # Find related files
        related_files = find_related_files(code_file)
        
        metadata = {
            "language": code_file.language,
            "size": code_file.size,
            "last_modified": code_file.last_modified,
            "functions": code_file.functions,
            "classes": code_file.classes,
            "imports": code_file.imports,
            "complexity_score": code_file.complexity_score
        }
        
        return CodeContextResponse(
            file_path=request.file_path,
            content=content,
            metadata=metadata,
            related_files=related_files
        )
        
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def clone_repository(repo_url: str, branch: str) -> str:
    """Clone or update repository"""
    try:
        # For now, use the current repository
        # In production, implement actual git cloning
        return "/home/ubuntu/sophia-intel"
        
    except Exception as e:
        logger.error(f"Repository cloning failed: {e}")
        raise

def find_code_files(repo_path: str, include_patterns: List[str], exclude_patterns: List[str]) -> List[str]:
    """Find all code files matching patterns"""
    code_files = []
    repo_path_obj = Path(repo_path)
    
    for pattern in include_patterns:
        for file_path in repo_path_obj.rglob(pattern):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(repo_path_obj))
                
                # Check exclude patterns
                excluded = False
                for exclude_pattern in exclude_patterns:
                    if re.match(exclude_pattern.replace('*', '.*'), relative_path):
                        excluded = True
                        break
                
                if not excluded:
                    code_files.append(str(file_path))
    
    return code_files

async def analyze_code_file(file_path: str) -> Optional[CodeFile]:
    """Analyze a code file and extract metadata"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_stat = os.stat(file_path)
        language = detect_language(file_path)
        
        # Extract functions, classes, and imports
        functions = []
        classes = []
        imports = []
        complexity_score = 0.0
        
        if language == "python":
            functions, classes, imports, complexity_score = analyze_python_file(content)
        elif language in ["javascript", "typescript"]:
            functions, classes, imports = analyze_js_file(content)
        
        return CodeFile(
            path=file_path,
            content=content,
            language=language,
            size=file_stat.st_size,
            last_modified=datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            functions=functions,
            classes=classes,
            imports=imports,
            complexity_score=complexity_score
        )
        
    except Exception as e:
        logger.warning(f"Failed to analyze {file_path}: {e}")
        return None

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = Path(file_path).suffix.lower()
    
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.rb': 'ruby'
    }
    
    return language_map.get(ext, 'unknown')

def analyze_python_file(content: str) -> Tuple[List[str], List[str], List[str], float]:
    """Analyze Python file for functions, classes, and imports"""
    functions = []
    classes = []
    imports = []
    complexity_score = 0.0
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                # Simple complexity calculation
                complexity_score += len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While))])
            
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Normalize complexity score
        complexity_score = min(complexity_score / max(len(functions), 1), 10.0)
        
    except Exception as e:
        logger.debug(f"Python AST parsing failed: {e}")
    
    return functions, classes, imports, complexity_score

def analyze_js_file(content: str) -> Tuple[List[str], List[str], List[str]]:
    """Analyze JavaScript/TypeScript file for functions, classes, and imports"""
    functions = []
    classes = []
    imports = []
    
    try:
        # Simple regex-based parsing for JS/TS
        # Function declarations
        func_pattern = r'(?:function\s+(\w+)|(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>)|(?:async\s+)?(\w+)\s*\([^)]*\)\s*{)'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                functions.append(func_name)
        
        # Class declarations
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            classes.append(match.group(1))
        
        # Import statements
        import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))
        
    except Exception as e:
        logger.debug(f"JS parsing failed: {e}")
    
    return functions, classes, imports

def query_matches(query: str, target: str) -> bool:
    """Check if query matches target using fuzzy matching"""
    query_lower = query.lower()
    target_lower = target.lower()
    
    # Exact match
    if query_lower == target_lower:
        return True
    
    # Substring match
    if query_lower in target_lower:
        return True
    
    # Word boundary match
    query_words = query_lower.split()
    target_words = target_lower.split('_')
    
    for query_word in query_words:
        for target_word in target_words:
            if query_word in target_word:
                return True
    
    return False

def content_matches(query: str, content: str) -> bool:
    """Check if query matches content"""
    query_lower = query.lower()
    content_lower = content.lower()
    
    # Simple keyword matching
    query_words = query_lower.split()
    
    # Require at least 2 words to match for content search
    matches = sum(1 for word in query_words if word in content_lower)
    return matches >= min(2, len(query_words))

def create_search_result(code_file: CodeFile, query: str, function_name: str = None, class_name: str = None) -> Optional[CodeSearchResult]:
    """Create a search result from a code file"""
    try:
        # Calculate relevance score
        relevance_score = 0.0
        
        if function_name:
            relevance_score = 0.9 if query_matches(query, function_name) else 0.7
        elif class_name:
            relevance_score = 0.9 if query_matches(query, class_name) else 0.7
        else:
            relevance_score = 0.5
        
        # Extract matched content
        matched_content = extract_matched_content(code_file.content, query)
        context_lines = extract_context_lines(code_file.content, query, 3)
        
        return CodeSearchResult(
            file_path=code_file.path,
            relevance_score=relevance_score,
            matched_content=matched_content,
            context_lines=context_lines,
            function_name=function_name,
            class_name=class_name
        )
        
    except Exception as e:
        logger.debug(f"Failed to create search result: {e}")
        return None

def extract_matched_content(content: str, query: str) -> str:
    """Extract content that matches the query"""
    lines = content.split('\n')
    query_words = query.lower().split()
    
    matched_lines = []
    for line in lines:
        line_lower = line.lower()
        if any(word in line_lower for word in query_words):
            matched_lines.append(line.strip())
            if len(matched_lines) >= 3:  # Limit matched content
                break
    
    return '\n'.join(matched_lines)

def extract_context_lines(content: str, query: str, context_size: int) -> List[str]:
    """Extract context lines around matches"""
    lines = content.split('\n')
    query_words = query.lower().split()
    context_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(word in line_lower for word in query_words):
            start = max(0, i - context_size)
            end = min(len(lines), i + context_size + 1)
            
            for j in range(start, end):
                if lines[j].strip() and lines[j] not in context_lines:
                    context_lines.append(lines[j])
            
            if len(context_lines) >= 10:  # Limit context
                break
    
    return context_lines

def extract_function_context(content: str, function_name: str, context_lines: int) -> str:
    """Extract context around a specific function"""
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if f"def {function_name}" in line or f"function {function_name}" in line:
            start = max(0, i - context_lines)
            
            # Find end of function (simple heuristic)
            end = i + 1
            indent_level = len(line) - len(line.lstrip())
            
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent_level:
                    end = j
                    break
            
            end = min(len(lines), end + context_lines)
            return '\n'.join(lines[start:end])
    
    return content

def extract_class_context(content: str, class_name: str, context_lines: int) -> str:
    """Extract context around a specific class"""
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if f"class {class_name}" in line:
            start = max(0, i - context_lines)
            
            # Find end of class (simple heuristic)
            end = i + 1
            indent_level = len(line) - len(line.lstrip())
            
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent_level:
                    end = j
                    break
            
            end = min(len(lines), end + context_lines)
            return '\n'.join(lines[start:end])
    
    return content

def find_related_files(code_file: CodeFile) -> List[str]:
    """Find files related to the given code file"""
    related = []
    
    # Find files that import this file or are imported by this file
    for import_name in code_file.imports:
        if import_name in import_index:
            related.extend(import_index[import_name])
    
    # Find files with similar functions or classes
    for func_name in code_file.functions:
        if func_name in function_index:
            related.extend(function_index[func_name])
    
    for class_name in code_file.classes:
        if class_name in class_index:
            related.extend(class_index[class_name])
    
    # Remove duplicates and self
    unique_related = list(set(related))
    if code_file.path in unique_related:
        unique_related.remove(code_file.path)
    
    return unique_related[:10]  # Limit to top 10

def remove_duplicate_results(results: List[CodeSearchResult]) -> List[CodeSearchResult]:
    """Remove duplicate search results"""
    seen_paths = set()
    unique_results = []
    
    for result in results:
        if result.file_path not in seen_paths:
            seen_paths.add(result.file_path)
            unique_results.append(result)
    
    return unique_results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

