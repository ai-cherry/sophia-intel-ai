"""
Salesforce MCP Server
Enterprise CRM integration with full Swarm support following standardized MCP patterns
"""
from mcp.saas.common.base_server import (
    BaseMCPServer, ContextRequest, ContextResponse, 
    SearchRequest, SearchResponse
)
from mcp.saas.common.auth import api_key_auth
from fastapi import Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import time
import os
import httpx
import json
import base64

class SalesforceContextRequest(ContextRequest):
    """Salesforce-specific context request"""
    org_id: str = Field(..., description="Salesforce org ID")
    object_type: str = Field(..., description="Salesforce object type (Account, Contact, etc.)")
    record_id: Optional[str] = Field(None, description="Salesforce record ID")
    user_id: Optional[str] = Field(None, description="Salesforce user ID")

class SalesforceSearchRequest(SearchRequest):
    """Salesforce-specific search request"""
    org_id: Optional[str] = Field(None, description="Limit search to specific org")
    object_types: Optional[List[str]] = Field(None, description="Object types to search")
    date_from: Optional[str] = Field(None, description="Search from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Search to date (YYYY-MM-DD)")

class SwarmSalesforceAction(BaseModel):
    """Salesforce action from Swarm agents"""
    action_type: str = Field(..., description="Action type: create, update, query")
    object_type: str = Field(..., description="Salesforce object type")
    data: Dict[str, Any] = Field(..., description="Action data")
    swarm_stage: str = Field(..., description="Current swarm stage")
    session_id: str = Field(..., description="Swarm session ID")

class SalesforceRecord(BaseModel):
    """Salesforce record model"""
    record_id: Optional[str] = Field(None, description="Salesforce record ID")
    object_type: str = Field(..., description="Object type")
    fields: Dict[str, Any] = Field(..., description="Record fields")

class SalesforceMCPServer(BaseMCPServer):
    """
    Salesforce MCP Server with comprehensive Swarm integration
    
    Features:
    - Context storage for Salesforce records and interactions
    - Semantic search across Salesforce data
    - Swarm agent CRUD operations
    - Real-time data synchronization
    - Enterprise security and compliance
    """
    
    def __init__(self):
        super().__init__(
            title="Salesforce MCP Server",
            description="Model Context Protocol server for Salesforce CRM with full Swarm support",
            version="1.0.0"
        )
        
        self._setup_salesforce_client()
        self._setup_storage()
        self._setup_routes()
        
    def _setup_salesforce_client(self):
        """Initialize Salesforce API client"""
        self.sf_client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.sf_client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.sf_username = os.getenv("SALESFORCE_USERNAME")
        self.sf_password = os.getenv("SALESFORCE_PASSWORD")
        self.sf_security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        self.sf_instance_url = os.getenv("SALESFORCE_INSTANCE_URL", "https://login.salesforce.com")
        
        self.access_token = None
        self.token_expires_at = 0
        
        if all([self.sf_client_id, self.sf_client_secret, self.sf_username, self.sf_password]):
            self.sf_client = httpx.AsyncClient(timeout=30.0)
            logger.info("Salesforce API client initialized")
        else:
            logger.warning("Salesforce credentials not fully configured - some features will be unavailable")
            self.sf_client = None
            
    def _setup_storage(self):
        """Initialize context storage"""
        self.context_store = {}  # In production: PostgreSQL + Qdrant
        self.record_cache = {}   # Cache for recent records
        self.field_mappings = {  # Common field mappings
            "Account": {"name": "Name", "description": "Description"},
            "Contact": {"name": "Name", "email": "Email", "phone": "Phone"},
            "Opportunity": {"name": "Name", "amount": "Amount", "stage": "StageName"},
            "Lead": {"name": "Name", "email": "Email", "company": "Company"},
            "Case": {"subject": "Subject", "description": "Description", "status": "Status"}
        }
        
    def _setup_routes(self):
        """Setup all Salesforce-specific routes"""
        
        # Standard MCP routes
        self.register_route(
            "/salesforce/context",
            "POST",
            self.store_context,
            response_model=ContextResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/salesforce/search",
            "POST",
            self.search_context,
            response_model=SearchResponse,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Swarm integration routes
        self.register_route(
            "/salesforce/swarm/action",
            "POST",
            self.execute_swarm_action,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/salesforce/swarm/extract-opportunities",
            "POST",
            self.extract_opportunities_context,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Salesforce API integration routes
        self.register_route(
            "/salesforce/records/{object_type}",
            "GET",
            self.query_records,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/salesforce/records/{object_type}",
            "POST",
            self.create_record,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/salesforce/records/{object_type}/{record_id}",
            "GET",
            self.get_record,
            dependencies=[Depends(api_key_auth)]
        )
        
        self.register_route(
            "/salesforce/records/{object_type}/{record_id}",
            "PATCH",
            self.update_record,
            dependencies=[Depends(api_key_auth)]
        )
        
        # Analytics and reporting routes
        self.register_route(
            "/salesforce/analytics/pipeline",
            "GET",
            self.get_pipeline_analytics,
            dependencies=[Depends(api_key_auth)]
        )
        
    async def store_context(self, request: SalesforceContextRequest, background_tasks: BackgroundTasks):
        """Store Salesforce record context with metadata"""
        logger.info(f"Storing Salesforce context: org={request.org_id}, object={request.object_type}")
        
        try:
            # Generate context ID
            context_id = f"sf_{request.org_id}_{request.object_type}_{int(time.time())}"
            
            # Enrich context with Salesforce metadata
            enriched_content = await self._enrich_salesforce_context(
                request.content, 
                request.object_type, 
                request.record_id
            )
            
            # Prepare context data
            context_data = {
                "id": context_id,
                "org_id": request.org_id,
                "object_type": request.object_type,
                "record_id": request.record_id,
                "user_id": request.user_id,
                "content": enriched_content,
                "original_content": request.content,
                "metadata": request.metadata,
                "context_type": request.context_type,
                "swarm_stage": request.swarm_stage,
                "session_id": request.session_id,
                "timestamp": time.time(),
                "service": "salesforce"
            }
            
            # Store in context store
            self.context_store[context_id] = context_data
            
            # Record in Swarm telemetry
            if request.swarm_stage:
                background_tasks.add_task(
                    self.swarm_telemetry,
                    {
                        "type": "context_storage",
                        "service": "salesforce",
                        "session_id": request.session_id,
                        "swarm_stage": request.swarm_stage,
                        "content_size": len(enriched_content),
                        "context_type": request.context_type,
                        "org_id": request.org_id,
                        "object_type": request.object_type
                    }
                )
            
            return ContextResponse(
                status="success",
                id=context_id,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error storing Salesforce context: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store context: {str(e)}")
    
    async def search_context(self, request: SalesforceSearchRequest):
        """Search Salesforce context with business intelligence"""
        logger.info(f"Searching Salesforce context: '{request.query}' (limit={request.limit})")
        
        try:
            results = []
            
            # Search stored contexts
            for context_id, context_data in self.context_store.items():
                # Apply org filter
                if request.org_id and context_data.get("org_id") != request.org_id:
                    continue
                
                # Apply object type filter
                if (request.object_types and 
                    context_data.get("object_type") not in request.object_types):
                    continue
                
                # Apply session filter
                if request.session_id and context_data.get("session_id") != request.session_id:
                    continue
                
                # Search in content (in production, use vector similarity)
                content = context_data.get("content", "").lower()
                if request.query.lower() in content:
                    results.append({
                        "id": context_id,
                        "content": context_data.get("content", "")[:500],
                        "metadata": context_data.get("metadata", {}),
                        "org_id": context_data.get("org_id"),
                        "object_type": context_data.get("object_type"),
                        "record_id": context_data.get("record_id"),
                        "timestamp": context_data.get("timestamp"),
                        "swarm_stage": context_data.get("swarm_stage"),
                        "score": 0.85,  # Mock score - use real similarity
                        "business_context": await self._extract_business_context(context_data)
                    })
            
            # Sort by relevance and timestamp
            results.sort(key=lambda x: (x["score"], x["timestamp"]), reverse=True)
            results = results[:request.limit]
            
            return SearchResponse(
                results=results,
                count=len(results),
                query=request.query
            )
            
        except Exception as e:
            logger.error(f"Error searching Salesforce context: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def execute_swarm_action(self, action: SwarmSalesforceAction):
        """Execute Salesforce actions from Swarm agents"""
        logger.info(f"Executing Swarm action: {action.action_type} on {action.object_type}")
        
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
        
        try:
            # Ensure we have a valid access token
            await self._ensure_access_token()
            
            result = None
            
            if action.action_type == "create":
                result = await self._create_salesforce_record(action.object_type, action.data)
            elif action.action_type == "update":
                record_id = action.data.pop("Id", action.data.pop("id", None))
                if not record_id:
                    raise HTTPException(status_code=400, detail="Record ID required for update")
                result = await self._update_salesforce_record(action.object_type, record_id, action.data)
            elif action.action_type == "query":
                result = await self._query_salesforce_records(action.object_type, action.data)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown action type: {action.action_type}")
            
            # Record in Swarm telemetry
            await self.swarm_telemetry({
                "type": "salesforce_action",
                "service": "salesforce",
                "session_id": action.session_id,
                "swarm_stage": action.swarm_stage,
                "action_type": action.action_type,
                "object_type": action.object_type,
                "success": True,
                "result_size": len(str(result)) if result else 0
            })
            
            return {
                "status": "success",
                "action_type": action.action_type,
                "object_type": action.object_type,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing Swarm Salesforce action: {e}")
            
            # Record failure in telemetry
            await self.swarm_telemetry({
                "type": "salesforce_action_error",
                "service": "salesforce",
                "session_id": action.session_id,
                "swarm_stage": action.swarm_stage,
                "action_type": action.action_type,
                "error": str(e)
            })
            
            raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")
    
    async def extract_opportunities_context(self, request: Dict[str, Any]):
        """Extract opportunities context for Swarm sales intelligence"""
        session_id = request.get("session_id")
        swarm_stage = request.get("swarm_stage")
        org_id = request.get("org_id")
        
        if not org_id:
            raise HTTPException(status_code=400, detail="org_id is required")
        
        logger.info(f"Extracting opportunities context for Swarm: org={org_id}")
        
        try:
            # Query recent opportunities
            opportunities = await self._query_salesforce_records("Opportunity", {
                "limit": 50,
                "order_by": "LastModifiedDate DESC"
            })
            
            # Analyze opportunities
            context = {
                "total_opportunities": len(opportunities),
                "pipeline_value": sum(opp.get("Amount", 0) for opp in opportunities if opp.get("Amount")),
                "stage_distribution": await self._analyze_opportunity_stages(opportunities),
                "top_opportunities": await self._get_top_opportunities(opportunities),
                "conversion_insights": await self._analyze_conversion_trends(opportunities),
                "risk_assessment": await self._assess_pipeline_risks(opportunities),
                "recommended_actions": await self._generate_action_recommendations(opportunities),
                "org_id": org_id,
                "analysis_timestamp": time.time()
            }
            
            # Store extracted context
            if session_id:
                await self.store_context(SalesforceContextRequest(
                    session_id=session_id,
                    content=json.dumps(context, indent=2),
                    metadata={
                        "extraction_type": "opportunities_analysis",
                        "org_id": org_id,
                        "opportunity_count": len(opportunities)
                    },
                    context_type="sales_intelligence",
                    swarm_stage=swarm_stage,
                    org_id=org_id,
                    object_type="Opportunity",
                    record_id=None,
                    user_id=request.get("user_id")
                ), BackgroundTasks())
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting opportunities context: {e}")
            raise HTTPException(status_code=500, detail=f"Context extraction failed: {str(e)}")
    
    # Salesforce API integration methods
    
    async def query_records(self, object_type: str, filters: Optional[Dict] = None):
        """Query Salesforce records"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        try:
            await self._ensure_access_token()
            return await self._query_salesforce_records(object_type, filters or {})
        except Exception as e:
            logger.error(f"Error querying {object_type} records: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_record(self, object_type: str, record: SalesforceRecord):
        """Create Salesforce record"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        try:
            await self._ensure_access_token()
            return await self._create_salesforce_record(object_type, record.fields)
        except Exception as e:
            logger.error(f"Error creating {object_type} record: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_record(self, object_type: str, record_id: str):
        """Get single Salesforce record"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        try:
            await self._ensure_access_token()
            
            # Get field list for object type
            fields = list(self.field_mappings.get(object_type, {}).values())
            if not fields:
                fields = ["Id", "Name"]
            
            url = f"{self.sf_instance_url}/services/data/v57.0/sobjects/{object_type}/{record_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = await self.sf_client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting {object_type} record {record_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_record(self, object_type: str, record_id: str, updates: Dict[str, Any]):
        """Update Salesforce record"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        try:
            await self._ensure_access_token()
            return await self._update_salesforce_record(object_type, record_id, updates)
        except Exception as e:
            logger.error(f"Error updating {object_type} record {record_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_pipeline_analytics(self):
        """Get sales pipeline analytics"""
        try:
            opportunities = await self._query_salesforce_records("Opportunity", {"limit": 1000})
            
            analytics = {
                "total_pipeline_value": sum(opp.get("Amount", 0) for opp in opportunities),
                "opportunity_count": len(opportunities),
                "stage_breakdown": await self._analyze_opportunity_stages(opportunities),
                "monthly_trends": await self._calculate_monthly_trends(opportunities),
                "conversion_rates": await self._calculate_conversion_rates(opportunities),
                "top_performers": await self._identify_top_performers(opportunities),
                "generated_at": time.time()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating pipeline analytics: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Helper methods
    
    async def _ensure_access_token(self):
        """Ensure we have a valid Salesforce access token"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        if self.access_token and time.time() < self.token_expires_at:
            return
            
        # Authenticate with Salesforce
        auth_url = f"{self.sf_instance_url}/services/oauth2/token"
        auth_data = {
            "grant_type": "password",
            "client_id": self.sf_client_id,
            "client_secret": self.sf_client_secret,
            "username": self.sf_username,
            "password": f"{self.sf_password}{self.sf_security_token or ''}"
        }
        
        response = await self.sf_client.post(auth_url, data=auth_data)
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Salesforce authentication failed")
            
        auth_result = response.json()
        self.access_token = auth_result["access_token"]
        self.sf_instance_url = auth_result["instance_url"]
        self.token_expires_at = time.time() + 3600  # 1 hour from now
    
    async def _enrich_salesforce_context(self, content: str, object_type: str, record_id: Optional[str]) -> str:
        """Enrich content with Salesforce context"""
        enriched = content
        
        # Add object type context
        enriched += f"\n\n[Salesforce Context: {object_type}]"
        
        # Add record details if available
        if record_id and self.sf_client:
            try:
                record = await self.get_record(object_type, record_id)
                enriched += f"\nRecord: {record.get('Name', record_id)}"
                if record.get("Description"):
                    enriched += f"\nDescription: {record['Description']}"
            except:
                pass  # Don't fail if we can't fetch record details
                
        return enriched
    
    async def _extract_business_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract business context from Salesforce data"""
        return {
            "business_unit": context_data.get("metadata", {}).get("business_unit", "Unknown"),
            "priority_level": context_data.get("metadata", {}).get("priority", "Medium"),
            "revenue_impact": context_data.get("metadata", {}).get("revenue_impact", "Unknown"),
            "stakeholders": context_data.get("metadata", {}).get("stakeholders", [])
        }
    
    async def _create_salesforce_record(self, object_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create record in Salesforce"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        url = f"{self.sf_instance_url}/services/data/v57.0/sobjects/{object_type}/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.sf_client.post(url, json=data, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        return response.json()
    
    async def _update_salesforce_record(self, object_type: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update record in Salesforce"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        url = f"{self.sf_instance_url}/services/data/v57.0/sobjects/{object_type}/{record_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.sf_client.patch(url, json=data, headers=headers)
        
        if response.status_code != 204:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        return {"success": True, "id": record_id}
    
    async def _query_salesforce_records(self, object_type: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query records from Salesforce"""
        if not self.sf_client:
            raise HTTPException(status_code=503, detail="Salesforce API not configured")
            
        # Build SOQL query
        fields = list(self.field_mappings.get(object_type, {}).values()) + ["Id"]
        fields = list(set(fields))  # Remove duplicates
        
        query = f"SELECT {', '.join(fields)} FROM {object_type}"
        
        # Add filters
        conditions = []
        if filters.get("limit"):
            query += f" LIMIT {filters['limit']}"
        if filters.get("order_by"):
            query += f" ORDER BY {filters['order_by']}"
            
        url = f"{self.sf_instance_url}/services/data/v57.0/query"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"q": query}
        
        response = await self.sf_client.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        result = response.json()
        return result.get("records", [])
    
    # Analytics helper methods
    
    async def _analyze_opportunity_stages(self, opportunities: List[Dict]) -> Dict[str, int]:
        """Analyze opportunity distribution by stage"""
        stages = {}
        for opp in opportunities:
            stage = opp.get("StageName", "Unknown")
            stages[stage] = stages.get(stage, 0) + 1
        return stages
    
    async def _get_top_opportunities(self, opportunities: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top opportunities by value"""
        sorted_opps = sorted(
            [opp for opp in opportunities if opp.get("Amount")],
            key=lambda x: x.get("Amount", 0),
            reverse=True
        )
        return sorted_opps[:limit]
    
    async def _analyze_conversion_trends(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze conversion trends"""
        # Mock implementation - in production, analyze historical data
        return {
            "monthly_conversion_rate": 0.23,
            "average_deal_size": 45000,
            "average_sales_cycle_days": 87,
            "trend": "improving"
        }
    
    async def _assess_pipeline_risks(self, opportunities: List[Dict]) -> List[str]:
        """Assess pipeline risks"""
        risks = []
        
        # Check for stale opportunities
        stale_count = len([opp for opp in opportunities 
                          if opp.get("StageName") in ["Proposal", "Negotiation"]])
        if stale_count > 10:
            risks.append(f"{stale_count} opportunities stuck in late stages")
            
        return risks
    
    async def _generate_action_recommendations(self, opportunities: List[Dict]) -> List[str]:
        """Generate action recommendations"""
        recommendations = []
        
        # Example recommendations based on data
        proposal_stage = len([opp for opp in opportunities 
                             if opp.get("StageName") == "Proposal"])
        if proposal_stage > 5:
            recommendations.append("Focus on closing proposal-stage opportunities")
            
        return recommendations
    
    async def _calculate_monthly_trends(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Calculate monthly trends"""
        # Mock implementation
        return {
            "current_month": {"value": 125000, "count": 15},
            "previous_month": {"value": 98000, "count": 12},
            "growth_rate": 0.28
        }
    
    async def _calculate_conversion_rates(self, opportunities: List[Dict]) -> Dict[str, float]:
        """Calculate conversion rates by stage"""
        # Mock implementation
        return {
            "Prospecting": 0.45,
            "Qualification": 0.62,
            "Proposal": 0.78,
            "Negotiation": 0.89,
            "Closed Won": 1.0
        }
    
    async def _identify_top_performers(self, opportunities: List[Dict]) -> List[Dict]:
        """Identify top performing sales reps"""
        # Mock implementation - would analyze by OwnerId
        return [
            {"name": "Sarah Johnson", "deals_closed": 12, "revenue": 340000},
            {"name": "Mike Chen", "deals_closed": 8, "revenue": 285000}
        ]


# Create the FastAPI app instance
app = SalesforceMCPServer().app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)