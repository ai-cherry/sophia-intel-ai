"""
NetSuite Connector for Enterprise Integration
Implements OAuth 2.0 and TBA authentication with NetSuite REST APIs
"""

import base64
import hashlib
import hmac
import json
import logging
import random
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import aiohttp

from app.integrations.connectors.base_connector import (
    BaseConnector,
    ConnectorConfig,
    DocChunk,
    SyncReport,
)
from app.memory.unified_memory_router import MemoryDomain

logger = logging.getLogger(__name__)


class NetSuiteAuthMethod(Enum):
    """NetSuite authentication methods"""

    TOKEN_BASED = "token_based"  # TBA
    OAUTH2 = "oauth2"


class NetSuiteRecordType(Enum):
    """Common NetSuite record types"""

    CUSTOMER = "customer"
    VENDOR = "vendor"
    EMPLOYEE = "employee"
    ITEM = "inventoryitem"
    SALES_ORDER = "salesorder"
    PURCHASE_ORDER = "purchaseorder"
    INVOICE = "invoice"
    PAYMENT = "customerpayment"
    JOURNAL_ENTRY = "journalentry"
    SUBSIDIARY = "subsidiary"
    DEPARTMENT = "department"
    CLASS = "class"
    LOCATION = "location"


@dataclass
class NetSuiteConfig(ConnectorConfig):
    """NetSuite-specific configuration"""

    account_id: str = ""
    auth_method: NetSuiteAuthMethod = NetSuiteAuthMethod.OAUTH2
    consumer_key: str = ""
    consumer_secret: str = ""
    token_id: str = ""
    token_secret: str = ""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "https://localhost:8080/callback"
    scope: str = "rest_webservices"
    suiteql_enabled: bool = True
    restlet_enabled: bool = False


class NetSuiteConnector(BaseConnector):
    """
    NetSuite connector implementation
    Supports both REST API and SuiteQL for comprehensive data access
    """

    def __init__(self, config: Optional[NetSuiteConfig] = None):
        """Initialize NetSuite connector"""
        if not config:
            config = NetSuiteConfig(
                name="netsuite",
                base_url="",  # Will be constructed from account_id
                api_version="v1",
                timeout_seconds=60,
                max_retries=3,
                rate_limit_calls=100,
                rate_limit_period=60,
                sync_interval=3600,
            )

        # Construct base URL from account ID
        if config.account_id:
            config.base_url = (
                f"https://{config.account_id}.suitetalk.api.netsuite.com/services/rest"
            )

        super().__init__(config)

        # Load NetSuite credentials from environment/secrets after parent init
        self._load_netsuite_config(config)
        self.config: NetSuiteConfig = config
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def _load_netsuite_config(self, config: NetSuiteConfig) -> None:
        """Load NetSuite configuration from secrets"""
        if self.credentials:
            config.account_id = self.credentials.get("account_id", config.account_id)
            config.consumer_key = self.credentials.get("consumer_key", config.consumer_key)
            config.consumer_secret = self.credentials.get("consumer_secret", config.consumer_secret)
            config.token_id = self.credentials.get("token_id", config.token_id)
            config.token_secret = self.credentials.get("token_secret", config.token_secret)
            config.client_id = self.credentials.get("client_id", config.client_id)
            config.client_secret = self.credentials.get("client_secret", config.client_secret)

    def _get_default_headers(self) -> dict[str, str]:
        """Get headers with NetSuite authentication"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SophiaIntelAI/NetSuite",
        }

        if self.config.auth_method == NetSuiteAuthMethod.TOKEN_BASED:
            # Generate OAuth 1.0a signature for TBA
            headers["Authorization"] = self._generate_tba_header("GET", "/")
        elif self.config.auth_method == NetSuiteAuthMethod.OAUTH2 and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _generate_tba_header(self, method: str, path: str) -> str:
        """Generate OAuth 1.0a header for Token-Based Authentication"""
        timestamp = str(int(time.time()))
        nonce = str(random.getrandbits(64))

        # OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.config.consumer_key,
            "oauth_token": self.config.token_id,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": timestamp,
            "oauth_nonce": nonce,
            "oauth_version": "1.0",
        }

        # Create signature base string
        base_url = f"{self.config.base_url}{path}"
        param_string = "&".join([f"{k}={v}" for k, v in sorted(oauth_params.items())])
        signature_base = (
            f"{method.upper()}&{urllib.parse.quote(base_url)}&{urllib.parse.quote(param_string)}"
        )

        # Generate signature
        signing_key = f"{self.config.consumer_secret}&{self.config.token_secret}"
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode("utf-8"),
                signature_base.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        oauth_params["oauth_signature"] = signature

        # Build authorization header
        auth_header = "OAuth " + ", ".join([f'{k}="{v}"' for k, v in oauth_params.items()])
        return auth_header

    async def _get_oauth2_token(self) -> bool:
        """Get OAuth 2.0 access token"""
        try:
            # Token endpoint
            token_url = f"{self.config.base_url}/oauth2/v1/token"

            # Token request
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": self.config.scope,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                        logger.info("NetSuite OAuth 2.0 token obtained")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Failed to get NetSuite token: {error}")
                        return False

        except Exception as e:
            logger.error(f"NetSuite OAuth 2.0 error: {e}")
            return False

    async def _ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication"""
        if self.config.auth_method == NetSuiteAuthMethod.OAUTH2:
            # Check if token needs refresh
            if not self.access_token or (
                self.token_expires_at and datetime.now() >= self.token_expires_at
            ):
                return await self._get_oauth2_token()
        return True

    async def test_connection(self) -> bool:
        """Test NetSuite connection"""
        try:
            # Ensure authenticated
            if not await self._ensure_authenticated():
                return False

            # Test with a simple API call
            response = await self.make_request("GET", "record/v1/metadata-catalog")
            return "items" in response

        except Exception as e:
            logger.error(f"NetSuite connection test failed: {e}")
            return False

    async def fetch_data(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Fetch data from NetSuite

        Args:
            params: Query parameters including record_type, filters, etc.

        Returns:
            Fetched records
        """
        record_type = params.get("record_type", NetSuiteRecordType.CUSTOMER.value)
        filters = params.get("filters", {})
        fields = params.get("fields", [])
        limit = params.get("limit", 100)
        offset = params.get("offset", 0)

        # Build query
        query_params = {"limit": limit, "offset": offset}

        # Add field selection
        if fields:
            query_params["fields"] = ",".join(fields)

        # Add filters
        if filters:
            query_params["q"] = self._build_filter_query(filters)

        # Fetch records
        endpoint = f"record/v1/{record_type}"
        response = await self.make_request("GET", endpoint, params=query_params)

        return response

    async def fetch_by_suiteql(
        self, query: str, limit: int = 1000, offset: int = 0
    ) -> dict[str, Any]:
        """
        Fetch data using SuiteQL

        Args:
            query: SuiteQL query
            limit: Result limit
            offset: Result offset

        Returns:
            Query results
        """
        if not self.config.suiteql_enabled:
            raise ValueError("SuiteQL is not enabled")

        # SuiteQL endpoint
        endpoint = "query/v1/suiteql"

        # Query payload
        payload = {"q": query}

        # Add pagination
        params = {"limit": limit, "offset": offset}

        # Execute query
        response = await self.make_request("POST", endpoint, params=params, json_data=payload)

        return response

    def _build_filter_query(self, filters: dict[str, Any]) -> str:
        """Build filter query string for NetSuite API"""
        conditions = []

        for field, value in filters.items():
            if isinstance(value, dict):
                # Complex filter (e.g., {"operator": ">=", "value": 100})
                operator = value.get("operator", "IS")
                val = value.get("value")
                conditions.append(f"{field} {operator} {val}")
            else:
                # Simple equality
                if isinstance(value, str):
                    conditions.append(f'{field} IS "{value}"')
                else:
                    conditions.append(f"{field} IS {value}")

        return " AND ".join(conditions)

    async def get_record(self, record_type: str, record_id: str) -> dict[str, Any]:
        """
        Get a single record by ID

        Args:
            record_type: Type of record
            record_id: Record internal ID

        Returns:
            Record data
        """
        endpoint = f"record/v1/{record_type}/{record_id}"
        return await self.make_request("GET", endpoint)

    async def create_record(self, record_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new record

        Args:
            record_type: Type of record to create
            data: Record data

        Returns:
            Created record
        """
        endpoint = f"record/v1/{record_type}"
        return await self.make_request("POST", endpoint, json_data=data)

    async def update_record(
        self, record_type: str, record_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update an existing record

        Args:
            record_type: Type of record
            record_id: Record internal ID
            data: Update data

        Returns:
            Updated record
        """
        endpoint = f"record/v1/{record_type}/{record_id}"
        return await self.make_request("PATCH", endpoint, json_data=data)

    async def delete_record(self, record_type: str, record_id: str) -> bool:
        """
        Delete a record

        Args:
            record_type: Type of record
            record_id: Record internal ID

        Returns:
            Success status
        """
        try:
            endpoint = f"record/v1/{record_type}/{record_id}"
            await self.make_request("DELETE", endpoint)
            return True
        except Exception as e:
            logger.error(f"Failed to delete NetSuite record: {e}")
            return False

    async def sync_customers(self) -> SyncReport:
        """Sync customer records"""
        params = {
            "record_type": NetSuiteRecordType.CUSTOMER.value,
            "fields": [
                "entityId",
                "companyName",
                "email",
                "phone",
                "dateCreated",
                "lastModifiedDate",
            ],
            "limit": 1000,
        }

        return await self.sync_record_type(params)

    async def sync_sales_orders(self, days_back: int = 30) -> SyncReport:
        """Sync recent sales orders"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")

        params = {
            "record_type": NetSuiteRecordType.SALES_ORDER.value,
            "filters": {"tranDate": {"operator": ">=", "value": cutoff_date}},
            "fields": ["tranId", "entity", "tranDate", "total", "status"],
            "limit": 1000,
        }

        return await self.sync_record_type(params)

    async def sync_record_type(self, params: dict[str, Any]) -> SyncReport:
        """
        Sync a specific record type

        Args:
            params: Sync parameters

        Returns:
            Sync report
        """
        start_time = datetime.now()
        report = SyncReport(success=False, records_fetched=0, records_stored=0)

        try:
            # Ensure authenticated
            if not await self._ensure_authenticated():
                report.errors.append("Authentication failed")
                return report

            # Fetch records
            all_records = []
            offset = 0
            has_more = True

            while has_more:
                params["offset"] = offset
                response = await self.fetch_data(params)

                if "items" in response:
                    records = response["items"]
                    all_records.extend(records)
                    report.records_fetched += len(records)

                    # Check for more records
                    has_more = response.get("hasMore", False)
                    offset = response.get("offset", offset) + len(records)
                else:
                    has_more = False

            # Transform to chunks
            chunks = await self._transform_netsuite_records(all_records, params.get("record_type"))

            # Store in memory
            if chunks:
                from app.memory.unified_memory_router import get_memory_router

                memory = get_memory_router()
                upsert_report = await memory.upsert_chunks(chunks, domain=MemoryDomain.SOPHIA)
                report.records_stored = upsert_report.chunks_stored

            report.success = True
            logger.info(
                f"NetSuite sync completed: {report.records_fetched} fetched, "
                f"{report.records_stored} stored"
            )

        except Exception as e:
            logger.error(f"NetSuite sync failed: {e}")
            report.errors.append(str(e))

        finally:
            report.duration_seconds = (datetime.now() - start_time).total_seconds()
            report.next_sync = datetime.now() + timedelta(seconds=self.config.sync_interval)

        return report

    async def _transform_netsuite_records(
        self, records: list[dict], record_type: str
    ) -> list[DocChunk]:
        """Transform NetSuite records to document chunks"""
        chunks = []

        for record in records:
            # Create searchable content
            content_parts = [f"NetSuite {record_type}"]

            # Add key fields to content
            if "entityId" in record:
                content_parts.append(f"ID: {record['entityId']}")
            if "companyName" in record:
                content_parts.append(f"Company: {record['companyName']}")
            if "tranId" in record:
                content_parts.append(f"Transaction: {record['tranId']}")
            if "email" in record:
                content_parts.append(f"Email: {record['email']}")

            # Include full record as JSON
            content_parts.append(f"Data: {json.dumps(record, default=str)}")

            chunk = DocChunk(
                content="\n".join(content_parts),
                source_uri=f"netsuite://{record_type}/{record.get('id', 'unknown')}",
                domain=MemoryDomain.SOPHIA,
                metadata={
                    "connector": "netsuite",
                    "record_type": record_type,
                    "internal_id": str(record.get("id", "")),
                    "timestamp": datetime.now().isoformat(),
                },
            )
            chunks.append(chunk)

        return chunks

    async def _process_webhook(self, payload: dict[str, Any]) -> None:
        """Process NetSuite webhook"""
        # NetSuite webhooks are typically handled through SuiteScript
        # This would process real-time updates
        event_type = payload.get("type")
        record_type = payload.get("recordType")
        record_id = payload.get("recordId")

        logger.info(f"Processing NetSuite webhook: {event_type} for {record_type}/{record_id}")

        # Fetch updated record
        if event_type in ["create", "edit"]:
            try:
                record = await self.get_record(record_type, record_id)
                chunks = await self._transform_netsuite_records([record], record_type)

                if chunks:
                    from app.memory.unified_memory_router import get_memory_router

                    memory = get_memory_router()
                    await memory.upsert_chunks(chunks, domain=MemoryDomain.SOPHIA)

            except Exception as e:
                logger.error(f"Failed to process NetSuite webhook: {e}")

    async def execute_saved_search(self, search_id: str) -> dict[str, Any]:
        """
        Execute a saved search

        Args:
            search_id: Saved search internal ID

        Returns:
            Search results
        """
        # This would require RESTlet implementation
        raise NotImplementedError("Saved search execution requires RESTlet setup")

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """Get NetSuite integration metrics for dashboard"""
        return {
            "connector": "NetSuite",
            "status": self.status.value,
            "auth_method": self.config.auth_method.value,
            "account_id": self.config.account_id,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "metrics": self.metrics,
            "features": {
                "rest_api": True,
                "suiteql": self.config.suiteql_enabled,
                "restlets": self.config.restlet_enabled,
                "webhooks": self.config.webhook_enabled,
            },
        }
