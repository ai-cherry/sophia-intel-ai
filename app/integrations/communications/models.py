"""
Communications Integration Models

Data models for multi-channel communication platform integrations,
compliance management, and campaign orchestration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class CommunicationChannel(str, Enum):
    """Communication channels for outreach"""

    SMS = "sms"
    EMAIL = "email"
    LINKEDIN = "linkedin"
    PHONE = "phone"
    DIRECT_MAIL = "direct_mail"
    SOCIAL_MEDIA = "social_media"


class MessageType(str, Enum):
    """Types of messages for different purposes"""

    INTRODUCTION = "introduction"
    FOLLOW_UP = "follow_up"
    VALUE_PROPOSITION = "value_proposition"
    MEETING_REQUEST = "meeting_request"
    CASE_STUDY = "case_study"
    SOCIAL_PROOF = "social_proof"
    EDUCATIONAL = "educational"
    RE_ENGAGEMENT = "re_engagement"
    THANK_YOU = "thank_you"
    NURTURE = "nurture"


class DeliveryStatus(str, Enum):
    """Message delivery status"""

    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"
    BLOCKED = "blocked"
    UNSUBSCRIBED = "unsubscribed"


class ConsentStatus(str, Enum):
    """Consent status for communications"""

    GRANTED = "granted"
    PENDING = "pending"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ComplianceStatus(str, Enum):
    """Compliance status for outreach activities"""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    APPROVED = "approved"
    BLOCKED = "blocked"


@dataclass
class Prospect:
    """Prospect information for outreach campaigns"""

    prospect_id: str = field(default_factory=lambda: str(uuid4()))
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    job_title: str = ""
    industry: str = ""

    # Contact preferences
    preferred_channel: CommunicationChannel = CommunicationChannel.EMAIL
    timezone: str = "UTC"
    language: str = "en"

    # Consent and compliance
    email_consent: ConsentStatus = ConsentStatus.UNKNOWN
    sms_consent: ConsentStatus = ConsentStatus.UNKNOWN
    phone_consent: ConsentStatus = ConsentStatus.UNKNOWN
    linkedin_connection_status: str = "not_connected"

    # Engagement data
    last_contacted: Optional[datetime] = None
    last_response: Optional[datetime] = None
    engagement_score: float = 0.0
    response_rate: float = 0.0

    # Segmentation
    lead_score: int = 0
    segment: str = ""
    priority: str = "medium"  # high, medium, low

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def update_engagement(self, channel: CommunicationChannel, engagement_type: str):
        """Update engagement metrics"""
        self.last_contacted = datetime.now()
        if engagement_type in ["replied", "clicked", "meeting_scheduled"]:
            self.last_response = datetime.now()
            # Simple engagement score calculation
            self.engagement_score = min(self.engagement_score + 0.1, 1.0)
        self.updated_at = datetime.now()

    def has_valid_consent(self, channel: CommunicationChannel) -> bool:
        """Check if prospect has valid consent for channel"""
        consent_mapping = {
            CommunicationChannel.EMAIL: self.email_consent,
            CommunicationChannel.SMS: self.sms_consent,
            CommunicationChannel.PHONE: self.phone_consent,
        }

        consent = consent_mapping.get(channel, ConsentStatus.UNKNOWN)
        return consent == ConsentStatus.GRANTED

    def is_eligible_for_outreach(self, channel: CommunicationChannel) -> bool:
        """Check if prospect is eligible for outreach on channel"""
        # Check consent
        if not self.has_valid_consent(channel):
            return False

        # Check recent contact frequency
        if self.last_contacted:
            hours_since_contact = (
                datetime.now() - self.last_contacted
            ).total_seconds() / 3600
            if hours_since_contact < 24:  # Minimum 24 hours between contacts
                return False

        return True


@dataclass
class MessageTemplate:
    """Template for outreach messages"""

    template_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    message_type: MessageType = MessageType.INTRODUCTION
    channel: CommunicationChannel = CommunicationChannel.EMAIL

    # Content
    subject_template: str = ""  # For email
    body_template: str = ""
    variables: list[str] = field(default_factory=list)  # Placeholder variables

    # Personalization
    personalization_level: str = "basic"  # basic, advanced, hyper
    dynamic_content_rules: dict[str, Any] = field(default_factory=dict)

    # Performance
    usage_count: int = 0
    success_rate: float = 0.0
    avg_response_rate: float = 0.0
    last_used: Optional[datetime] = None

    # A/B Testing
    is_test_variant: bool = False
    parent_template_id: Optional[str] = None
    test_results: dict[str, Any] = field(default_factory=dict)

    # Approval and compliance
    approval_status: str = "approved"
    brand_compliance_score: float = 1.0
    compliance_notes: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: list[str] = field(default_factory=list)

    def render_message(
        self, prospect: Prospect, custom_variables: dict[str, Any] = None
    ) -> dict[str, str]:
        """Render message template with prospect data"""
        variables = {
            "first_name": prospect.first_name,
            "last_name": prospect.last_name,
            "full_name": prospect.full_name,
            "company": prospect.company,
            "job_title": prospect.job_title,
            "industry": prospect.industry,
        }

        if custom_variables:
            variables.update(custom_variables)

        # Render subject and body
        subject = self.subject_template
        body = self.body_template

        for var_name, value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))

        return {
            "subject": subject,
            "body": body,
            "rendered_at": datetime.now().isoformat(),
        }

    def update_performance(self, delivered: bool, responded: bool):
        """Update template performance metrics"""
        self.usage_count += 1
        self.last_used = datetime.now()

        # Update success rate (simple calculation)
        if delivered:
            old_success = self.success_rate * (self.usage_count - 1)
            self.success_rate = (old_success + 1.0) / self.usage_count

        # Update response rate
        if responded:
            old_response = self.avg_response_rate * (self.usage_count - 1)
            self.avg_response_rate = (old_response + 1.0) / self.usage_count

        self.updated_at = datetime.now()


@dataclass
class ComplianceRecord:
    """Record of compliance check or violation"""

    record_id: str = field(default_factory=lambda: str(uuid4()))
    prospect_id: str = ""
    campaign_id: str = ""
    channel: CommunicationChannel = CommunicationChannel.EMAIL

    # Compliance details
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    regulation_type: str = "TCPA"  # TCPA, CAN-SPAM, GDPR, CCPA
    violation_type: str = ""  # consent, timing, frequency, content
    violation_description: str = ""

    # Context
    message_content: str = ""
    send_time: Optional[datetime] = None
    recipient_timezone: str = "UTC"

    # Resolution
    action_taken: str = ""
    resolved: bool = False
    resolution_notes: str = ""
    reviewed_by: str = ""

    # Audit trail
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    system_flags: list[str] = field(default_factory=list)

    def add_violation(self, violation_type: str, description: str):
        """Add compliance violation"""
        self.compliance_status = ComplianceStatus.NON_COMPLIANT
        self.violation_type = violation_type
        self.violation_description = description
        self.updated_at = datetime.now()

        # Add system flag
        self.system_flags.append(
            f"VIOLATION_{violation_type.upper()}_{datetime.now().isoformat()}"
        )

    def resolve_violation(self, action: str, reviewer: str, notes: str = ""):
        """Resolve compliance violation"""
        self.action_taken = action
        self.resolved = True
        self.resolution_notes = notes
        self.reviewed_by = reviewer
        self.compliance_status = ComplianceStatus.APPROVED
        self.updated_at = datetime.now()


@dataclass
class OutreachMessage:
    """Individual outreach message"""

    message_id: str = field(default_factory=lambda: str(uuid4()))
    campaign_id: str = ""
    prospect_id: str = ""
    template_id: str = ""

    # Message details
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    message_type: MessageType = MessageType.INTRODUCTION
    subject: str = ""
    content: str = ""

    # Delivery information
    recipient_email: str = ""
    recipient_phone: str = ""
    sender_name: str = ""
    sender_email: str = ""

    # Status and timing
    status: DeliveryStatus = DeliveryStatus.QUEUED
    scheduled_send_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    delivered_time: Optional[datetime] = None
    read_time: Optional[datetime] = None
    response_time: Optional[datetime] = None

    # Engagement tracking
    opened: bool = False
    clicked: bool = False
    replied: bool = False
    meeting_scheduled: bool = False
    unsubscribed: bool = False

    # External platform IDs
    platform_message_id: str = ""  # ID from email/SMS platform
    platform_thread_id: str = ""

    # Performance
    delivery_attempts: int = 0
    last_delivery_attempt: Optional[datetime] = None
    error_message: str = ""

    # Compliance
    compliance_record_id: Optional[str] = None
    tcpa_compliant: bool = False
    consent_verified: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_status(self, new_status: DeliveryStatus, timestamp: datetime = None):
        """Update message delivery status"""
        self.status = new_status
        timestamp = timestamp or datetime.now()

        # Update relevant timestamp fields
        if new_status == DeliveryStatus.SENT:
            self.sent_time = timestamp
        elif new_status == DeliveryStatus.DELIVERED:
            self.delivered_time = timestamp
        elif new_status == DeliveryStatus.READ:
            self.read_time = timestamp
            self.opened = True
        elif new_status == DeliveryStatus.REPLIED:
            self.response_time = timestamp
            self.replied = True
        elif new_status == DeliveryStatus.CLICKED:
            self.clicked = True
        elif new_status == DeliveryStatus.UNSUBSCRIBED:
            self.unsubscribed = True

        self.updated_at = timestamp

    def calculate_engagement_score(self) -> float:
        """Calculate engagement score for message"""
        score = 0.0

        if self.status == DeliveryStatus.DELIVERED:
            score += 0.2
        if self.opened:
            score += 0.3
        if self.clicked:
            score += 0.3
        if self.replied:
            score += 0.5
        if self.meeting_scheduled:
            score += 0.8

        return min(score, 1.0)


@dataclass
class OutreachSequence:
    """Multi-step outreach sequence"""

    sequence_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Sequence configuration
    steps: list[dict[str, Any]] = field(default_factory=list)
    total_steps: int = 0
    active: bool = True

    # Targeting
    target_segments: list[str] = field(default_factory=list)
    priority_prospects: list[str] = field(default_factory=list)
    exclusion_rules: list[str] = field(default_factory=list)

    # Performance
    prospects_enrolled: int = 0
    completion_rate: float = 0.0
    response_rate: float = 0.0
    meeting_rate: float = 0.0

    # A/B Testing
    is_test_sequence: bool = False
    test_variations: list[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

    def add_step(
        self,
        step_number: int,
        channel: CommunicationChannel,
        template_id: str,
        delay_days: int = 1,
        conditions: dict[str, Any] = None,
    ):
        """Add step to outreach sequence"""
        step = {
            "step_number": step_number,
            "channel": channel.value,
            "template_id": template_id,
            "delay_days": delay_days,
            "conditions": conditions or {},
            "active": True,
        }

        self.steps.append(step)
        self.total_steps = len(self.steps)
        self.updated_at = datetime.now()

    def get_next_step(
        self, current_step: int, prospect_data: dict[str, Any] = None
    ) -> Optional[dict[str, Any]]:
        """Get next step in sequence for prospect"""
        next_step_number = current_step + 1

        for step in self.steps:
            if step["step_number"] == next_step_number and step["active"]:
                # Check conditions if specified
                conditions = step.get("conditions", {})
                if conditions and prospect_data:
                    # Simple condition checking - would be more complex in production
                    if not self._check_step_conditions(conditions, prospect_data):
                        continue

                return step

        return None

    def _check_step_conditions(
        self, conditions: dict[str, Any], prospect_data: dict[str, Any]
    ) -> bool:
        """Check if step conditions are met"""
        # Simplified condition checking
        for condition_key, expected_value in conditions.items():
            if prospect_data.get(condition_key) != expected_value:
                return False
        return True


@dataclass
class OutreachCampaign:
    """Complete outreach campaign"""

    campaign_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    campaign_type: str = "prospecting"  # prospecting, nurture, re_engagement

    # Campaign configuration
    channels: list[CommunicationChannel] = field(default_factory=list)
    sequences: list[str] = field(default_factory=list)  # Sequence IDs
    target_segments: list[str] = field(default_factory=list)

    # Scheduling
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: str = "UTC"
    send_times: list[str] = field(default_factory=list)  # ["09:00", "14:00"]

    # Status
    status: str = "draft"  # draft, active, paused, completed
    approval_required: bool = True
    approved_by: str = ""
    approval_date: Optional[datetime] = None

    # Performance tracking
    prospects_targeted: int = 0
    messages_sent: int = 0
    messages_delivered: int = 0
    responses_received: int = 0
    meetings_scheduled: int = 0
    opportunities_created: int = 0

    # Budget and costs
    budget_allocated: float = 0.0
    budget_spent: float = 0.0
    cost_per_message: float = 0.0
    cost_per_response: float = 0.0
    cost_per_meeting: float = 0.0

    # Compliance
    compliance_review_required: bool = True
    compliance_approved: bool = False
    compliance_notes: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    tags: list[str] = field(default_factory=list)

    def calculate_performance_metrics(self) -> dict[str, float]:
        """Calculate campaign performance metrics"""
        metrics = {
            "delivery_rate": 0.0,
            "response_rate": 0.0,
            "meeting_rate": 0.0,
            "opportunity_rate": 0.0,
            "roi": 0.0,
        }

        if self.messages_sent > 0:
            metrics["delivery_rate"] = self.messages_delivered / self.messages_sent

        if self.messages_delivered > 0:
            metrics["response_rate"] = self.responses_received / self.messages_delivered
            metrics["meeting_rate"] = self.meetings_scheduled / self.messages_delivered
            metrics["opportunity_rate"] = (
                self.opportunities_created / self.messages_delivered
            )

        if self.budget_spent > 0:
            # Simple ROI calculation - would need revenue attribution in production
            estimated_revenue = self.opportunities_created * 1000  # Mock value
            metrics["roi"] = (estimated_revenue - self.budget_spent) / self.budget_spent

        return metrics

    def update_performance(
        self,
        messages_sent: int = 0,
        messages_delivered: int = 0,
        responses_received: int = 0,
        meetings_scheduled: int = 0,
        opportunities_created: int = 0,
        cost_incurred: float = 0.0,
    ):
        """Update campaign performance metrics"""
        self.messages_sent += messages_sent
        self.messages_delivered += messages_delivered
        self.responses_received += responses_received
        self.meetings_scheduled += meetings_scheduled
        self.opportunities_created += opportunities_created
        self.budget_spent += cost_incurred

        # Update derived metrics
        if self.messages_sent > 0:
            self.cost_per_message = self.budget_spent / self.messages_sent

        if self.responses_received > 0:
            self.cost_per_response = self.budget_spent / self.responses_received

        if self.meetings_scheduled > 0:
            self.cost_per_meeting = self.budget_spent / self.meetings_scheduled

        self.updated_at = datetime.now()

    def is_active(self) -> bool:
        """Check if campaign is currently active"""
        if self.status != "active":
            return False

        now = datetime.now()

        if self.start_date and now < self.start_date:
            return False

        return not (self.end_date and now > self.end_date)

    def get_campaign_health_score(self) -> float:
        """Calculate overall campaign health score"""
        if self.messages_sent == 0:
            return 0.0

        metrics = self.calculate_performance_metrics()

        # Weighted health score
        health_factors = [
            metrics["delivery_rate"] * 0.3,
            metrics["response_rate"] * 10 * 0.4,  # Scale response rate
            metrics["meeting_rate"] * 20 * 0.3,  # Scale meeting rate
        ]

        return min(sum(health_factors), 1.0)
