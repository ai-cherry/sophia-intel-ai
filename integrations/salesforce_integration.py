"""
Salesforce Integration for SOPHIA
Enables CRM operations, lead management, and sales automation
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SalesforceContact(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    lead_source: Optional[str] = "SOPHIA AI"

class SalesforceOpportunity(BaseModel):
    name: str
    account_id: str
    stage_name: str = "Prospecting"
    close_date: str
    amount: Optional[float] = None
    description: Optional[str] = None
    lead_source: Optional[str] = "SOPHIA AI"

class SalesforceTask(BaseModel):
    subject: str
    description: Optional[str] = None
    activity_date: Optional[str] = None
    priority: str = "Normal"
    status: str = "Not Started"
    who_id: Optional[str] = None  # Contact/Lead ID
    what_id: Optional[str] = None  # Account/Opportunity ID

class SalesforceClient:
    """Salesforce API client for SOPHIA integrations."""
    
    def __init__(self, instance_url: str = None, access_token: str = None):
        self.instance_url = instance_url or os.getenv("SALESFORCE_INSTANCE_URL")
        self.access_token = access_token or os.getenv("SALESFORCE_ACCESS_TOKEN")
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.username = os.getenv("SALESFORCE_USERNAME")
        self.password = os.getenv("SALESFORCE_PASSWORD")
        self.security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        
        self.api_version = "v58.0"
        self.base_url = f"{self.instance_url}/services/data/{self.api_version}"
        
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with Salesforce using OAuth2."""
        try:
            auth_url = f"{self.instance_url}/services/oauth2/token"
            
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": f"{self.password}{self.security_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    auth_url,
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    self.access_token = auth_data.get("access_token")
                    self.instance_url = auth_data.get("instance_url")
                    self.base_url = f"{self.instance_url}/services/data/{self.api_version}"
                    
                    logger.info("Salesforce authentication successful")
                    return {
                        "success": True,
                        "access_token": self.access_token,
                        "instance_url": self.instance_url
                    }
                else:
                    logger.error(f"Salesforce auth failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Authentication failed: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Salesforce authentication error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Salesforce API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def create_lead(self, contact: SalesforceContact) -> Dict[str, Any]:
        """Create a new lead in Salesforce."""
        try:
            lead_data = {
                "FirstName": contact.first_name,
                "LastName": contact.last_name,
                "Email": contact.email,
                "Company": contact.company or "Unknown",
                "LeadSource": contact.lead_source
            }
            
            if contact.phone:
                lead_data["Phone"] = contact.phone
            
            if contact.title:
                lead_data["Title"] = contact.title
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sobjects/Lead/",
                    headers=self._get_headers(),
                    json=lead_data,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Lead created: {result.get('id')}")
                    return {
                        "success": True,
                        "id": result.get("id"),
                        "lead_data": lead_data
                    }
                else:
                    logger.error(f"Lead creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Lead creation failed: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Lead creation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_opportunity(self, opportunity: SalesforceOpportunity) -> Dict[str, Any]:
        """Create a new opportunity in Salesforce."""
        try:
            opp_data = {
                "Name": opportunity.name,
                "AccountId": opportunity.account_id,
                "StageName": opportunity.stage_name,
                "CloseDate": opportunity.close_date,
                "LeadSource": opportunity.lead_source
            }
            
            if opportunity.amount:
                opp_data["Amount"] = opportunity.amount
            
            if opportunity.description:
                opp_data["Description"] = opportunity.description
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sobjects/Opportunity/",
                    headers=self._get_headers(),
                    json=opp_data,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Opportunity created: {result.get('id')}")
                    return {
                        "success": True,
                        "id": result.get("id"),
                        "opportunity_data": opp_data
                    }
                else:
                    logger.error(f"Opportunity creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Opportunity creation failed: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Opportunity creation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_task(self, task: SalesforceTask) -> Dict[str, Any]:
        """Create a new task in Salesforce."""
        try:
            task_data = {
                "Subject": task.subject,
                "Priority": task.priority,
                "Status": task.status
            }
            
            if task.description:
                task_data["Description"] = task.description
            
            if task.activity_date:
                task_data["ActivityDate"] = task.activity_date
            else:
                # Default to tomorrow
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                task_data["ActivityDate"] = tomorrow
            
            if task.who_id:
                task_data["WhoId"] = task.who_id
            
            if task.what_id:
                task_data["WhatId"] = task.what_id
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sobjects/Task/",
                    headers=self._get_headers(),
                    json=task_data,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Task created: {result.get('id')}")
                    return {
                        "success": True,
                        "id": result.get("id"),
                        "task_data": task_data
                    }
                else:
                    logger.error(f"Task creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Task creation failed: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Task creation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_contacts(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for contacts in Salesforce."""
        try:
            # SOSL search query
            search_query = f"FIND {{*{query}*}} IN ALL FIELDS RETURNING Contact(Id, FirstName, LastName, Email, Phone, Account.Name) LIMIT {limit}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search/",
                    headers=self._get_headers(),
                    params={"q": search_query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    contacts = result.get("searchRecords", [])
                    logger.info(f"Found {len(contacts)} contacts for query: {query}")
                    return contacts
                else:
                    logger.error(f"Contact search failed: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Contact search error: {e}")
            return []
    
    async def get_recent_opportunities(self, limit: int = 10) -> List[Dict]:
        """Get recent opportunities from Salesforce."""
        try:
            # SOQL query for recent opportunities
            query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name, Owner.Name FROM Opportunity ORDER BY CreatedDate DESC LIMIT {limit}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/query/",
                    headers=self._get_headers(),
                    params={"q": query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    opportunities = result.get("records", [])
                    logger.info(f"Retrieved {len(opportunities)} recent opportunities")
                    return opportunities
                else:
                    logger.error(f"Opportunity query failed: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Opportunity query error: {e}")
            return []
    
    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get sales pipeline summary."""
        try:
            # Query for pipeline data
            query = """
            SELECT StageName, COUNT(Id) RecordCount, SUM(Amount) TotalAmount 
            FROM Opportunity 
            WHERE IsClosed = false 
            GROUP BY StageName
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/query/",
                    headers=self._get_headers(),
                    params={"q": query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    pipeline_data = result.get("records", [])
                    
                    summary = {
                        "total_opportunities": sum(record.get("RecordCount", 0) for record in pipeline_data),
                        "total_value": sum(record.get("TotalAmount", 0) or 0 for record in pipeline_data),
                        "stages": pipeline_data,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                    
                    logger.info(f"Pipeline summary: {summary['total_opportunities']} opportunities, ${summary['total_value']:,.2f}")
                    return {
                        "success": True,
                        "summary": summary
                    }
                else:
                    logger.error(f"Pipeline query failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Pipeline query failed: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Pipeline summary error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_opportunity_stage(self, opportunity_id: str, new_stage: str) -> Dict[str, Any]:
        """Update opportunity stage."""
        try:
            update_data = {
                "StageName": new_stage
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/sobjects/Opportunity/{opportunity_id}",
                    headers=self._get_headers(),
                    json=update_data,
                    timeout=30.0
                )
                
                if response.status_code == 204:
                    logger.info(f"Opportunity {opportunity_id} updated to stage: {new_stage}")
                    return {
                        "success": True,
                        "opportunity_id": opportunity_id,
                        "new_stage": new_stage
                    }
                else:
                    logger.error(f"Opportunity update failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Update failed: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Opportunity update error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Salesforce API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sobjects/",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "sobjects_count": len(result.get("sobjects", [])),
                        "instance_url": self.instance_url,
                        "api_version": self.api_version
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Connection test failed: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Salesforce Automation
class SalesforceAutomation:
    """Automated Salesforce operations for SOPHIA."""
    
    def __init__(self, salesforce_client: SalesforceClient):
        self.sf = salesforce_client
    
    async def process_gong_call_insights(self, call_data: Dict) -> Dict[str, Any]:
        """Process Gong call insights and create Salesforce records."""
        
        results = {
            "leads_created": [],
            "tasks_created": [],
            "opportunities_updated": [],
            "errors": []
        }
        
        try:
            # Extract insights from Gong call data
            participants = call_data.get("participants", [])
            call_summary = call_data.get("summary", "")
            action_items = call_data.get("action_items", [])
            
            # Create leads for new contacts
            for participant in participants:
                if participant.get("is_external", False):
                    contact = SalesforceContact(
                        first_name=participant.get("first_name", ""),
                        last_name=participant.get("last_name", "Unknown"),
                        email=participant.get("email", ""),
                        company=participant.get("company", ""),
                        title=participant.get("title", ""),
                        lead_source="Gong Call"
                    )
                    
                    lead_result = await self.sf.create_lead(contact)
                    if lead_result.get("success"):
                        results["leads_created"].append(lead_result)
                    else:
                        results["errors"].append(f"Lead creation failed: {lead_result.get('error')}")
            
            # Create tasks for action items
            for action_item in action_items:
                task = SalesforceTask(
                    subject=f"Follow-up: {action_item.get('description', 'Gong call action item')}",
                    description=f"Action item from Gong call:\n{call_summary}",
                    priority="High" if action_item.get("urgent", False) else "Normal"
                )
                
                task_result = await self.sf.create_task(task)
                if task_result.get("success"):
                    results["tasks_created"].append(task_result)
                else:
                    results["errors"].append(f"Task creation failed: {task_result.get('error')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Gong call processing error: {e}")
            results["errors"].append(str(e))
            return results
    
    async def sync_with_linear_issues(self, linear_issues: List[Dict]) -> Dict[str, Any]:
        """Sync Linear issues with Salesforce tasks."""
        
        results = {
            "tasks_created": [],
            "tasks_updated": [],
            "errors": []
        }
        
        try:
            for issue in linear_issues:
                # Create Salesforce task for Linear issue
                task = SalesforceTask(
                    subject=f"Linear Issue: {issue.get('title', 'Untitled')}",
                    description=f"Linear Issue ID: {issue.get('id')}\n\n{issue.get('description', '')}",
                    priority="High" if issue.get('priority', 0) > 2 else "Normal",
                    status="In Progress" if issue.get('state', {}).get('name') == "In Progress" else "Not Started"
                )
                
                task_result = await self.sf.create_task(task)
                if task_result.get("success"):
                    results["tasks_created"].append(task_result)
                else:
                    results["errors"].append(f"Task creation failed: {task_result.get('error')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Linear sync error: {e}")
            results["errors"].append(str(e))
            return results

