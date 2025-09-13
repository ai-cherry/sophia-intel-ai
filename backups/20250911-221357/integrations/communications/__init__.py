"""
Communications Integration Suite
Comprehensive communications platform integrations for:
- TCPA-compliant SMS outreach with Twilio
- Email campaign automation via HubSpot
- LinkedIn social selling and automation
- Multi-channel orchestration and coordination
- Compliance monitoring and audit trails
"""
from .email_automation import (
    EmailCampaignOrchestrator,
    EmailTemplateManager,
    HubSpotEmailManager,
)
from .linkedin_automation import (
    LinkedInConnectionManager,
    LinkedInSalesNavigator,
    SocialSellingOrchestrator,
)
from .models import (
    CommunicationChannel,
    ComplianceRecord,
    DeliveryStatus,
    MessageTemplate,
    OutreachCampaign,
)
from .multi_channel import (
    ChannelCoordinator,
    CrossChannelAnalytics,
    MultiChannelOrchestrator,
)
from .sms_outreach import (
    ConsentManager,
    SMSCampaignOrchestrator,
    TCPAComplianceEngine,
    TwilioSMSManager,
)
__all__ = [
    "TCPAComplianceEngine",
    "TwilioSMSManager",
    "SMSCampaignOrchestrator",
    "ConsentManager",
    "HubSpotEmailManager",
    "EmailCampaignOrchestrator",
    "EmailTemplateManager",
    "LinkedInSalesNavigator",
    "LinkedInConnectionManager",
    "SocialSellingOrchestrator",
    "MultiChannelOrchestrator",
    "ChannelCoordinator",
    "CrossChannelAnalytics",
    "OutreachCampaign",
    "CommunicationChannel",
    "ComplianceRecord",
    "MessageTemplate",
    "DeliveryStatus",
]
