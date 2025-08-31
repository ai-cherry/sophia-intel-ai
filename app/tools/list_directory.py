"""
List directory tool implementation for agent system.
Provides directory listing functionality for agents.
"""

import os
from typing import Dict, Any, List


class ListDirectory:
    """Directory listing tool."""
    
    def __call__(self, dir_path: str = ".") -> Dict[str, Any]:
        """List directory contents."""
        return list_directory(dir_path)


def list_directory(dir_path: str = ".") -> Dict[str, Any]:
    """List directory contents safely."""
    try:
        if not os.path.exists(dir_path):
            return {"error": f"Directory not found: {dir_path}"}
            
        items = []
        for item in os.listdir(dir_path):
            full_path = os.path.join(dir_path, item)
            try:
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(full_path) else "file",
                    "size": os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                })
            except (OSError, PermissionError):
                # Skip items we can't access
                items.append({
                    "name": item,
                    "type": "unknown",
                    "size": 0
                })
            
        return {
            "directory": dir_path,
            "items": items[:50],  # Limit to 50 items for performance
            "total": len(items),
            "success": True
        }
    except Exception as e:
        return {
            "directory": dir_path, 
            "error": str(e),
            "items": [],
            "total": 0,
            "success": False
        }