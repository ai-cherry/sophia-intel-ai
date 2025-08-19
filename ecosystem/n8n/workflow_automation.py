"""
SOPHIA Intel n8n Workflow Automation Integration
Phase 6 of V4 Mega Upgrade - Ecosystem Integration

Provides automated workflow orchestration using n8n for SOPHIA's autonomous operations
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@dataclass
class WorkflowTemplate:
    """n8n workflow template configuration"""
    name: str
    description: str
    trigger_type: str
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    settings: Dict[str, Any]

class N8NWorkflowAutomation:
    """
    n8n workflow automation integration for SOPHIA Intel.
    Provides automated workflow orchestration and process automation.
    """
    
    def __init__(self):
        self.n8n_base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.n8n_api_key = os.getenv("N8N_API_KEY")
        self.webhook_base_url = os.getenv("N8N_WEBHOOK_URL", "https://sophia-intel.fly.dev/webhooks/n8n")
        
        # Predefined workflow templates for SOPHIA operations
        self.workflow_templates = {
            "github_pr_automation": WorkflowTemplate(
                name="SOPHIA GitHub PR Automation",
                description="Automated PR creation, review, and deployment workflow",
                trigger_type="webhook",
                nodes=[
                    {
                        "name": "Webhook Trigger",
                        "type": "n8n-nodes-base.webhook",
                        "parameters": {
                            "path": "github-pr",
                            "httpMethod": "POST"
                        }
                    },
                    {
                        "name": "GitHub PR Creation",
                        "type": "n8n-nodes-base.github",
                        "parameters": {
                            "operation": "create",
                            "resource": "pullRequest",
                            "owner": "ai-cherry",
                            "repository": "sophia-intel"
                        }
                    },
                    {
                        "name": "Code Review Analysis",
                        "type": "n8n-nodes-base.httpRequest",
                        "parameters": {
                            "url": "https://sophia-intel.fly.dev/api/v1/ai/generate",
                            "method": "POST",
                            "body": {
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": "You are a code review expert. Analyze the PR changes and provide feedback."
                                    }
                                ],
                                "task_type": "coding",
                                "complexity": "medium"
                            }
                        }
                    },
                    {
                        "name": "Automated Deployment",
                        "type": "n8n-nodes-base.httpRequest",
                        "parameters": {
                            "url": "https://sophia-intel.fly.dev/api/v1/deploy",
                            "method": "POST"
                        }
                    }
                ],
                connections={
                    "Webhook Trigger": {
                        "main": [["GitHub PR Creation"]]
                    },
                    "GitHub PR Creation": {
                        "main": [["Code Review Analysis"]]
                    },
                    "Code Review Analysis": {
                        "main": [["Automated Deployment"]]
                    }
                },
                settings={
                    "executionOrder": "v1",
                    "saveManualExecutions": True,
                    "callerPolicy": "workflowsFromSameOwner"
                }
            ),
            
            "data_sync_automation": WorkflowTemplate(
                name="SOPHIA Data Sync Automation",
                description="Automated data synchronization across systems",
                trigger_type="schedule",
                nodes=[
                    {
                        "name": "Schedule Trigger",
                        "type": "n8n-nodes-base.cron",
                        "parameters": {
                            "rule": {
                                "interval": [{"field": "hours", "value": 1}]
                            }
                        }
                    },
                    {
                        "name": "Fetch Salesforce Data",
                        "type": "n8n-nodes-base.salesforce",
                        "parameters": {
                            "operation": "getAll",
                            "resource": "lead"
                        }
                    },
                    {
                        "name": "Sync to Database",
                        "type": "n8n-nodes-base.postgres",
                        "parameters": {
                            "operation": "insert",
                            "table": "leads"
                        }
                    },
                    {
                        "name": "Update Qdrant Vector DB",
                        "type": "n8n-nodes-base.httpRequest",
                        "parameters": {
                            "url": "https://sophia-intel.fly.dev/api/v1/vector/upsert",
                            "method": "POST"
                        }
                    },
                    {
                        "name": "Notify Slack",
                        "type": "n8n-nodes-base.slack",
                        "parameters": {
                            "operation": "postMessage",
                            "channel": "#sophia-intel"
                        }
                    }
                ],
                connections={
                    "Schedule Trigger": {
                        "main": [["Fetch Salesforce Data"]]
                    },
                    "Fetch Salesforce Data": {
                        "main": [["Sync to Database", "Update Qdrant Vector DB"]]
                    },
                    "Sync to Database": {
                        "main": [["Notify Slack"]]
                    },
                    "Update Qdrant Vector DB": {
                        "main": [["Notify Slack"]]
                    }
                },
                settings={
                    "executionOrder": "v1",
                    "saveManualExecutions": True
                }
            ),
            
            "monitoring_automation": WorkflowTemplate(
                name="SOPHIA Monitoring Automation",
                description="Automated system monitoring and alerting",
                trigger_type="webhook",
                nodes=[
                    {
                        "name": "Monitoring Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "parameters": {
                            "path": "monitoring-alert",
                            "httpMethod": "POST"
                        }
                    },
                    {
                        "name": "Analyze Alert",
                        "type": "n8n-nodes-base.httpRequest",
                        "parameters": {
                            "url": "https://sophia-intel.fly.dev/api/v1/ai/generate",
                            "method": "POST",
                            "body": {
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": "You are a system monitoring expert. Analyze the alert and provide recommendations."
                                    }
                                ],
                                "task_type": "analysis",
                                "complexity": "medium"
                            }
                        }
                    },
                    {
                        "name": "Create GitHub Issue",
                        "type": "n8n-nodes-base.github",
                        "parameters": {
                            "operation": "create",
                            "resource": "issue",
                            "owner": "ai-cherry",
                            "repository": "sophia-intel"
                        }
                    },
                    {
                        "name": "Send Slack Alert",
                        "type": "n8n-nodes-base.slack",
                        "parameters": {
                            "operation": "postMessage",
                            "channel": "#alerts"
                        }
                    }
                ],
                connections={
                    "Monitoring Webhook": {
                        "main": [["Analyze Alert"]]
                    },
                    "Analyze Alert": {
                        "main": [["Create GitHub Issue", "Send Slack Alert"]]
                    }
                },
                settings={
                    "executionOrder": "v1",
                    "saveManualExecutions": True
                }
            )
        }
        
        logger.info(f"Initialized n8n automation with {len(self.workflow_templates)} templates")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def create_workflow(self, template_name: str, custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new n8n workflow from template.
        
        Args:
            template_name: Name of the workflow template to use
            custom_params: Custom parameters to override template defaults
            
        Returns:
            Created workflow information
        """
        if template_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {template_name}")
        
        template = self.workflow_templates[template_name]
        
        # Build workflow definition
        workflow_def = {
            "name": template.name,
            "nodes": template.nodes.copy(),
            "connections": template.connections.copy(),
            "settings": template.settings.copy(),
            "staticData": {},
            "tags": ["sophia-intel", "automated", template_name],
            "meta": {
                "created_by": "SOPHIA Intel V4",
                "template": template_name,
                "description": template.description
            }
        }
        
        # Apply custom parameters
        if custom_params:
            workflow_def.update(custom_params)
        
        try:
            if self.n8n_api_key:
                # Use n8n API to create workflow
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "X-N8N-API-KEY": self.n8n_api_key,
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        f"{self.n8n_base_url}/api/v1/workflows",
                        json=workflow_def,
                        headers=headers
                    ) as response:
                        if response.status == 201:
                            result = await response.json()
                            logger.info(f"Created n8n workflow: {template.name}")
                            return {
                                "status": "created",
                                "workflow_id": result.get("id"),
                                "name": template.name,
                                "webhook_url": f"{self.webhook_base_url}/{template_name}",
                                "template": template_name
                            }
                        else:
                            error_text = await response.text()
                            raise Exception(f"n8n API error: {response.status} - {error_text}")
            else:
                # Return workflow definition for manual setup
                logger.warning("N8N_API_KEY not configured, returning workflow definition")
                return {
                    "status": "definition_ready",
                    "workflow_definition": workflow_def,
                    "name": template.name,
                    "template": template_name,
                    "setup_instructions": "Import this workflow definition into your n8n instance"
                }
                
        except Exception as e:
            logger.error(f"Error creating n8n workflow: {e}")
            raise e
    
    async def trigger_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a workflow execution.
        
        Args:
            workflow_id: ID of the workflow to trigger
            data: Data to pass to the workflow
            
        Returns:
            Execution result
        """
        try:
            if self.n8n_api_key:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "X-N8N-API-KEY": self.n8n_api_key,
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        f"{self.n8n_base_url}/api/v1/workflows/{workflow_id}/execute",
                        json=data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "status": "triggered",
                                "execution_id": result.get("id"),
                                "workflow_id": workflow_id
                            }
                        else:
                            error_text = await response.text()
                            raise Exception(f"n8n trigger error: {response.status} - {error_text}")
            else:
                # Simulate workflow trigger
                return {
                    "status": "simulated",
                    "workflow_id": workflow_id,
                    "message": "N8N_API_KEY not configured, workflow trigger simulated"
                }
                
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            raise e
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow"""
        try:
            if self.n8n_api_key:
                async with aiohttp.ClientSession() as session:
                    headers = {"X-N8N-API-KEY": self.n8n_api_key}
                    
                    async with session.get(
                        f"{self.n8n_base_url}/api/v1/workflows/{workflow_id}",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "status": "active" if result.get("active") else "inactive",
                                "name": result.get("name"),
                                "nodes_count": len(result.get("nodes", [])),
                                "last_updated": result.get("updatedAt")
                            }
                        else:
                            return {"status": "not_found"}
            else:
                return {"status": "api_not_configured"}
                
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available workflow templates"""
        return {
            name: {
                "name": template.name,
                "description": template.description,
                "trigger_type": template.trigger_type,
                "nodes_count": len(template.nodes)
            }
            for name, template in self.workflow_templates.items()
        }
    
    async def setup_sophia_automation(self) -> Dict[str, Any]:
        """
        Set up complete SOPHIA automation workflows.
        Creates all essential workflows for autonomous operations.
        """
        results = {}
        
        for template_name in self.workflow_templates.keys():
            try:
                result = await self.create_workflow(template_name)
                results[template_name] = result
                logger.info(f"Set up workflow: {template_name}")
            except Exception as e:
                logger.error(f"Failed to set up workflow {template_name}: {e}")
                results[template_name] = {"status": "error", "error": str(e)}
        
        return {
            "status": "setup_complete",
            "workflows_created": len([r for r in results.values() if r.get("status") in ["created", "definition_ready"]]),
            "workflows_failed": len([r for r in results.values() if r.get("status") == "error"]),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

# Global n8n automation instance
n8n_automation = N8NWorkflowAutomation()

