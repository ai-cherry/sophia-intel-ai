#!/usr/bin/env python3
"""
Sophia Business Intelligence Memory Service
Handles BI-specific context and retrieval
Port: 8767
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.memory.base_memory import BaseMemoryService

class SophiaMemoryService(BaseMemoryService):
    """
    Memory service for business intelligence domain
    Handles business metrics, reports, customer data, and service integrations
    """
    
    def __init__(self):
        super().__init__(domain="sophia", port=8767)
        self.collection_name = "business_intelligence"
        
        # Business-specific keywords for enhanced search
        self.business_keywords = {
            "metrics": ["revenue", "sales", "conversion", "kpi", "roi"],
            "customers": ["customer", "client", "user", "account", "lead"],
            "services": ["salesforce", "hubspot", "slack", "asana", "linear"],
            "reports": ["dashboard", "report", "analytics", "insights", "trends"]
        }
    
    async def search(self, query: str, limit: int, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search business intelligence context
        Uses hybrid search with caching
        """
        # Check cache first
        cache_key = self._get_cache_key(query)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached[:limit]
        
        results = []
        
        # Try Weaviate vector search if available
        if self.weaviate_client:
            try:
                # Build where filter if provided
                where_filter = None
                if filters:
                    where_filter = self._build_weaviate_filter(filters)
                
                weaviate_query = (
                    self.weaviate_client.query
                    .get(self.collection_name, ["content", "metadata", "source", "type"])
                    .with_hybrid(query=query, alpha=0.5)  # Balance between vector and keyword
                    .with_limit(limit * 2)  # Get more for filtering
                )
                
                if where_filter:
                    weaviate_query = weaviate_query.with_where(where_filter)
                
                weaviate_results = weaviate_query.do()
                
                if self.collection_name in weaviate_results.get("data", {}).get("Get", {}):
                    results = weaviate_results["data"]["Get"][self.collection_name]
            except Exception as e:
                print(f"Weaviate search error: {e}")
        
        # Fallback to Redis keyword search
        if not results and self.redis_available:
            # Expand query with business keywords
            expanded_terms = self._expand_business_query(query)
            
            for term in expanded_terms:
                pattern = f"{self.domain}:doc:*{term.lower()}*"
                for key in self.redis_client.scan_iter(match=pattern, count=100):
                    doc = self.redis_client.get(key)
                    if doc:
                        doc_data = json.loads(doc)
                        # Apply filters
                        if self._apply_filters(doc_data, filters):
                            results.append(doc_data)
                            if len(results) >= limit * 2:
                                break
                
                if len(results) >= limit * 2:
                    break
        
        # Score and rank results
        results = self._rank_business_results(results, query)
        
        # Cache results
        if results:
            self._set_cache(cache_key, results, ttl=1800)  # 30 min cache for BI data
        
        return results[:limit]
    
    async def index(self, document: Dict[str, Any]) -> bool:
        """
        Index business document with metadata enrichment
        """
        try:
            # Enrich with business metadata
            document = self._enrich_business_metadata(document)
            
            # Generate document ID
            doc_id = document.get("id", f"sophia:{datetime.now().timestamp()}")
            document["id"] = doc_id
            
            # Store in Redis for fast access
            if self.redis_available:
                self.redis_client.setex(
                    f"{self.domain}:doc:{doc_id}",
                    86400 * 7,  # 7 day TTL for business data
                    json.dumps(document)
                )
                
                # Also index by type for quick filtering
                doc_type = document.get("type", "general")
                self.redis_client.sadd(f"{self.domain}:type:{doc_type}", doc_id)
            else:
                self.memory_cache[f"{self.domain}:doc:{doc_id}"] = document
            
            # Index in Weaviate for vector search
            if self.weaviate_client:
                try:
                    self.weaviate_client.data_object.create(
                        document,
                        self.collection_name
                    )
                except Exception as e:
                    print(f"Weaviate indexing error: {e}")
            
            return True
            
        except Exception as e:
            print(f"Indexing error: {e}")
            return False
    
    async def enrich_with_context(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add business context to results
        Includes related metrics, temporal context, and data sources
        """
        for result in results:
            content = str(result.get("content", "")).lower()
            
            # Add metric context
            metric_context = []
            if "revenue" in content:
                metric_context.extend(["revenue_growth", "mrr", "arr", "ltv"])
            if "customer" in content:
                metric_context.extend(["cac", "churn_rate", "nps", "retention"])
            if "sales" in content:
                metric_context.extend(["conversion_rate", "pipeline_value", "deal_velocity"])
            
            if metric_context:
                result["metric_context"] = metric_context
            
            # Add temporal context
            result["temporal_context"] = {
                "current_quarter": self._get_current_quarter(),
                "fiscal_year": f"FY{datetime.now().year}",
                "comparison_period": "YoY"  # Year-over-Year default
            }
            
            # Add data source context
            source = result.get("source", "").lower()
            if source:
                result["integration_context"] = self._get_integration_context(source)
            
            # Add business impact assessment
            result["impact_level"] = self._assess_business_impact(content)
        
        return results
    
    def _expand_business_query(self, query: str) -> List[str]:
        """Expand query with business-specific terms"""
        terms = [query]
        query_lower = query.lower()
        
        for category, keywords in self.business_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Add related terms from the same category
                    terms.extend([kw for kw in keywords if kw != keyword])
                    break
        
        return list(set(terms))
    
    def _rank_business_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rank results based on business relevance"""
        query_lower = query.lower()
        
        for result in results:
            score = 0
            content = str(result.get("content", "")).lower()
            
            # Exact match bonus
            if query_lower in content:
                score += 10
            
            # Business keyword matches
            for terms in self.business_keywords.values():
                for term in terms:
                    if term in query_lower and term in content:
                        score += 5
            
            # Recency bonus (if timestamp available)
            if "timestamp" in result:
                try:
                    doc_time = datetime.fromisoformat(result["timestamp"])
                    age_days = (datetime.now() - doc_time).days
                    if age_days < 7:
                        score += 3
                    elif age_days < 30:
                        score += 1
                except:
                    pass
            
            # Source reliability bonus
            source = result.get("source", "").lower()
            if source in ["salesforce", "hubspot", "analytics"]:
                score += 2
            
            result["_score"] = score
        
        # Sort by score descending
        return sorted(results, key=lambda x: x.get("_score", 0), reverse=True)
    
    def _apply_filters(self, document: Dict, filters: Optional[Dict]) -> bool:
        """Apply filters to document"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in document:
                return False
            if isinstance(value, list):
                if document[key] not in value:
                    return False
            elif document[key] != value:
                return False
        
        return True
    
    def _build_weaviate_filter(self, filters: Dict) -> Dict:
        """Build Weaviate where filter from filters dict"""
        # Simple filter building - can be extended
        where = {"operator": "And", "operands": []}
        
        for key, value in filters.items():
            where["operands"].append({
                "path": [key],
                "operator": "Equal",
                "valueString": str(value)
            })
        
        return where if where["operands"] else None
    
    def _enrich_business_metadata(self, document: Dict) -> Dict:
        """Enrich document with business metadata"""
        # Auto-detect document type if not provided
        if "type" not in document:
            content = str(document.get("content", "")).lower()
            if any(word in content for word in ["revenue", "sales", "profit"]):
                document["type"] = "financial"
            elif any(word in content for word in ["customer", "client", "user"]):
                document["type"] = "customer"
            elif any(word in content for word in ["kpi", "metric", "performance"]):
                document["type"] = "metric"
            else:
                document["type"] = "general"
        
        # Add timestamp if not present
        if "timestamp" not in document:
            document["timestamp"] = datetime.now().isoformat()
        
        # Add domain tag
        document["domain"] = self.domain
        
        return document
    
    def _get_current_quarter(self) -> str:
        """Get current business quarter"""
        month = datetime.now().month
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter} {datetime.now().year}"
    
    def _get_integration_context(self, source: str) -> Dict:
        """Get context for business service integration"""
        contexts = {
            "salesforce": {
                "type": "CRM",
                "data_types": ["leads", "opportunities", "accounts"],
                "refresh_rate": "real-time"
            },
            "hubspot": {
                "type": "Marketing",
                "data_types": ["contacts", "campaigns", "analytics"],
                "refresh_rate": "hourly"
            },
            "slack": {
                "type": "Communication",
                "data_types": ["messages", "channels", "users"],
                "refresh_rate": "real-time"
            },
            "asana": {
                "type": "Project Management",
                "data_types": ["tasks", "projects", "teams"],
                "refresh_rate": "real-time"
            }
        }
        return contexts.get(source, {"type": "External", "refresh_rate": "unknown"})
    
    def _assess_business_impact(self, content: str) -> str:
        """Assess business impact level of content"""
        content_lower = content.lower()
        
        # High impact keywords
        if any(word in content_lower for word in ["revenue", "profit", "loss", "critical", "urgent"]):
            return "high"
        
        # Medium impact keywords
        if any(word in content_lower for word in ["performance", "efficiency", "growth", "metric"]):
            return "medium"
        
        return "low"


if __name__ == "__main__":
    service = SophiaMemoryService()
    service.run()