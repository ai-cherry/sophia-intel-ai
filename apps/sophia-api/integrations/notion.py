from fastapi import APIRouter, HTTPException
import requests
import os
import logging

router = APIRouter(prefix="/api/v1/integrations/notion")
logger = logging.getLogger(__name__)

@router.post("/query")
async def notion_query(data: dict):
    """Query Notion database"""
    try:
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            raise HTTPException(status_code=503, detail="Notion API key not configured")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        response = requests.post(
            f"https://api.notion.com/v1/databases/{data['database_id']}/query",
            json=data.get('filter', {}),
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Notion query: {data['database_id']}")
        return response.json()
    except Exception as e:
        logger.error(f"Notion query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_page")
async def notion_create_page(data: dict):
    """Create page in Notion"""
    try:
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            raise HTTPException(status_code=503, detail="Notion API key not configured")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        response = requests.post(
            "https://api.notion.com/v1/pages",
            json={
                "parent": {"database_id": data["database_id"]},
                "properties": data["properties"]
            },
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Notion page created in {data['database_id']}")
        return response.json()
    except Exception as e:
        logger.error(f"Notion create page failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/databases")
async def notion_databases():
    """List accessible Notion databases"""
    try:
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            raise HTTPException(status_code=503, detail="Notion API key not configured")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28"
        }
        response = requests.post(
            "https://api.notion.com/v1/search",
            json={"filter": {"property": "object", "value": "database"}},
            headers=headers
        )
        response.raise_for_status()
        logger.info("Notion databases retrieved")
        return response.json()
    except Exception as e:
        logger.error(f"Notion databases failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

