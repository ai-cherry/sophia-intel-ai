"""
MCP Filesystem Server
Provides filesystem access with strict allowlist enforcement
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

app = FastAPI(title="MCP Filesystem Server")
security = HTTPBearer()

try:
    from builder_cli.lib.env import load_central_env
    load_central_env()
except Exception:
    pass


class FileOperation(BaseModel):
    """File operation request"""
    path: str
    operation: str = Field(pattern="^(read|write|list|delete)$")
    content: Optional[str] = None
    encoding: str = "utf-8"


class FileInfo(BaseModel):
    """File information"""
    path: str
    name: str
    size: int
    modified: datetime
    is_directory: bool


class MCPFilesystemServer:
    """Filesystem server with allowlist"""
    
    def __init__(self, allowlist: List[Path], read_only: bool = False):
        """Initialize with allowlist paths"""
        self.allowlist = [p.resolve() for p in allowlist]
        self.read_only = read_only
        logger.info(f"Filesystem server initialized with {len(self.allowlist)} allowed paths")
    
    def validate_path(self, path_str: str) -> Path:
        """Validate path is within allowlist"""
        path = Path(path_str).resolve()
        
        # Check if path is within any allowed directory
        for allowed in self.allowlist:
            try:
                path.relative_to(allowed)
                return path
            except ValueError:
                continue
        
        raise HTTPException(403, f"Path not in allowlist: {path}")
    
    async def read(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents"""
        file_path = self.validate_path(path)
        
        if not file_path.exists():
            raise HTTPException(404, f"File not found: {path}")
        
        if not file_path.is_file():
            raise HTTPException(400, f"Not a file: {path}")
        
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Read error: {e}")
            raise HTTPException(500, f"Read error: {e}")
    
    async def write(self, path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Write file contents"""
        if self.read_only:
            raise HTTPException(403, "Server is in read-only mode")
        
        file_path = self.validate_path(path)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Backup existing file
            backup_path = None
            if file_path.exists():
                backup_path = file_path.with_suffix(f".backup.{datetime.now().timestamp()}")
                file_path.rename(backup_path)
            
            # Write new content
            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)
            
            # Remove backup on success
            if backup_path and backup_path.exists():
                backup_path.unlink()
            
            return {
                "path": str(file_path),
                "size": len(content),
                "encoding": encoding
            }
            
        except Exception as e:
            # Restore backup on failure
            if backup_path and backup_path.exists():
                backup_path.rename(file_path)
            
            logger.error(f"Write error: {e}")
            raise HTTPException(500, f"Write error: {e}")
    
    async def list(self, path: str) -> List[FileInfo]:
        """List directory contents"""
        dir_path = self.validate_path(path)
        
        if not dir_path.exists():
            raise HTTPException(404, f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise HTTPException(400, f"Not a directory: {path}")
        
        files = []
        for item in dir_path.iterdir():
            # Only include items still within allowlist
            try:
                self.validate_path(str(item))
                stat = item.stat()
                files.append(FileInfo(
                    path=str(item),
                    name=item.name,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    is_directory=item.is_dir()
                ))
            except HTTPException:
                # Skip items outside allowlist
                continue
        
        return sorted(files, key=lambda f: (not f.is_directory, f.name))
    
    async def delete(self, path: str) -> Dict[str, Any]:
        """Delete file or directory"""
        if self.read_only:
            raise HTTPException(403, "Server is in read-only mode")
        
        file_path = self.validate_path(path)
        
        if not file_path.exists():
            raise HTTPException(404, f"Path not found: {path}")
        
        try:
            # Create backup
            backup_path = file_path.with_suffix(f".deleted.{datetime.now().timestamp()}")
            file_path.rename(backup_path)
            
            return {
                "path": str(file_path),
                "deleted": True,
                "backup": str(backup_path)
            }
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            raise HTTPException(500, f"Delete error: {e}")


# Initialize server
allowlist_paths = [
    Path(os.getenv("WORKSPACE_PATH", "/app"))
]
server = MCPFilesystemServer(allowlist_paths, read_only=False)


# API Routes
@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "server": "filesystem"}


@app.post("/read")
async def read_file(
    operation: FileOperation,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Read file contents"""
    content = await server.read(operation.path, operation.encoding)
    return {"content": content}


@app.post("/write")
async def write_file(
    operation: FileOperation,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Write file contents"""
    if not operation.content:
        raise HTTPException(400, "Content required for write operation")
    
    result = await server.write(operation.path, operation.content, operation.encoding)
    return result


@app.post("/list")
async def list_directory(
    operation: FileOperation,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """List directory contents"""
    files = await server.list(operation.path)
    return {"files": [f.model_dump() for f in files]}


@app.post("/delete")
async def delete_path(
    operation: FileOperation,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete file or directory"""
    result = await server.delete(operation.path)
    return result


@app.post("/validate")
async def validate_path(
    operation: FileOperation,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validate path is in allowlist"""
    try:
        path = server.validate_path(operation.path)
        return {"valid": True, "resolved": str(path)}
    except HTTPException:
        return {"valid": False, "resolved": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
