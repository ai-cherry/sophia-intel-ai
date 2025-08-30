"""
JSON validation utilities for structured agent outputs.
"""

import json
from typing import List, Dict, Any

def as_json_or_error(content: str, required: List[str]) -> Dict[str, Any]:
    """
    Parse JSON content and validate required fields.
    
    Args:
        content: Raw string content to parse
        required: List of required field names
    
    Returns:
        Parsed dict if valid, or dict with "_error" key if invalid
    """
    try:
        data = json.loads(content)
    except Exception as e:
        return {"_error": "invalid-json", "raw": content, "exception": str(e)}
    
    missing = [k for k in required if k not in data]
    if missing:
        return {"_error": f"missing-keys:{missing}", "raw": data}
    
    return data

def extract_json_from_markdown(content: str) -> str:
    """
    Extract JSON from markdown code blocks if present.
    """
    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        if end > start:
            return content[start:end].strip()
    elif "```" in content:
        start = content.find("```") + 3
        end = content.find("```", start)
        if end > start:
            return content[start:end].strip()
    return content