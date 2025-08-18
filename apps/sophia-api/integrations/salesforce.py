from fastapi import APIRouter, HTTPException
import requests
import os
import logging

router = APIRouter(prefix="/api/v1/integrations/salesforce")
logger = logging.getLogger(__name__)

@router.post("/query")
async def salesforce_query(data: dict):
    """Execute SOQL query against Salesforce"""
    try:
        access_token = os.getenv('SALESFORCE_ACCESS_TOKEN')
        if not access_token:
            raise HTTPException(status_code=503, detail="Salesforce access token not configured")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"https://api.salesforce.com/services/data/v60.0/query?q={data['soql']}",
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Salesforce query: {data['soql']}")
        return response.json()
    except Exception as e:
        logger.error(f"Salesforce query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def salesforce_create(data: dict):
    """Create record in Salesforce"""
    try:
        access_token = os.getenv('SALESFORCE_ACCESS_TOKEN')
        if not access_token:
            raise HTTPException(status_code=503, detail="Salesforce access token not configured")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"https://api.salesforce.com/services/data/v60.0/sobjects/{data['object_type']}/",
            json=data['fields'],
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Salesforce record created: {data['object_type']}")
        return response.json()
    except Exception as e:
        logger.error(f"Salesforce create failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/objects")
async def salesforce_objects():
    """List available Salesforce objects"""
    try:
        access_token = os.getenv('SALESFORCE_ACCESS_TOKEN')
        if not access_token:
            raise HTTPException(status_code=503, detail="Salesforce access token not configured")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://api.salesforce.com/services/data/v60.0/sobjects/",
            headers=headers
        )
        response.raise_for_status()
        logger.info("Salesforce objects retrieved")
        return response.json()
    except Exception as e:
        logger.error(f"Salesforce objects failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

