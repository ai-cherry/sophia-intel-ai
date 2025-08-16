"""
SOPHIA Intel Notion Sync MCP Server Routes
CEO governance layer for canonical principles and knowledge management
"""

from flask import Blueprint, request, jsonify
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
import json

# Create blueprint
notion_bp = Blueprint('notion', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionSyncMCP:
    """Notion Sync MCP for CEO governance and knowledge management"""
    
    def __init__(self):
        # Get API key from environment variables (populated by Kubernetes secrets)
        self.notion_api_key = os.getenv("NOTION_API_KEY")
        
        # Notion API configuration
        self.base_url = "https://api.notion.com/v1"
        self.session = requests.Session()
        
        if self.notion_api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            })
        
        # Database IDs (these would be configured via environment variables)
        self.canonical_principles_db = os.getenv("NOTION_CANONICAL_PRINCIPLES_DB")
        self.knowledge_base_db = os.getenv("NOTION_KNOWLEDGE_BASE_DB")
        
        logger.info("Notion Sync MCP initialized for CEO governance")
    
    def push_principle(self, principle: Dict) -> Dict:
        """Push a canonical principle to Notion for CEO review"""
        try:
            if not self.notion_api_key:
                return {"error": "Notion API key not configured"}
            
            if not self.canonical_principles_db:
                return {"error": "Canonical principles database not configured"}
            
            # Create page in Notion database
            endpoint = f"{self.base_url}/pages"
            
            payload = {
                "parent": {"database_id": self.canonical_principles_db},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": principle.get("title", "Untitled Principle")}}]
                    },
                    "Description": {
                        "rich_text": [{"text": {"content": principle.get("description", "")}}]
                    },
                    "Category": {
                        "select": {"name": principle.get("category", "General")}
                    },
                    "Priority": {
                        "select": {"name": principle.get("priority", "Medium")}
                    },
                    "Status": {
                        "select": {"name": "Pending Review"}
                    },
                    "Source": {
                        "rich_text": [{"text": {"content": principle.get("source", "SOPHIA AI")}}]
                    },
                    "Created Date": {
                        "date": {"start": datetime.utcnow().isoformat()}
                    }
                }
            }
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "notion_page_id": data["id"],
                    "url": data["url"],
                    "status": "pending_review",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"Notion API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to push principle: {str(e)}"}
    
    def get_pending_principles(self) -> Dict:
        """Get principles awaiting CEO approval"""
        try:
            if not self.notion_api_key:
                return {"error": "Notion API key not configured"}
            
            if not self.canonical_principles_db:
                return {"error": "Canonical principles database not configured"}
            
            # Query database for pending principles
            endpoint = f"{self.base_url}/databases/{self.canonical_principles_db}/query"
            
            payload = {
                "filter": {
                    "property": "Status",
                    "select": {"equals": "Pending Review"}
                },
                "sorts": [
                    {
                        "property": "Created Date",
                        "direction": "descending"
                    }
                ]
            }
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                principles = []
                
                for page in data.get("results", []):
                    properties = page.get("properties", {})
                    principles.append({
                        "id": page["id"],
                        "title": self._extract_title(properties.get("Title", {})),
                        "description": self._extract_rich_text(properties.get("Description", {})),
                        "category": self._extract_select(properties.get("Category", {})),
                        "priority": self._extract_select(properties.get("Priority", {})),
                        "source": self._extract_rich_text(properties.get("Source", {})),
                        "created_date": self._extract_date(properties.get("Created Date", {})),
                        "url": page["url"]
                    })
                
                return {
                    "pending_principles": principles,
                    "count": len(principles),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"Notion API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to get pending principles: {str(e)}"}
    
    def approve_principle(self, page_id: str, badge: str = "Gold") -> Dict:
        """Approve a principle and assign badge (Gold/Silver/Bronze)"""
        try:
            if not self.notion_api_key:
                return {"error": "Notion API key not configured"}
            
            # Update page properties
            endpoint = f"{self.base_url}/pages/{page_id}"
            
            payload = {
                "properties": {
                    "Status": {
                        "select": {"name": "Approved"}
                    },
                    "Badge": {
                        "select": {"name": badge}
                    },
                    "Approved Date": {
                        "date": {"start": datetime.utcnow().isoformat()}
                    }
                }
            }
            
            response = self.session.patch(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "page_id": page_id,
                    "status": "approved",
                    "badge": badge,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"Notion API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to approve principle: {str(e)}"}
    
    def sync_knowledge_base(self, knowledge_items: List[Dict]) -> Dict:
        """Sync knowledge base items to Notion"""
        try:
            if not self.notion_api_key:
                return {"error": "Notion API key not configured"}
            
            if not self.knowledge_base_db:
                return {"error": "Knowledge base database not configured"}
            
            results = []
            errors = []
            
            for item in knowledge_items:
                try:
                    endpoint = f"{self.base_url}/pages"
                    
                    payload = {
                        "parent": {"database_id": self.knowledge_base_db},
                        "properties": {
                            "Title": {
                                "title": [{"text": {"content": item.get("title", "Untitled")}}]
                            },
                            "Content": {
                                "rich_text": [{"text": {"content": item.get("content", "")[:2000]}}]  # Notion limit
                            },
                            "Type": {
                                "select": {"name": item.get("type", "General")}
                            },
                            "Source": {
                                "url": item.get("source_url", "")
                            },
                            "Tags": {
                                "multi_select": [{"name": tag} for tag in item.get("tags", [])]
                            }
                        }
                    }
                    
                    response = self.session.post(endpoint, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        results.append({
                            "title": item.get("title"),
                            "notion_page_id": data["id"],
                            "url": data["url"]
                        })
                    else:
                        errors.append({
                            "title": item.get("title"),
                            "error": f"HTTP {response.status_code}"
                        })
                        
                except Exception as e:
                    errors.append({
                        "title": item.get("title", "Unknown"),
                        "error": str(e)
                    })
            
            return {
                "synced_items": results,
                "errors": errors,
                "total_processed": len(knowledge_items),
                "successful": len(results),
                "failed": len(errors),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_workspace_info(self) -> Dict:
        """Get Notion workspace information"""
        try:
            if not self.notion_api_key:
                return {"error": "Notion API key not configured"}
            
            # Get user info
            endpoint = f"{self.base_url}/users/me"
            response = self.session.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Get databases info
                databases_info = []
                if self.canonical_principles_db:
                    db_endpoint = f"{self.base_url}/databases/{self.canonical_principles_db}"
                    db_response = self.session.get(db_endpoint, timeout=10)
                    if db_response.status_code == 200:
                        db_data = db_response.json()
                        databases_info.append({
                            "id": self.canonical_principles_db,
                            "title": self._extract_title(db_data.get("title", {})),
                            "type": "canonical_principles"
                        })
                
                return {
                    "workspace": {
                        "user": user_data.get("name", "Unknown"),
                        "user_id": user_data.get("id"),
                        "avatar_url": user_data.get("avatar_url")
                    },
                    "databases": databases_info,
                    "configuration": {
                        "canonical_principles_db": bool(self.canonical_principles_db),
                        "knowledge_base_db": bool(self.knowledge_base_db)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"Notion API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to get workspace info: {str(e)}"}
    
    def _extract_title(self, title_property: Dict) -> str:
        """Extract title from Notion property"""
        try:
            return title_property.get("title", [{}])[0].get("text", {}).get("content", "")
        except (IndexError, KeyError):
            return ""
    
    def _extract_rich_text(self, rich_text_property: Dict) -> str:
        """Extract rich text from Notion property"""
        try:
            return rich_text_property.get("rich_text", [{}])[0].get("text", {}).get("content", "")
        except (IndexError, KeyError):
            return ""
    
    def _extract_select(self, select_property: Dict) -> str:
        """Extract select value from Notion property"""
        try:
            return select_property.get("select", {}).get("name", "")
        except KeyError:
            return ""
    
    def _extract_date(self, date_property: Dict) -> str:
        """Extract date from Notion property"""
        try:
            return date_property.get("date", {}).get("start", "")
        except KeyError:
            return ""

# Initialize notion sync MCP
notion_sync_mcp = NotionSyncMCP()

@notion_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "service": "notion-sync-mcp",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "notion_configured": bool(notion_sync_mcp.notion_api_key)
    })

@notion_bp.route('/workspace', methods=['GET'])
def get_workspace():
    """Get Notion workspace information"""
    return jsonify(notion_sync_mcp.get_workspace_info())

@notion_bp.route('/principles/push', methods=['POST'])
def push_principle():
    """Push a canonical principle for CEO review"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        result = notion_sync_mcp.push_principle(data)
        
        if "error" in result:
            return jsonify(result), 400
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notion_bp.route('/principles/pending', methods=['GET'])
def get_pending_principles():
    """Get principles awaiting approval"""
    return jsonify(notion_sync_mcp.get_pending_principles())

@notion_bp.route('/principles/approve', methods=['POST'])
def approve_principle():
    """Approve a principle with badge assignment"""
    try:
        data = request.get_json()
        if not data or 'page_id' not in data:
            return jsonify({"error": "Missing 'page_id' field in request"}), 400
        
        page_id = data['page_id']
        badge = data.get('badge', 'Gold')
        
        result = notion_sync_mcp.approve_principle(page_id, badge)
        
        if "error" in result:
            return jsonify(result), 400
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notion_bp.route('/knowledge/sync', methods=['POST'])
def sync_knowledge():
    """Sync knowledge base items to Notion"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({"error": "Missing 'items' field in request"}), 400
        
        items = data['items']
        
        if not isinstance(items, list):
            return jsonify({"error": "'items' must be a list"}), 400
        
        result = notion_sync_mcp.sync_knowledge_base(items)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notion_bp.route('/test', methods=['GET'])
def test_notion():
    """Test Notion integration"""
    workspace_info = notion_sync_mcp.get_workspace_info()
    
    if "error" in workspace_info:
        return jsonify({"test_status": "failed", "error": workspace_info["error"]}), 500
    else:
        return jsonify({
            "test_status": "success",
            "workspace": workspace_info["workspace"],
            "databases_configured": len(workspace_info["databases"]),
            "timestamp": workspace_info["timestamp"]
        })

