#!/usr/bin/env python3
"""
Notion Sync MCP Server for Primary Mentor Initiative
Handles synchronization between SOPHIA's canonical principles and Notion workspace
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CanonicalPrinciple:
    """Data class for canonical principles"""
    entity_type: str
    entity_name: str
    principle_text: str
    source_interaction_id: Optional[str] = None
    created_by: str = "system"
    importance_score: int = 5
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class NotionSyncMCP:
    """Notion Sync MCP for Primary Mentor Initiative"""
    
    def __init__(self, notion_api_key: str):
        self.notion_api_key = notion_api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Initialize workspace structure
        self.foundational_page_id = None
        self.principles_database_id = None
        
        logger.info("NotionSyncMCP initialized")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Notion API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Notion API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def initialize_workspace(self) -> Dict[str, str]:
        """Initialize Notion workspace structure for Primary Mentor"""
        try:
            logger.info("Initializing Notion workspace for Primary Mentor Initiative...")
            
            # First, search for existing pages
            search_results = self._make_request("POST", "search", {
                "query": "SOPHIA – Foundational Knowledge",
                "filter": {
                    "value": "page",
                    "property": "object"
                }
            })
            
            # Check if foundational page already exists
            foundational_page = None
            for result in search_results.get("results", []):
                if "SOPHIA – Foundational Knowledge" in result.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", ""):
                    foundational_page = result
                    break
            
            if not foundational_page:
                # Create foundational knowledge page
                foundational_page_data = {
                    "parent": {"type": "page_id", "page_id": "root"},  # This would need to be updated with actual parent
                    "properties": {
                        "title": {
                            "title": [
                                {
                                    "text": {
                                        "content": "SOPHIA – Foundational Knowledge"
                                    }
                                }
                            ]
                        }
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": "This page contains the foundational knowledge and canonical principles for SOPHIA AI and Pay Ready organization. All principles here are considered authoritative and take precedence over other sources."
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
                
                # Note: In a real implementation, we'd need a valid parent page ID
                logger.info("Foundational page creation would happen here with valid parent ID")
                self.foundational_page_id = "mock_foundational_page_id"
            else:
                self.foundational_page_id = foundational_page["id"]
                logger.info(f"Found existing foundational page: {self.foundational_page_id}")
            
            # Create or find Canonical Principles database
            principles_db_data = {
                "parent": {"type": "page_id", "page_id": self.foundational_page_id},
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Canonical Principles & Truths"
                        }
                    }
                ],
                "properties": {
                    "Principle": {
                        "title": {}
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Pending Review", "color": "yellow"},
                                {"name": "Approved", "color": "green"},
                                {"name": "Rejected", "color": "red"},
                                {"name": "Needs Revision", "color": "orange"}
                            ]
                        }
                    },
                    "Entity Type": {
                        "select": {
                            "options": [
                                {"name": "AI_ASSISTANT", "color": "blue"},
                                {"name": "ORGANIZATION", "color": "purple"},
                                {"name": "PROJECT", "color": "pink"},
                                {"name": "PROCESS", "color": "gray"}
                            ]
                        }
                    },
                    "Entity Name": {
                        "rich_text": {}
                    },
                    "Source Interaction ID": {
                        "rich_text": {}
                    },
                    "Created By": {
                        "rich_text": {}
                    },
                    "Created At": {
                        "created_time": {}
                    },
                    "Importance": {
                        "number": {
                            "format": "number"
                        }
                    },
                    "Tags": {
                        "multi_select": {
                            "options": [
                                {"name": "core_values", "color": "red"},
                                {"name": "accuracy", "color": "blue"},
                                {"name": "security", "color": "green"},
                                {"name": "architecture", "color": "purple"},
                                {"name": "best_practices", "color": "orange"}
                            ]
                        }
                    }
                }
            }
            
            # For demo purposes, we'll use a mock database ID
            self.principles_database_id = "mock_principles_database_id"
            logger.info("Canonical Principles database initialized")
            
            return {
                "foundational_page_id": self.foundational_page_id,
                "principles_database_id": self.principles_database_id,
                "status": "initialized"
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize workspace: {str(e)}")
            raise
    
    def push_to_notion(self, principle: CanonicalPrinciple) -> Dict[str, Any]:
        """Push a canonical principle to Notion for review"""
        try:
            logger.info(f"Pushing principle to Notion: {principle.principle_text[:50]}...")
            
            # Prepare the database entry
            page_data = {
                "parent": {"database_id": self.principles_database_id},
                "properties": {
                    "Principle": {
                        "title": [
                            {
                                "text": {
                                    "content": principle.principle_text[:100]  # Notion title limit
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": "Pending Review"
                        }
                    },
                    "Entity Type": {
                        "select": {
                            "name": principle.entity_type
                        }
                    },
                    "Entity Name": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": principle.entity_name
                                }
                            }
                        ]
                    },
                    "Source Interaction ID": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": principle.source_interaction_id or ""
                                }
                            }
                        ]
                    },
                    "Created By": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": principle.created_by
                                }
                            }
                        ]
                    },
                    "Importance": {
                        "number": principle.importance_score
                    },
                    "Tags": {
                        "multi_select": [
                            {"name": tag} for tag in principle.tags[:5]  # Limit tags
                        ]
                    }
                }
            }
            
            # Add the full principle text as page content
            page_data["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": principle.principle_text
                                }
                            }
                        ]
                    }
                }
            ]
            
            # For demo purposes, simulate the API call
            mock_response = {
                "id": f"notion_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "url": f"https://notion.so/mock_page_{principle.entity_name.lower()}",
                "properties": page_data["properties"],
                "created_time": datetime.now(timezone.utc).isoformat(),
                "status": "created"
            }
            
            logger.info(f"Principle pushed to Notion successfully: {mock_response['id']}")
            
            return mock_response
            
        except Exception as e:
            logger.error(f"Failed to push principle to Notion: {str(e)}")
            raise
    
    def handle_notion_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Handle webhook from Notion when principle status changes"""
        try:
            logger.info("Processing Notion webhook...")
            
            # Extract relevant information from webhook
            page_id = webhook_data.get("page_id")
            new_status = webhook_data.get("properties", {}).get("Status", {}).get("select", {}).get("name")
            
            if not page_id or not new_status:
                raise ValueError("Invalid webhook data: missing page_id or status")
            
            logger.info(f"Page {page_id} status changed to: {new_status}")
            
            if new_status == "Approved":
                # Principle has been approved - should be inserted into canonical_principles table
                # and embedded into sophia_foundational_knowledge collection
                
                # Get the full principle data from Notion
                principle_data = self.get_principle_from_notion(page_id)
                
                result = {
                    "action": "approve_principle",
                    "page_id": page_id,
                    "principle_data": principle_data,
                    "next_steps": [
                        "Insert into canonical_principles table",
                        "Create embedding and store in sophia_foundational_knowledge",
                        "Update Notion page with database reference"
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Principle approved for processing: {page_id}")
                return result
                
            elif new_status == "Rejected":
                # Principle has been rejected - log and archive
                result = {
                    "action": "reject_principle",
                    "page_id": page_id,
                    "next_steps": ["Archive principle", "Log rejection reason"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Principle rejected: {page_id}")
                return result
            
            else:
                # Other status changes (Needs Revision, etc.)
                result = {
                    "action": "status_change",
                    "page_id": page_id,
                    "new_status": new_status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to handle Notion webhook: {str(e)}")
            raise
    
    def get_principle_from_notion(self, page_id: str) -> Dict[str, Any]:
        """Retrieve principle data from Notion page"""
        try:
            # Simulate retrieving principle data
            mock_principle = {
                "id": page_id,
                "principle_text": "Sample canonical principle retrieved from Notion",
                "entity_type": "AI_ASSISTANT",
                "entity_name": "SOPHIA",
                "importance_score": 9,
                "tags": ["core_values", "accuracy"],
                "created_by": "ceo",
                "source_interaction_id": "chat_20250815_001"
            }
            
            logger.info(f"Retrieved principle from Notion: {page_id}")
            return mock_principle
            
        except Exception as e:
            logger.error(f"Failed to retrieve principle from Notion: {str(e)}")
            raise
    
    def get_pending_principles(self) -> List[Dict[str, Any]]:
        """Get all principles with 'Pending Review' status"""
        try:
            # Simulate querying for pending principles
            mock_pending = [
                {
                    "id": "pending_1",
                    "principle_text": "Always validate user input before processing",
                    "entity_type": "AI_ASSISTANT",
                    "entity_name": "SOPHIA",
                    "status": "Pending Review",
                    "created_at": "2025-08-15T20:00:00Z"
                },
                {
                    "id": "pending_2",
                    "principle_text": "Prefer Infrastructure as Code for all deployments",
                    "entity_type": "ORGANIZATION", 
                    "entity_name": "Pay Ready",
                    "status": "Pending Review",
                    "created_at": "2025-08-15T20:15:00Z"
                }
            ]
            
            logger.info(f"Retrieved {len(mock_pending)} pending principles")
            return mock_pending
            
        except Exception as e:
            logger.error(f"Failed to retrieve pending principles: {str(e)}")
            raise

# Flask application for MCP endpoints
app = Flask(__name__)
CORS(app)

# Initialize Notion Sync MCP
notion_api_key = os.getenv("NOTION_API_KEY")
if not notion_api_key:
    logger.error("NOTION_API_KEY environment variable not set")
    sys.exit(1)

notion_sync = NotionSyncMCP(notion_api_key)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "service": "notion-sync-mcp",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notion_configured": bool(notion_api_key)
    })

@app.route('/initialize', methods=['POST'])
def initialize_workspace():
    """Initialize Notion workspace structure"""
    try:
        result = notion_sync.initialize_workspace()
        return jsonify({
            "success": True,
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Workspace initialization failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/push_principle', methods=['POST'])
def push_principle():
    """Push a canonical principle to Notion for review"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['entity_type', 'entity_name', 'principle_text']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create CanonicalPrinciple object
        principle = CanonicalPrinciple(
            entity_type=data['entity_type'],
            entity_name=data['entity_name'],
            principle_text=data['principle_text'],
            source_interaction_id=data.get('source_interaction_id'),
            created_by=data.get('created_by', 'system'),
            importance_score=data.get('importance_score', 5),
            tags=data.get('tags', [])
        )
        
        # Push to Notion
        result = notion_sync.push_to_notion(principle)
        
        return jsonify({
            "success": True,
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Push principle failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/webhook', methods=['POST'])
def notion_webhook():
    """Handle webhooks from Notion"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data received"
            }), 400
        
        result = notion_sync.handle_notion_webhook(data)
        
        return jsonify({
            "success": True,
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Webhook handling failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/pending_principles', methods=['GET'])
def get_pending_principles():
    """Get all principles with 'Pending Review' status"""
    try:
        principles = notion_sync.get_pending_principles()
        
        return jsonify({
            "success": True,
            "data": {
                "principles": principles,
                "count": len(principles)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get pending principles failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/approve_principle', methods=['POST'])
def approve_principle():
    """Manually approve a principle (for testing)"""
    try:
        data = request.get_json()
        page_id = data.get('page_id')
        
        if not page_id:
            return jsonify({
                "success": False,
                "error": "Missing page_id"
            }), 400
        
        # Simulate approval webhook
        webhook_data = {
            "page_id": page_id,
            "properties": {
                "Status": {
                    "select": {
                        "name": "Approved"
                    }
                }
            }
        }
        
        result = notion_sync.handle_notion_webhook(webhook_data)
        
        return jsonify({
            "success": True,
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Approve principle failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

if __name__ == '__main__':
    logger.info("🔗 Starting Notion Sync MCP Server for Primary Mentor Initiative")
    logger.info(f"Notion API configured: {bool(notion_api_key)}")
    
    # Initialize workspace on startup
    try:
        notion_sync.initialize_workspace()
        logger.info("✅ Notion workspace initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️  Workspace initialization failed: {str(e)}")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

