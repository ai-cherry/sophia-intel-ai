import os, glob, pathlib, json, time
from typing import List, Dict, Any
from haystack import Pipeline
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.dataclasses import Document
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersTextEmbedder

ROOT = os.getenv("INDEX_ROOT", ".")
COLL = os.getenv("QDRANT_COLLECTION", "repo_docs")
BATCH_SIZE = int(os.getenv("INDEX_BATCH_SIZE", "100"))
CHUNK_SIZE = int(os.getenv("INDEX_CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("INDEX_CHUNK_OVERLAP", "64"))

EXCLUDE_PATTERNS = [
    ".git", "node_modules", "__pycache__", ".venv", "dist", "build", 
    ".next", ".nuxt", "coverage", ".nyc_output", "*.log", "*.tmp",
    ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.pyd"
]

FILE_EXTENSIONS = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', 
    '.jsx': 'react', '.tsx': 'react', '.html': 'html', '.css': 'css',
    '.scss': 'scss', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
    '.md': 'markdown', '.txt': 'text', '.sql': 'sql', '.sh': 'shell',
    '.dockerfile': 'docker', '.tf': 'terraform', '.go': 'go', 
    '.rs': 'rust', '.java': 'java', '.cpp': 'cpp', '.c': 'c'
}

def extract_code_metrics(content: str, file_path: str) -> Dict[str, Any]:
    """Extract code quality metrics and metadata"""
    lines = content.split('\n')
    return {
        "line_count": len(lines),
        "char_count": len(content),
        "avg_line_length": sum(len(line) for line in lines) / max(1, len(lines)),
        "empty_lines": sum(1 for line in lines if not line.strip()),
        "has_comments": any(line.strip().startswith(('#', '//', '/*', '"""', "'''")) for line in lines),
        "complexity_score": min(100, len([l for l in lines if any(kw in l.lower() for kw in ['if', 'for', 'while', 'try', 'def', 'class'])]))
    }

def should_index_file(file_path: str) -> bool:
    """Determine if file should be indexed based on patterns and size"""
    path_str = str(file_path)
    
    # Check exclusion patterns
    if any(pattern in path_str for pattern in EXCLUDE_PATTERNS):
        return False
        
    # Check file size (skip files > 1MB)
    try:
        if pathlib.Path(file_path).stat().st_size > 1024 * 1024:
            return False
    except OSError:
        return False
        
    return True

def create_enhanced_pipeline():
    """Create indexing pipeline with embeddings and chunking"""
    store = QdrantDocumentStore(
        url=os.getenv("QDRANT_URL"), 
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=COLL, 
        recreate_index=os.getenv("RECREATE_INDEX", "false").lower() == "true",
        embedding_dim=384  # for all-MiniLM-L6-v2
    )
    
    embedder = SentenceTransformersTextEmbedder(
        model=os.getenv("EMBEDDER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    
    splitter = DocumentSplitter(
        split_by="token", 
        split_length=CHUNK_SIZE, 
        split_overlap=CHUNK_OVERLAP
    )
    
    writer = DocumentWriter(document_store=store)
    
    pipe = Pipeline()
    pipe.add_component("embed", embedder)
    pipe.add_component("split", splitter)  
    pipe.add_component("write", writer)
    
    pipe.connect("embed", "split")
    pipe.connect("split", "write")
    
    return pipe

def process_files_batch(files: List[str]) -> List[Document]:
    """Process files into documents with enhanced metadata"""
    docs = []
    
    for file_path in files:
        try:
            path_obj = pathlib.Path(file_path)
            content = path_obj.read_text(encoding='utf-8', errors='ignore')
            
            if len(content.strip()) < 10:  # Skip nearly empty files
                continue
                
            file_ext = path_obj.suffix.lower()
            file_type = FILE_EXTENSIONS.get(file_ext, 'unknown')
            
            # Extract metrics
            metrics = extract_code_metrics(content, file_path)
            
            # Create document with rich metadata
            doc = Document(
                content=content,
                meta={
                    "path": str(path_obj.resolve()),
                    "filename": path_obj.name,
                    "extension": file_ext,
                    "file_type": file_type,
                    "size": len(content),
                    "modified_time": path_obj.stat().st_mtime,
                    "indexed_time": time.time(),
                    **metrics
                }
            )
            docs.append(doc)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
            
    return docs

def main():
    start_time = time.time()
    
    # Discover files
    pattern = f"{ROOT}/**/*.*"
    all_files = glob.glob(pattern, recursive=True)
    valid_files = [f for f in all_files if should_index_file(f)]
    
    print(f"Found {len(valid_files)} indexable files out of {len(all_files)} total")
    
    if not valid_files:
        print("No files to index")
        return
        
    # Create pipeline
    try:
        pipeline = create_enhanced_pipeline()
        print(f"Created indexing pipeline for collection: {COLL}")
    except Exception as e:
        print(f"Failed to create pipeline: {e}")
        return
    
    # Process in batches
    total_docs = 0
    for i in range(0, len(valid_files), BATCH_SIZE):
        batch = valid_files[i:i + BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1}/{(len(valid_files)-1)//BATCH_SIZE + 1}")
        
        docs = process_files_batch(batch)
        
        if docs:
            try:
                result = pipeline.run({"embed": {"documents": docs}})
                total_docs += len(docs)
                print(f"Indexed {len(docs)} documents")
            except Exception as e:
                print(f"Error indexing batch: {e}")
                continue
                
    duration = time.time() - start_time
    print(f"Indexing complete: {total_docs} documents in {duration:.2f}s")
    
    # Save indexing report
    report = {
        "collection": COLL,
        "total_files": len(valid_files),
        "indexed_documents": total_docs,
        "duration_seconds": duration,
        "chunk_size": CHUNK_SIZE,
        "batch_size": BATCH_SIZE,
        "timestamp": time.time()
    }
    
    with open(f".indexing_report_{int(time.time())}.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()