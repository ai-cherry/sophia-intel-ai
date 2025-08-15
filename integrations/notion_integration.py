#!/usr/bin/env python3
"""
SOPHIA Intel - Notion API Integration
Provides seamless integration with Notion for knowledge management and documentation.
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionIntegration:
    """Notion API integration for SOPHIA Intel platform."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Notion integration with API key."""
        self.api_key = api_key or os.environ.get('NOTION_API_KEY')
        if not self.api_key:
            raise ValueError("Notion API key is required")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Notion integration initialized")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Notion API."""
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info("Notion API connection successful")
                return {
                    "status": "success",
                    "user": user_info.get("name", "Unknown"),
                    "workspace": user_info.get("workspace_name", "Unknown")
                }
            else:
                logger.error(f"Notion API connection failed: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"API returned {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Notion API connection error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def search_databases(self, query: str = "") -> List[Dict[str, Any]]:
        """Search for databases in the workspace."""
        try:
            payload = {
                "filter": {
                    "value": "database",
                    "property": "object"
                }
            }
            
            if query:
                payload["query"] = query
            
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                databases = []
                
                for db in results:
                    if db.get("object") == "database":
                        databases.append({
                            "id": db.get("id"),
                            "title": db.get("title", [{}])[0].get("plain_text", "Untitled"),
                            "url": db.get("url"),
                            "created_time": db.get("created_time"),
                            "last_edited_time": db.get("last_edited_time")
                        })
                
                logger.info(f"Found {len(databases)} databases")
                return databases
            else:
                logger.error(f"Database search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Database search error: {str(e)}")
            return []
    
    def create_page(self, database_id: str, properties: Dict[str, Any], 
                   content: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a new page in a database."""
        try:
            payload = {
                "parent": {"database_id": database_id},
                "properties": properties
            }
            
            if content:
                payload["children"] = content
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                page = response.json()
                logger.info(f"Created page: {page.get('id')}")
                return {
                    "status": "success",
                    "page_id": page.get("id"),
                    "url": page.get("url")
                }
            else:
                logger.error(f"Page creation failed: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"API returned {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Page creation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def query_database(self, database_id: str, filter_criteria: Optional[Dict] = None,
                      sorts: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Query pages from a database."""
        try:
            payload = {}
            
            if filter_criteria:
                payload["filter"] = filter_criteria
            
            if sorts:
                payload["sorts"] = sorts
            
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                pages = []
                
                for page in results:
                    pages.append({
                        "id": page.get("id"),
                        "url": page.get("url"),
                        "properties": page.get("properties", {}),
                        "created_time": page.get("created_time"),
                        "last_edited_time": page.get("last_edited_time")
                    })
                
                logger.info(f"Retrieved {len(pages)} pages from database")
                return pages
            else:
                logger.error(f"Database query failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return []
    
    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update properties of an existing page."""
        try:
            payload = {"properties": properties}
            
            response = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                page = response.json()
                logger.info(f"Updated page: {page_id}")
                return {
                    "status": "success",
                    "page_id": page.get("id"),
                    "url": page.get("url")
                }
            else:
                logger.error(f"Page update failed: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"API returned {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Page update error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def create_mission_log(self, mission_title: str, status: str, 
                          details: str, database_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a mission log entry in Notion."""
        if not database_id:
            # Try to find a missions database
            databases = self.search_databases("missions")
            if not databases:
                return {
                    "status": "error",
                    "message": "No missions database found"
                }
            database_id = databases[0]["id"]
        
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": mission_title
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": status
                }
            },
            "Created": {
                "date": {
                    "start": datetime.utcnow().isoformat()
                }
            }
        }
        
        content = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": details
                            }
                        }
                    ]
                }
            }
        ]
        
        return self.create_page(database_id, properties, content)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Notion integration."""
        connection_test = self.test_connection()
        
        if connection_test["status"] == "success":
            databases = self.search_databases()
            return {
                "status": "healthy",
                "connection": "active",
                "databases_count": len(databases),
                "user": connection_test.get("user"),
                "workspace": connection_test.get("workspace"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": connection_test.get("message"),
                "timestamp": datetime.utcnow().isoformat()
            }

def main():
    """Test the Notion integration."""
    try:
        notion = NotionIntegration()
        
        print("🔍 Testing Notion API connection...")
        connection = notion.test_connection()
        print(f"Connection: {connection}")
        
        print("\n📊 Searching for databases...")
        databases = notion.search_databases()
        print(f"Found {len(databases)} databases:")
        for db in databases[:3]:  # Show first 3
            print(f"  - {db['title']} ({db['id']})")
        
        print("\n💊 Health status:")
        health = notion.get_health_status()
        print(json.dumps(health, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()

