"""
Airtable Federated Architecture Integration
Comprehensive Airtable integration for:
- Federated data architecture with domain-specific bases
- Shared core data synchronization
- Brand kit and asset management
- Sophia foundational knowledge base
- Cross-domain data sync and collaboration
"""
from .base_manager import AirtableBaseManager
from .connectors import (
    CustomerSuccessConnector,
    FinanceOpsConnector,
    MarketingOpsConnector,
    SalesIntelligenceConnector,
    SharedDataConnector,
)
from .models import (
    AirtableBase,
    AirtableRecord,
    BrandAsset,
    FoundationalKnowledge,
    SyncConfiguration,
)
from .sync_engine import FederatedSyncEngine
__all__ = [
    "AirtableBaseManager",
    "FederatedSyncEngine",
    "AirtableBase",
    "AirtableRecord",
    "SyncConfiguration",
    "BrandAsset",
    "FoundationalKnowledge",
    "SharedDataConnector",
    "MarketingOpsConnector",
    "SalesIntelligenceConnector",
    "CustomerSuccessConnector",
    "FinanceOpsConnector",
]
