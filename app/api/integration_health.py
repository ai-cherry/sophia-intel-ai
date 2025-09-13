from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import httpx
from datetime import datetime

router = APIRouter(prefix='/api/integrations')

async def check_salesforce() -> Dict[str, Any]:
    """Check Salesforce integration health"""
    try:
        if not os.getenv('SALESFORCE_USERNAME'):
            return {'status': 'error', 'message': 'Missing credentials'}
        # Add actual Salesforce health check here
        return {'status': 'healthy', 'last_check': datetime.now().isoformat()}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

async def check_slack() -> Dict[str, Any]:
    """Check Slack integration health"""
    try:
        token = os.getenv('SLACK_BOT_TOKEN')
        if not token:
            return {'status': 'error', 'message': 'Missing SLACK_BOT_TOKEN'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://slack.com/api/auth.test',
                headers={'Authorization': f'Bearer {token}'}
            )
            data = response.json()
            if data.get('ok'):
                return {'status': 'healthy', 'team': data.get('team')}
            return {'status': 'error', 'message': data.get('error')}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

async def check_hubspot() -> Dict[str, Any]:
    """Check HubSpot integration health"""
    try:
        api_key = os.getenv('HUBSPOT_PRIVATE_APP_KEY')
        if not api_key:
            return {'status': 'error', 'message': 'Missing HUBSPOT_PRIVATE_APP_KEY'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.hubapi.com/account-info/v3/details',
                headers={'Authorization': f'Bearer {api_key}'}
            )
            if response.status_code == 200:
                return {'status': 'healthy', 'account': response.json()}
            return {'status': 'error', 'code': response.status_code}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

async def check_gong() -> Dict[str, Any]:
    """Check Gong integration health"""
    try:
        api_key = os.getenv('GONG_API_KEY')
        if not api_key:
            return {'status': 'error', 'message': 'Missing GONG_API_KEY'}
        return {'status': 'healthy', 'message': 'Gong integration configured'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@router.get('/salesforce/health')
async def salesforce_health():
    return await check_salesforce()

@router.get('/slack/health')
async def slack_health():
    return await check_slack()

@router.get('/hubspot/health')
async def hubspot_health():
    return await check_hubspot()

@router.get('/gong/health')
async def gong_health():
    return await check_gong()

@router.get('/health')
async def all_health():
    """Check all integrations"""
    return {
        'salesforce': await check_salesforce(),
        'slack': await check_slack(),
        'hubspot': await check_hubspot(),
        'gong': await check_gong(),
        'timestamp': datetime.now().isoformat()
    }
