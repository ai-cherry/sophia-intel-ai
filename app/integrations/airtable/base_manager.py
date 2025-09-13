"""
Airtable Base Manager
Manages Airtable bases in federated architecture with domain-specific
bases and shared data synchronization.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Optional
from pyairtable import Api
from .models import (
    AirtableBase,
    AirtableRecord,
    BaseType,
    BrandAsset,
    FoundationalKnowledge,
    RecordType,
    SyncStatus,
)
logger = logging.getLogger(__name__)
class AirtableBaseManager:
    """
    Central manager for all Airtable bases in federated architecture
    """
    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.bases: dict[str, AirtableBase] = {}
        self.api_clients: dict[str, Api] = {}
        self.base_schemas: dict[str, dict[str, Any]] = {}
        # Rate limiting
        self.rate_limit_per_second = 5
        self.last_request_time = datetime.now()
        # Caching
        self.record_cache: dict[str, dict[str, AirtableRecord]] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        self.last_cache_clear = datetime.now()
    async def initialize_federated_bases(self, base_configs: dict[str, dict[str, Any]]):
        """Initialize all bases in federated architecture"""
        logger.info("Initializing federated Airtable architecture")
        # Initialize shared core base first (highest priority)
        if "shared_core" in base_configs:
            await self._initialize_base(
                BaseType.SHARED_CORE, base_configs["shared_core"]
            )
        # Initialize domain-specific bases
        base_type_mapping = {
            "marketing_ops": BaseType.MARKETING_OPS,
            "sales_intelligence": BaseType.SALES_INTELLIGENCE,
            "customer_success": BaseType.CUSTOMER_SUCCESS,
            "finance_ops": BaseType.FINANCE_OPS,
            "brand_kit": BaseType.BRAND_KIT,
            "sophia_foundation": BaseType.SOPHIA_FOUNDATION,
        }
        for config_key, base_type in base_type_mapping.items():
            if config_key in base_configs:
                await self._initialize_base(base_type, base_configs[config_key])
        # Validate base dependencies
        await self._validate_base_dependencies()
        logger.info(f"Initialized {len(self.bases)} Airtable bases")
    async def _initialize_base(self, base_type: BaseType, config: dict[str, Any]):
        """Initialize individual Airtable base"""
        base_id = config["base_id"]
        api_key = config["api_key"]
        # Create base configuration
        base = AirtableBase(
            base_id=base_id,
            name=config.get("name", f"{base_type.value}_base"),
            base_type=base_type,
            workspace_id=config.get("workspace_id", ""),
            api_key=api_key,
            access_permissions=config.get("permissions", {}),
            sync_enabled=config.get("sync_enabled", True),
            auto_sync_interval=config.get("sync_interval", 300),
            sync_dependencies=config.get("dependencies", []),
            sync_priority=config.get("priority", 1),
        )
        # Initialize API client
        try:
            api_client = Api(api_key)
            self.api_clients[base_id] = api_client
            # Load base schema
            await self._load_base_schema(base_id, api_client)
            # Store base configuration
            self.bases[base_id] = base
            # Initialize record cache for base
            self.record_cache[base_id] = {}
            logger.info(f"Initialized {base_type.value} base: {base_id}")
        except Exception as e:
            logger.error(f"Failed to initialize base {base_id}: {e}")
            raise
    async def _load_base_schema(self, base_id: str, api_client: Api):
        """Load schema information for Airtable base"""
        try:
            # In production, would use actual Airtable API to get schema
            # For now, define standard schemas for each base type
            base = self.bases.get(base_id)
            if not base:
                return
            schema = await self._get_standard_schema(base.base_type)
            base.tables = schema
            self.base_schemas[base_id] = schema
        except Exception as e:
            logger.error(f"Failed to load schema for base {base_id}: {e}")
    async def _get_standard_schema(
        self, base_type: BaseType
    ) -> dict[str, dict[str, Any]]:
        """Get standard schema for base type"""
        schemas = {
            BaseType.SHARED_CORE: {
                "Company_Profiles": {
                    "fields": ["Name", "Industry", "Size", "Location", "Status"],
                    "primary_field": "Name",
                },
                "Industry_Data": {
                    "fields": ["Industry", "Market_Size", "Growth_Rate", "Key_Trends"],
                    "primary_field": "Industry",
                },
                "Integration_Credentials": {
                    "fields": ["Platform", "Credential_Type", "Status", "Last_Updated"],
                    "primary_field": "Platform",
                },
                "Universal_Metrics": {
                    "fields": ["Metric_Name", "Value", "Period", "Source", "Domain"],
                    "primary_field": "Metric_Name",
                },
            },
            BaseType.MARKETING_OPS: {
                "Campaign_Templates": {
                    "fields": ["Name", "Type", "Channel", "Template_Content", "Status"],
                    "primary_field": "Name",
                },
                "Lead_Scoring_Models": {
                    "fields": ["Model_Name", "Criteria", "Score_Weights", "Active"],
                    "primary_field": "Model_Name",
                },
                "AB_Test_Results": {
                    "fields": [
                        "Test_Name",
                        "Variant_A",
                        "Variant_B",
                        "Winner",
                        "Confidence",
                    ],
                    "primary_field": "Test_Name",
                },
                "Channel_Performance": {
                    "fields": [
                        "Channel",
                        "Period",
                        "Impressions",
                        "Clicks",
                        "Conversions",
                        "ROI",
                    ],
                    "primary_field": "Channel",
                },
            },
            BaseType.SALES_INTELLIGENCE: {
                "Prospect_Profiles": {
                    "fields": [
                        "Name",
                        "Company",
                        "Role",
                        "Email",
                        "Phone",
                        "Stage",
                        "Score",
                    ],
                    "primary_field": "Name",
                },
                "Personality_Assessments": {
                    "fields": [
                        "Prospect_ID",
                        "DISC_Type",
                        "Communication_Style",
                        "Decision_Factors",
                    ],
                    "primary_field": "Prospect_ID",
                },
                "Outreach_Sequences": {
                    "fields": [
                        "Sequence_Name",
                        "Channel",
                        "Steps",
                        "Success_Rate",
                        "Active",
                    ],
                    "primary_field": "Sequence_Name",
                },
                "Competitive_Intelligence": {
                    "fields": [
                        "Competitor",
                        "Strengths",
                        "Weaknesses",
                        "Pricing",
                        "Last_Updated",
                    ],
                    "primary_field": "Competitor",
                },
            },
            BaseType.CUSTOMER_SUCCESS: {
                "Health_Score_Models": {
                    "fields": [
                        "Model_Name",
                        "Metrics",
                        "Weights",
                        "Thresholds",
                        "Active",
                    ],
                    "primary_field": "Model_Name",
                },
                "Success_Milestones": {
                    "fields": [
                        "Milestone",
                        "Timeline",
                        "Success_Criteria",
                        "Completion_Rate",
                    ],
                    "primary_field": "Milestone",
                },
                "Onboarding_Workflows": {
                    "fields": [
                        "Workflow_Name",
                        "Steps",
                        "Duration",
                        "Success_Rate",
                        "Owner",
                    ],
                    "primary_field": "Workflow_Name",
                },
            },
            BaseType.FINANCE_OPS: {
                "Budget_Allocations": {
                    "fields": [
                        "Department",
                        "Category",
                        "Budget",
                        "Spent",
                        "Remaining",
                        "Period",
                    ],
                    "primary_field": "Department",
                },
                "ROI_Models": {
                    "fields": [
                        "Model_Name",
                        "Formula",
                        "Variables",
                        "Accuracy",
                        "Last_Updated",
                    ],
                    "primary_field": "Model_Name",
                },
                "Vendor_Contracts": {
                    "fields": ["Vendor", "Service", "Cost", "Contract_End", "Status"],
                    "primary_field": "Vendor",
                },
            },
            BaseType.BRAND_KIT: {
                "Brand_Guidelines": {
                    "fields": [
                        "Guideline_Type",
                        "Content",
                        "Version",
                        "Status",
                        "Last_Updated",
                    ],
                    "primary_field": "Guideline_Type",
                },
                "Template_Assets": {
                    "fields": [
                        "Asset_Name",
                        "Type",
                        "Format",
                        "File_URL",
                        "Usage_Context",
                    ],
                    "primary_field": "Asset_Name",
                },
                "Color_Palettes": {
                    "fields": [
                        "Palette_Name",
                        "Colors",
                        "Usage",
                        "Hex_Codes",
                        "Status",
                    ],
                    "primary_field": "Palette_Name",
                },
                "Logo_Variants": {
                    "fields": ["Variant_Name", "Format", "Size", "Usage", "File_URL"],
                    "primary_field": "Variant_Name",
                },
            },
            BaseType.SOPHIA_FOUNDATION: {
                "Foundational_Knowledge": {
                    "fields": [
                        "Title",
                        "Category",
                        "Content",
                        "Confidence",
                        "Last_Validated",
                    ],
                    "primary_field": "Title",
                },
                "Context_Mappings": {
                    "fields": [
                        "Context_Type",
                        "Business_Domain",
                        "Usage_Patterns",
                        "Priority",
                    ],
                    "primary_field": "Context_Type",
                },
                "Decision_Frameworks": {
                    "fields": [
                        "Framework_Name",
                        "Criteria",
                        "Process",
                        "Outcomes",
                        "Active",
                    ],
                    "primary_field": "Framework_Name",
                },
            },
        }
        return schemas.get(base_type, {})
    async def _validate_base_dependencies(self):
        """Validate that all base dependencies are satisfied"""
        for base_id, base in self.bases.items():
            for dependency_id in base.sync_dependencies:
                if dependency_id not in self.bases:
                    logger.warning(
                        f"Base {base_id} depends on {dependency_id} which is not initialized"
                    )
    async def create_record(
        self,
        base_id: str,
        table_name: str,
        record_data: dict[str, Any],
        record_type: RecordType = None,
    ) -> AirtableRecord:
        """Create new record in Airtable base"""
        await self._rate_limit_check()
        try:
            # Get API client and table
            api_client = self.api_clients.get(base_id)
            if not api_client:
                raise ValueError(f"No API client for base {base_id}")
            table = api_client.table(base_id, table_name)
            # Create record in Airtable
            airtable_record = table.create(record_data)
            # Create internal record object
            record = AirtableRecord(
                record_id=airtable_record["id"],
                table_name=table_name,
                base_id=base_id,
                record_type=record_type or RecordType.COMPANY_PROFILE,
                fields=airtable_record["fields"],
                source_base=base_id,
                sync_status=SyncStatus.COMPLETED,
            )
            # Cache the record
            if base_id not in self.record_cache:
                self.record_cache[base_id] = {}
            self.record_cache[base_id][record.record_id] = record
            logger.info(f"Created record {record.record_id} in {base_id}/{table_name}")
            return record
        except Exception as e:
            logger.error(f"Failed to create record in {base_id}/{table_name}: {e}")
            raise
    async def get_record(
        self, base_id: str, table_name: str, record_id: str, use_cache: bool = True
    ) -> Optional[AirtableRecord]:
        """Get record from Airtable base"""
        # Check cache first
        if use_cache and base_id in self.record_cache:
            cached_record = self.record_cache[base_id].get(record_id)
            if cached_record and self._is_cache_valid(cached_record):
                return cached_record
        await self._rate_limit_check()
        try:
            # Get API client and table
            api_client = self.api_clients.get(base_id)
            if not api_client:
                raise ValueError(f"No API client for base {base_id}")
            table = api_client.table(base_id, table_name)
            # Get record from Airtable
            airtable_record = table.get(record_id)
            # Create internal record object
            record = AirtableRecord(
                record_id=airtable_record["id"],
                table_name=table_name,
                base_id=base_id,
                record_type=RecordType.COMPANY_PROFILE,  # Would determine from context
                fields=airtable_record["fields"],
                source_base=base_id,
                sync_status=SyncStatus.COMPLETED,
            )
            # Cache the record
            if base_id not in self.record_cache:
                self.record_cache[base_id] = {}
            self.record_cache[base_id][record_id] = record
            return record
        except Exception as e:
            logger.error(
                f"Failed to get record {record_id} from {base_id}/{table_name}: {e}"
            )
            return None
    async def update_record(
        self,
        base_id: str,
        table_name: str,
        record_id: str,
        updates: dict[str, Any],
        updated_by: str = "system",
    ) -> Optional[AirtableRecord]:
        """Update record in Airtable base"""
        await self._rate_limit_check()
        try:
            # Get API client and table
            api_client = self.api_clients.get(base_id)
            if not api_client:
                raise ValueError(f"No API client for base {base_id}")
            table = api_client.table(base_id, table_name)
            # Update record in Airtable
            airtable_record = table.update(record_id, updates)
            # Update cached record if exists
            if base_id in self.record_cache and record_id in self.record_cache[base_id]:
                cached_record = self.record_cache[base_id][record_id]
                for field_name, value in updates.items():
                    cached_record.update_field(field_name, value, updated_by)
                cached_record.sync_status = SyncStatus.COMPLETED
            else:
                # Create new record object
                record = AirtableRecord(
                    record_id=airtable_record["id"],
                    table_name=table_name,
                    base_id=base_id,
                    record_type=RecordType.COMPANY_PROFILE,
                    fields=airtable_record["fields"],
                    source_base=base_id,
                    sync_status=SyncStatus.COMPLETED,
                    updated_by=updated_by,
                )
                # Cache the record
                if base_id not in self.record_cache:
                    self.record_cache[base_id] = {}
                self.record_cache[base_id][record_id] = record
            logger.info(f"Updated record {record_id} in {base_id}/{table_name}")
            return self.record_cache[base_id][record_id]
        except Exception as e:
            logger.error(
                f"Failed to update record {record_id} in {base_id}/{table_name}: {e}"
            )
            return None
    async def query_records(
        self,
        base_id: str,
        table_name: str,
        formula: str = "",
        sort: list[dict[str, Any]] = None,
        max_records: int = 100,
    ) -> list[AirtableRecord]:
        """Query records from Airtable base with filtering and sorting"""
        await self._rate_limit_check()
        try:
            # Get API client and table
            api_client = self.api_clients.get(base_id)
            if not api_client:
                raise ValueError(f"No API client for base {base_id}")
            table = api_client.table(base_id, table_name)
            # Query records from Airtable
            query_params = {"max_records": max_records}
            if formula:
                query_params["formula"] = formula
            if sort:
                query_params["sort"] = sort
            airtable_records = table.all(**query_params)
            # Convert to internal record objects
            records = []
            for airtable_record in airtable_records:
                record = AirtableRecord(
                    record_id=airtable_record["id"],
                    table_name=table_name,
                    base_id=base_id,
                    record_type=RecordType.COMPANY_PROFILE,
                    fields=airtable_record["fields"],
                    source_base=base_id,
                    sync_status=SyncStatus.COMPLETED,
                )
                records.append(record)
                # Cache the record
                if base_id not in self.record_cache:
                    self.record_cache[base_id] = {}
                self.record_cache[base_id][record.record_id] = record
            logger.info(f"Queried {len(records)} records from {base_id}/{table_name}")
            return records
        except Exception as e:
            logger.error(f"Failed to query records from {base_id}/{table_name}: {e}")
            return []
    async def create_brand_asset(
        self, brand_kit_base_id: str, asset_data: BrandAsset
    ) -> Optional[AirtableRecord]:
        """Create brand asset in brand kit base"""
        try:
            # Convert BrandAsset to Airtable fields
            fields = {
                "Asset_Name": asset_data.name,
                "Asset_Type": asset_data.asset_type,
                "Category": asset_data.category,
                "File_URL": asset_data.file_url,
                "File_Format": asset_data.file_format,
                "Usage_Context": asset_data.usage_contexts,
                "Brand_Compliance_Score": asset_data.brand_compliance_score,
                "Approval_Status": asset_data.approval_status,
                "Version": asset_data.version,
                "Created_By": asset_data.created_by,
                "Tags": asset_data.tags,
            }
            # Add color information if present
            if asset_data.color_hex:
                fields["Color_Hex"] = asset_data.color_hex
                fields["Color_RGB"] = asset_data.color_rgb
            # Add template information if present
            if asset_data.template_type:
                fields["Template_Type"] = asset_data.template_type
                fields["Template_Variables"] = asset_data.template_variables
            record = await self.create_record(
                brand_kit_base_id, "Template_Assets", fields, RecordType.BRAND_ASSET
            )
            logger.info(f"Created brand asset: {asset_data.name}")
            return record
        except Exception as e:
            logger.error(f"Failed to create brand asset: {e}")
            return None
    async def create_foundational_knowledge(
        self, sophia_base_id: str, knowledge_data: FoundationalKnowledge
    ) -> Optional[AirtableRecord]:
        """Create foundational knowledge entry for Sophia"""
        try:
            # Convert FoundationalKnowledge to Airtable fields
            fields = {
                "Title": knowledge_data.title,
                "Category": knowledge_data.category,
                "Knowledge_Type": knowledge_data.knowledge_type,
                "Content": knowledge_data.content,
                "Summary": knowledge_data.summary,
                "Key_Points": knowledge_data.key_points,
                "Business_Domains": knowledge_data.business_domains,
                "Use_Cases": knowledge_data.use_cases,
                "Importance_Level": knowledge_data.importance_level,
                "Confidence": knowledge_data.confidence_level,
                "Data_Sources": knowledge_data.data_sources,
                "Validation_Status": knowledge_data.validation_status,
                "Access_Count": knowledge_data.access_count,
                "Created_By": knowledge_data.created_by,
                "Tags": knowledge_data.tags,
            }
            record = await self.create_record(
                sophia_base_id,
                "Foundational_Knowledge",
                fields,
                RecordType.FOUNDATIONAL_KNOWLEDGE,
            )
            logger.info(f"Created foundational knowledge: {knowledge_data.title}")
            return record
        except Exception as e:
            logger.error(f"Failed to create foundational knowledge: {e}")
            return None
    async def get_sophia_knowledge(
        self,
        sophia_base_id: str,
        category: str = "",
        business_domain: str = "",
        max_results: int = 50,
    ) -> list[FoundationalKnowledge]:
        """Get foundational knowledge entries for Sophia"""
        try:
            # Build filter formula
            filters = []
            if category:
                filters.append(f"{{Category}} = '{category}'")
            if business_domain:
                filters.append(f"FIND('{business_domain}', {{Business_Domains}}) > 0")
            formula = " AND ".join([f"({f})" for f in filters]) if filters else ""
            # Query records
            records = await self.query_records(
                sophia_base_id,
                "Foundational_Knowledge",
                formula=formula,
                max_records=max_results,
                sort=[{"field": "Confidence", "direction": "desc"}],
            )
            # Convert to FoundationalKnowledge objects
            knowledge_entries = []
            for record in records:
                fields = record.fields
                knowledge = FoundationalKnowledge(
                    knowledge_id=record.record_id,
                    title=fields.get("Title", ""),
                    category=fields.get("Category", ""),
                    knowledge_type=fields.get("Knowledge_Type", ""),
                    content=fields.get("Content", ""),
                    summary=fields.get("Summary", ""),
                    key_points=fields.get("Key_Points", []),
                    business_domains=fields.get("Business_Domains", []),
                    use_cases=fields.get("Use_Cases", []),
                    importance_level=fields.get("Importance_Level", "medium"),
                    confidence_level=fields.get("Confidence", 0.9),
                    data_sources=fields.get("Data_Sources", []),
                    validation_status=fields.get("Validation_Status", "verified"),
                    access_count=fields.get("Access_Count", 0),
                    created_by=fields.get("Created_By", "system"),
                    tags=fields.get("Tags", []),
                )
                knowledge_entries.append(knowledge)
            logger.info(f"Retrieved {len(knowledge_entries)} knowledge entries")
            return knowledge_entries
        except Exception as e:
            logger.error(f"Failed to get Sophia knowledge: {e}")
            return []
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        min_interval = 1.0 / self.rate_limit_per_second
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        self.last_request_time = datetime.now()
    def _is_cache_valid(self, record: AirtableRecord) -> bool:
        """Check if cached record is still valid"""
        time_since_update = (datetime.now() - record.updated_at).total_seconds()
        return time_since_update < self.cache_ttl_seconds
    async def clear_expired_cache(self):
        """Clear expired cache entries"""
        now = datetime.now()
        for base_id in self.record_cache:
            expired_records = []
            for record_id, record in self.record_cache[base_id].items():
                if not self._is_cache_valid(record):
                    expired_records.append(record_id)
            for record_id in expired_records:
                del self.record_cache[base_id][record_id]
        self.last_cache_clear = now
        logger.info("Cleared expired cache entries")
    async def get_base_health_status(self) -> dict[str, dict[str, Any]]:
        """Get health status for all bases"""
        health_status = {}
        for base_id, base in self.bases.items():
            try:
                # Test API connectivity
                api_client = self.api_clients.get(base_id)
                if api_client:
                    # Simple test query to check connectivity
                    test_table = list(base.tables.keys())[0] if base.tables else None
                    if test_table:
                        await self.query_records(base_id, test_table, max_records=1)
                    health_status[base_id] = {
                        "status": "healthy",
                        "last_sync": base.last_sync,
                        "sync_status": base.sync_status.value,
                        "cached_records": len(self.record_cache.get(base_id, {})),
                        "tables_count": len(base.tables),
                    }
                else:
                    health_status[base_id] = {
                        "status": "no_api_client",
                        "error": "API client not initialized",
                    }
            except Exception as e:
                health_status[base_id] = {
                    "status": "error",
                    "error": str(e),
                    "last_sync": base.last_sync,
                }
        return health_status
