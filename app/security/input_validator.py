import re
from typing import Dict, Any

def sanitize_input(text: str) -> str:
    """Remove potentially dangerous characters from user input"""
    # Remove HTML tags and special characters
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[&<>"\'%]', '', text)
    return text

def validate_request(request_data: Dict[str, Any]) -> bool:
    """Validate request data against security rules"""
    # Validate text length
    if 'text' in request_data and len(request_data['text']) > 10000:
        return False
    
    # Validate model name format
    if 'model' in request_data and not re.match(r'^[a-zA-Z0-9\-_]+$', request_data['model']):
        return False
    
    return True

def validate_api_key(api_key: str) -> bool:
    """Validate API key format and length"""
    return bool(api_key) and len(api_key) >= 32
