from fastapi import APIRouter, HTTPException
import requests
import os
import logging

router = APIRouter(prefix="/api/v1/integrations/slack")
logger = logging.getLogger(__name__)

@router.post("/message")
async def slack_message(data: dict):
    """Send message to Slack channel"""
    try:
        api_token = os.getenv('SLACK_API_TOKEN')
        if not api_token:
            raise HTTPException(status_code=503, detail="Slack API token not configured")
        
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            json={"channel": data["channel"], "text": data["text"]},
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Slack message sent to {data['channel']}")
        return response.json()
    except Exception as e:
        logger.error(f"Slack message failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channels")
async def slack_channels():
    """List Slack channels"""
    try:
        api_token = os.getenv('SLACK_API_TOKEN')
        if not api_token:
            raise HTTPException(status_code=503, detail="Slack API token not configured")
        
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.get(
            "https://slack.com/api/conversations.list",
            headers=headers
        )
        response.raise_for_status()
        logger.info("Slack channels retrieved")
        return response.json()
    except Exception as e:
        logger.error(f"Slack channels failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/file")
async def slack_file_upload(data: dict):
    """Upload file to Slack"""
    try:
        api_token = os.getenv('SLACK_API_TOKEN')
        if not api_token:
            raise HTTPException(status_code=503, detail="Slack API token not configured")
        
        headers = {"Authorization": f"Bearer {api_token}"}
        files = {"file": data["file_content"]}
        payload = {
            "channels": data["channel"],
            "title": data.get("title", "File upload"),
            "initial_comment": data.get("comment", "")
        }
        response = requests.post(
            "https://slack.com/api/files.upload",
            headers=headers,
            files=files,
            data=payload
        )
        response.raise_for_status()
        logger.info(f"Slack file uploaded to {data['channel']}")
        return response.json()
    except Exception as e:
        logger.error(f"Slack file upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

