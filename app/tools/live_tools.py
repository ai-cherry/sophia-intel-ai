"""
Live Tool Implementations for Local Development
All tools are fully functional and execute real operations.
BE CAREFUL - These tools can modify your filesystem and git repository!
"""

import os
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles
import logging

logger = logging.getLogger(__name__)

class LiveFileSystemTools:
    """Real file system operations."""
    
    def __init__(self, allowed_paths: List[str] = None):
        """Initialize with optional path restrictions."""
        self.allowed_paths = allowed_paths or ["./"]
        
    def _is_safe_path(self, path: str) -> bool:
        """Check if path is within allowed directories."""
        if not self.allowed_paths:
            return True
        path = Path(path).resolve()
        for allowed in self.allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                path.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False
    
    async def read_file(self, path: str) -> str:
        """Read a file from disk."""
        if not self._is_safe_path(path):
            raise PermissionError(f"Path {path} is not in allowed directories")
        
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
        logger.info(f"Read {len(content)} bytes from {path}")
        return content
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        if not self._is_safe_path(path):
            raise PermissionError(f"Path {path} is not in allowed directories")
        
        # Create directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(path, 'w') as f:
            await f.write(content)
        
        logger.info(f"Wrote {len(content)} bytes to {path}")
        return {
            "status": "success",
            "path": path,
            "bytes_written": len(content)
        }
    
    async def list_directory(self, path: str = ".") -> List[Dict[str, Any]]:
        """List contents of a directory."""
        if not self._is_safe_path(path):
            raise PermissionError(f"Path {path} is not in allowed directories")
        
        path_obj = Path(path)
        items = []
        
        for item in path_obj.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": item.stat().st_mtime
            })
        
        logger.info(f"Listed {len(items)} items in {path}")
        return items
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file (with confirmation)."""
        if not self._is_safe_path(path):
            raise PermissionError(f"Path {path} is not in allowed directories")
        
        path_obj = Path(path)
        if not path_obj.exists():
            return {"status": "error", "message": "File not found"}
        
        path_obj.unlink()
        logger.warning(f"Deleted file: {path}")
        return {"status": "success", "deleted": path}


class LiveGitTools:
    """Real git operations."""
    
    async def git_status(self) -> Dict[str, Any]:
        """Get git status."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n') if result.stdout else []
        return {
            "modified_files": len([l for l in lines if l.startswith(' M')]),
            "new_files": len([l for l in lines if l.startswith('??')]),
            "deleted_files": len([l for l in lines if l.startswith(' D')]),
            "raw": result.stdout
        }
    
    async def git_diff(self, file: Optional[str] = None) -> str:
        """Get git diff."""
        cmd = ["git", "diff"]
        if file:
            cmd.append(file)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    async def git_add(self, files: List[str]) -> Dict[str, Any]:
        """Add files to git staging."""
        result = subprocess.run(
            ["git", "add"] + files,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Added {len(files)} files to git staging")
            return {"status": "success", "files_added": files}
        else:
            return {"status": "error", "message": result.stderr}
    
    async def git_commit(self, message: str) -> Dict[str, Any]:
        """Create a git commit."""
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Created commit: {message[:50]}")
            return {
                "status": "success",
                "message": message,
                "output": result.stdout
            }
        else:
            return {"status": "error", "message": result.stderr}
    
    async def git_branch(self, name: Optional[str] = None, checkout: bool = False) -> Dict[str, Any]:
        """Create or list git branches."""
        if name:
            cmd = ["git", "checkout", "-b" if checkout else "", name]
            cmd = [c for c in cmd if c]  # Remove empty strings
        else:
            cmd = ["git", "branch"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout
            }
        else:
            return {"status": "error", "message": result.stderr}


class LiveCodeTools:
    """Real code execution and testing tools."""
    
    async def run_tests(self, test_path: str = None) -> Dict[str, Any]:
        """Run tests using pytest."""
        cmd = ["python", "-m", "pytest", "-v"]
        if test_path:
            cmd.append(test_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse pytest output
        passed = result.stdout.count(" PASSED")
        failed = result.stdout.count(" FAILED")
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "passed": passed,
            "failed": failed,
            "output": result.stdout,
            "errors": result.stderr
        }
    
    async def run_linter(self, file_path: str = None) -> Dict[str, Any]:
        """Run linter (ruff or flake8)."""
        # Try ruff first, fall back to flake8
        for linter in ["ruff", "flake8"]:
            cmd = [linter]
            if file_path:
                cmd.append(file_path)
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                return {
                    "status": "success" if result.returncode == 0 else "issues_found",
                    "linter": linter,
                    "output": result.stdout,
                    "issues": result.stdout.count('\n') if result.stdout else 0
                }
            except FileNotFoundError:
                continue
        
        return {"status": "error", "message": "No linter found (install ruff or flake8)"}
    
    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code snippet (with caution!)."""
        if language != "python":
            return {"status": "error", "message": f"Language {language} not supported"}
        
        # Write to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=10  # 10 second timeout
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        finally:
            os.unlink(temp_path)


class LiveSearchTools:
    """Real code search tools."""
    
    async def search_code(
        self,
        query: str,
        file_type: str = None,
        path: str = "."
    ) -> List[Dict[str, Any]]:
        """Search code using ripgrep."""
        cmd = ["rg", "--json", query, path]
        if file_type:
            cmd.extend(["-t", file_type])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            matches = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "match":
                            match_data = data.get("data", {})
                            matches.append({
                                "file": match_data.get("path", {}).get("text"),
                                "line": match_data.get("line_number"),
                                "text": match_data.get("lines", {}).get("text", "").strip(),
                                "column": match_data.get("submatches", [{}])[0].get("start", 0)
                            })
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Found {len(matches)} matches for '{query}'")
            return matches
            
        except FileNotFoundError:
            # Fallback to grep if ripgrep not installed
            cmd = ["grep", "-n", "-r", query, path]
            if file_type:
                cmd.extend(["--include", f"*.{file_type}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            matches = []
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        matches.append({
                            "file": parts[0],
                            "line": int(parts[1]) if parts[1].isdigit() else 0,
                            "text": parts[2].strip()
                        })
            
            return matches


# Singleton instances for easy access
file_tools = LiveFileSystemTools()
git_tools = LiveGitTools()
code_tools = LiveCodeTools()
search_tools = LiveSearchTools()


# Unified tool executor
async def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Execute any tool by name."""
    
    tools_map = {
        # File system
        "fs.read": file_tools.read_file,
        "fs.write": file_tools.write_file,
        "fs.list": file_tools.list_directory,
        "fs.delete": file_tools.delete_file,
        
        # Git
        "git.status": git_tools.git_status,
        "git.diff": git_tools.git_diff,
        "git.add": git_tools.git_add,
        "git.commit": git_tools.git_commit,
        "git.branch": git_tools.git_branch,
        
        # Code
        "code.test": code_tools.run_tests,
        "code.lint": code_tools.run_linter,
        "code.execute": code_tools.execute_code,
        "code.search": search_tools.search_code,
    }
    
    if tool_name not in tools_map:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}
    
    try:
        result = await tools_map[tool_name](**kwargs)
        return result
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test the tools
    async def test():
        print("Testing live tools...")
        
        # Test file read
        content = await file_tools.read_file("README.md")
        print(f"✅ Read README.md: {len(content)} bytes")
        
        # Test git status
        status = await git_tools.git_status()
        print(f"✅ Git status: {status}")
        
        # Test code search
        matches = await search_tools.search_code("async def", file_type="py")
        print(f"✅ Found {len(matches)} async functions")
    
    asyncio.run(test())