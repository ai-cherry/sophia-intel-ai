"""
TCPA-Compliant SMS Outreach System

Comprehensive SMS outreach system with Twilio integration featuring:
- TCPA compliance engine and monitoring
- Consent management and verification
- SMS campaign orchestration
- Delivery tracking and analytics
- Compliance audit trails
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from twilio.base.exceptions import TwilioException
from twilio.rest import Client as TwilioClient

from .models import (
    CommunicationChannel,
    ComplianceRecord,
    ComplianceStatus,
    ConsentStatus,
    DeliveryStatus,
    OutreachMessage,
    Prospect,
)

logger = logging.getLogger(__name__)


class ConsentManager:
    """
    Manages consent for SMS communications with TCPA compliance
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.consent_records: Dict[str, Dict[str, Any]] = {}
        self.opt_out_keywords = ["STOP", "QUIT", "UNSUBSCRIBE", "CANCEL", "END", "OPT-OUT"]
        self.opt_in_keywords = ["START", "YES", "SUBSCRIBE", "JOIN", "OPT-IN"]

    async def verify_consent(self, phone_number: str, prospect_id: str = "") -> Tuple[bool, str]:
        """Verify SMS consent for phone number"""
        try:
            # Clean phone number
            clean_phone = self._clean_phone_number(phone_number)

            # Check consent record
            consent_record = self.consent_records.get(clean_phone)

            if not consent_record:
                return False, "No consent record found"

            # Check consent status
            if consent_record["status"] != ConsentStatus.GRANTED.value:
                return False, f"Consent status: {consent_record['status']}"

            # Check consent expiration
            if self._is_consent_expired(consent_record):
                return False, "Consent has expired"

            # Check do not call registry status
            if await self._check_dnc_registry(clean_phone):
                return False, "Phone number on Do Not Call registry"

            return True, "Consent verified"

        except Exception as e:
            logger.error(f"Error verifying consent for {phone_number}: {e}")
            return False, f"Verification error: {str(e)}"

    async def record_consent(
        self,
        phone_number: str,
        prospect_id: str,
        consent_method: str,
        opt_in_message: str = "",
        consent_source: str = "",
    ) -> bool:
        """Record explicit consent for SMS communications"""
        try:
            clean_phone = self._clean_phone_number(phone_number)

            consent_record = {
                "phone_number": clean_phone,
                "prospect_id": prospect_id,
                "status": ConsentStatus.GRANTED.value,
                "consent_method": consent_method,  # web_form, sms, phone, email
                "opt_in_message": opt_in_message,
                "consent_source": consent_source,
                "consent_date": datetime.now(timezone.utc),
                "expiry_date": datetime.now(timezone.utc) + timedelta(days=365),
                "revocation_date": None,
                "audit_trail": [
                    {
                        "action": "consent_granted",
                        "timestamp": datetime.now(timezone.utc),
                        "method": consent_method,
                        "source": consent_source,
                    }
                ],
            }

            self.consent_records[clean_phone] = consent_record
            logger.info(f"Recorded consent for {clean_phone} via {consent_method}")

            return True

        except Exception as e:
            logger.error(f"Error recording consent for {phone_number}: {e}")
            return False

    async def revoke_consent(
        self,
        phone_number: str,
        revocation_method: str = "sms_opt_out",
        revocation_message: str = "",
    ) -> bool:
        """Revoke SMS consent"""
        try:
            clean_phone = self._clean_phone_number(phone_number)

            if clean_phone not in self.consent_records:
                logger.warning(f"No consent record found for {clean_phone}")
                return True  # Already opted out

            consent_record = self.consent_records[clean_phone]
            consent_record["status"] = ConsentStatus.REVOKED.value
            consent_record["revocation_date"] = datetime.now(timezone.utc)
            consent_record["revocation_method"] = revocation_method
            consent_record["revocation_message"] = revocation_message

            # Add to audit trail
            consent_record["audit_trail"].append(
                {
                    "action": "consent_revoked",
                    "timestamp": datetime.now(timezone.utc),
                    "method": revocation_method,
                    "message": revocation_message,
                }
            )

            logger.info(f"Revoked consent for {clean_phone}")
            return True

        except Exception as e:
            logger.error(f"Error revoking consent for {phone_number}: {e}")
            return False

    async def process_inbound_message(self, phone_number: str, message_body: str) -> Dict[str, Any]:
        """Process inbound SMS message for opt-in/opt-out"""
        try:
            clean_phone = self._clean_phone_number(phone_number)
            message_upper = message_body.upper().strip()

            result = {
                "phone_number": clean_phone,
                "message": message_body,
                "action": "none",
                "processed_at": datetime.now(timezone.utc),
            }

            # Check for opt-out keywords
            if any(keyword in message_upper for keyword in self.opt_out_keywords):
                await self.revoke_consent(
                    clean_phone, revocation_method="sms_opt_out", revocation_message=message_body
                )
                result["action"] = "opt_out"
                result["auto_response"] = "You have been unsubscribed from SMS messages."

            # Check for opt-in keywords
            elif any(keyword in message_upper for keyword in self.opt_in_keywords):
                # Note: Real implementation would require double opt-in
                result["action"] = "opt_in_request"
                result["auto_response"] = "Reply YES to confirm you want to receive SMS messages."

            return result

        except Exception as e:
            logger.error(f"Error processing inbound message from {phone_number}: {e}")
            return {"error": str(e)}

    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone_number)

        # Add country code if missing (assume US)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"

    def _is_consent_expired(self, consent_record: Dict[str, Any]) -> bool:
        """Check if consent has expired"""
        if not consent_record.get("expiry_date"):
            return False

        return datetime.now(timezone.utc) > consent_record["expiry_date"]

    async def _check_dnc_registry(self, phone_number: str) -> bool:
        """Check if phone number is on Do Not Call registry"""
        # In production, would integrate with actual DNC registry API
        # For now, return False (not on DNC registry)
        return False

    def get_consent_status(self, phone_number: str) -> Dict[str, Any]:
        """Get detailed consent status for phone number"""
        clean_phone = self._clean_phone_number(phone_number)
        consent_record = self.consent_records.get(clean_phone)

        if not consent_record:
            return {
                "phone_number": clean_phone,
                "status": ConsentStatus.UNKNOWN.value,
                "has_consent": False,
            }

        return {
            "phone_number": clean_phone,
            "status": consent_record["status"],
            "consent_date": consent_record.get("consent_date"),
            "expiry_date": consent_record.get("expiry_date"),
            "consent_method": consent_record.get("consent_method"),
            "has_consent": (
                consent_record["status"] == ConsentStatus.GRANTED.value
                and not self._is_consent_expired(consent_record)
            ),
        }


class TCPAComplianceEngine:
    """
    TCPA Compliance Engine for SMS communications
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.consent_manager = ConsentManager(config)
        self.compliance_violations: List[ComplianceRecord] = []

        # TCPA compliance rules
        self.quiet_hours_start = 21  # 9 PM
        self.quiet_hours_end = 8  # 8 AM
        self.max_daily_messages = 3
        self.min_message_interval_hours = 4
        self.business_only_days = True  # Only send Monday-Friday

    async def validate_sms_outreach(
        self, prospect: Prospect, message_content: str, scheduled_time: datetime = None
    ) -> Dict[str, Any]:
        """Complete TCPA compliance validation for SMS outreach"""
        scheduled_time = scheduled_time or datetime.now(timezone.utc)

        validation_result = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "approved_send_time": scheduled_time,
            "compliance_score": 1.0,
        }

        # Check consent
        consent_valid, consent_reason = await self.consent_manager.verify_consent(
            prospect.phone, prospect.prospect_id
        )

        if not consent_valid:
            validation_result["compliant"] = False
            validation_result["violations"].append(
                {
                    "type": "consent_violation",
                    "description": f"Invalid consent: {consent_reason}",
                    "severity": "critical",
                }
            )
            validation_result["compliance_score"] -= 0.5

        # Check timing restrictions
        timing_validation = await self._validate_timing(prospect, scheduled_time)
        if not timing_validation["valid"]:
            validation_result["compliant"] = False
            validation_result["violations"].extend(timing_validation["violations"])
            validation_result["compliance_score"] -= 0.3

            # Suggest optimal send time
            optimal_time = await self._suggest_optimal_send_time(prospect, scheduled_time)
            validation_result["approved_send_time"] = optimal_time

        # Check frequency limits
        frequency_validation = await self._validate_frequency(prospect, scheduled_time)
        if not frequency_validation["valid"]:
            validation_result["compliant"] = False
            validation_result["violations"].extend(frequency_validation["violations"])
            validation_result["compliance_score"] -= 0.2

        # Check message content
        content_validation = await self._validate_message_content(message_content)
        if not content_validation["valid"]:
            validation_result["warnings"].extend(content_validation["warnings"])
            validation_result["compliance_score"] -= 0.1

        # Final compliance score
        validation_result["compliance_score"] = max(0.0, validation_result["compliance_score"])

        # Log compliance check
        await self._log_compliance_check(prospect, validation_result)

        return validation_result

    async def _validate_timing(
        self, prospect: Prospect, scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Validate timing compliance with TCPA quiet hours"""
        violations = []

        # Convert to prospect's timezone
        prospect_tz = prospect.timezone or "UTC"
        # In production, would use actual timezone conversion
        local_time = scheduled_time  # Simplified for demo

        # Check quiet hours (9 PM to 8 AM)
        hour = local_time.hour
        if hour >= self.quiet_hours_start or hour < self.quiet_hours_end:
            violations.append(
                {
                    "type": "quiet_hours_violation",
                    "description": f"Message scheduled during quiet hours ({hour}:00)",
                    "severity": "critical",
                }
            )

        # Check business days only
        if self.business_only_days:
            weekday = local_time.weekday()  # Monday=0, Sunday=6
            if weekday >= 5:  # Saturday=5, Sunday=6
                violations.append(
                    {
                        "type": "non_business_day",
                        "description": "Message scheduled for weekend",
                        "severity": "moderate",
                    }
                )

        return {"valid": len(violations) == 0, "violations": violations, "local_time": local_time}

    async def _validate_frequency(
        self, prospect: Prospect, scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Validate frequency compliance"""
        violations = []

        # Check minimum interval since last message
        if prospect.last_contacted:
            hours_since_last = (scheduled_time - prospect.last_contacted).total_seconds() / 3600
            if hours_since_last < self.min_message_interval_hours:
                violations.append(
                    {
                        "type": "frequency_violation",
                        "description": f"Only {hours_since_last:.1f} hours since last message",
                        "severity": "moderate",
                    }
                )

        # Check daily message limit
        # In production, would query actual message history
        today_message_count = 1  # Mock count
        if today_message_count >= self.max_daily_messages:
            violations.append(
                {
                    "type": "daily_limit_violation",
                    "description": f"Daily limit of {self.max_daily_messages} messages exceeded",
                    "severity": "high",
                }
            )

        return {"valid": len(violations) == 0, "violations": violations}

    async def _validate_message_content(self, message_content: str) -> Dict[str, Any]:
        """Validate message content for compliance"""
        warnings = []

        # Check for required opt-out instructions
        opt_out_indicators = ["stop", "unsubscribe", "opt-out", "opt out", "text stop"]
        has_opt_out = any(indicator in message_content.lower() for indicator in opt_out_indicators)

        if not has_opt_out:
            warnings.append(
                {
                    "type": "missing_opt_out",
                    "description": "Message should include opt-out instructions",
                    "severity": "moderate",
                }
            )

        # Check message length (SMS limit)
        if len(message_content) > 160:
            warnings.append(
                {
                    "type": "message_length",
                    "description": f"Message length ({len(message_content)}) exceeds standard SMS limit",
                    "severity": "low",
                }
            )

        # Check for prohibited content patterns
        prohibited_patterns = [r"100% guaranteed", r"act now", r"urgent.*offer", r"limited.*time"]

        for pattern in prohibited_patterns:
            if re.search(pattern, message_content, re.IGNORECASE):
                warnings.append(
                    {
                        "type": "potentially_misleading_content",
                        "description": f"Content contains potentially misleading language: {pattern}",
                        "severity": "moderate",
                    }
                )

        return {"valid": True, "warnings": warnings}  # Content warnings don't prevent sending

    async def _suggest_optimal_send_time(
        self, prospect: Prospect, original_time: datetime
    ) -> datetime:
        """Suggest optimal send time that complies with TCPA"""
        # Find next compliant time slot
        candidate_time = original_time

        # If in quiet hours, move to 8 AM next business day
        if (
            candidate_time.hour >= self.quiet_hours_start
            or candidate_time.hour < self.quiet_hours_end
        ):
            # Move to 8 AM
            candidate_time = candidate_time.replace(hour=8, minute=0, second=0, microsecond=0)

            # If that's still today and we were in early morning quiet hours, it's fine
            # If we were in evening quiet hours, move to next day
            if original_time.hour >= self.quiet_hours_start:
                candidate_time += timedelta(days=1)

        # If weekend, move to Monday
        while candidate_time.weekday() >= 5:  # Saturday=5, Sunday=6
            candidate_time += timedelta(days=1)

        # Ensure business hours (8 AM - 9 PM)
        if candidate_time.hour < self.quiet_hours_end:
            candidate_time = candidate_time.replace(hour=self.quiet_hours_end)
        elif candidate_time.hour >= self.quiet_hours_start:
            candidate_time = candidate_time.replace(hour=self.quiet_hours_start - 1)

        return candidate_time

    async def _log_compliance_check(
        self, prospect: Prospect, validation_result: Dict[str, Any]
    ) -> ComplianceRecord:
        """Log compliance check for audit trail"""
        compliance_record = ComplianceRecord(
            prospect_id=prospect.prospect_id,
            channel=CommunicationChannel.SMS,
            compliance_status=(
                ComplianceStatus.COMPLIANT
                if validation_result["compliant"]
                else ComplianceStatus.NON_COMPLIANT
            ),
            regulation_type="TCPA",
        )

        # Add violation details
        if validation_result["violations"]:
            violation_descriptions = [v["description"] for v in validation_result["violations"]]
            compliance_record.violation_description = "; ".join(violation_descriptions)
            compliance_record.violation_type = validation_result["violations"][0]["type"]

        self.compliance_violations.append(compliance_record)
        return compliance_record

    async def generate_compliance_report(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """Generate compliance report for audit"""
        end_date = end_date or datetime.now(timezone.utc)
        start_date = start_date or (end_date - timedelta(days=30))

        # Filter compliance records by date range
        period_records = [
            record
            for record in self.compliance_violations
            if start_date <= record.created_at <= end_date
        ]

        # Calculate statistics
        total_checks = len(period_records)
        compliant_checks = len(
            [r for r in period_records if r.compliance_status == ComplianceStatus.COMPLIANT]
        )
        violation_checks = len(
            [r for r in period_records if r.compliance_status == ComplianceStatus.NON_COMPLIANT]
        )

        # Violation breakdown
        violation_types = {}
        for record in period_records:
            if record.violation_type:
                violation_types[record.violation_type] = (
                    violation_types.get(record.violation_type, 0) + 1
                )

        report = {
            "reporting_period": {"start_date": start_date, "end_date": end_date},
            "summary_statistics": {
                "total_compliance_checks": total_checks,
                "compliant_checks": compliant_checks,
                "violation_checks": violation_checks,
                "compliance_rate": compliant_checks / total_checks if total_checks > 0 else 0.0,
            },
            "violation_breakdown": violation_types,
            "top_violations": sorted(violation_types.items(), key=lambda x: x[1], reverse=True)[:5],
            "recommendations": await self._generate_compliance_recommendations(period_records),
        }

        return report

    async def _generate_compliance_recommendations(
        self, compliance_records: List[ComplianceRecord]
    ) -> List[str]:
        """Generate compliance improvement recommendations"""
        recommendations = []

        # Analyze violation patterns
        violation_counts = {}
        for record in compliance_records:
            if record.violation_type:
                violation_counts[record.violation_type] = (
                    violation_counts.get(record.violation_type, 0) + 1
                )

        # Generate recommendations based on common violations
        if violation_counts.get("consent_violation", 0) > 5:
            recommendations.append("Implement double opt-in consent process for SMS")
            recommendations.append("Review and update consent collection procedures")

        if violation_counts.get("quiet_hours_violation", 0) > 3:
            recommendations.append("Implement automatic timezone-aware scheduling")
            recommendations.append("Add quiet hours validation to campaign setup")

        if violation_counts.get("frequency_violation", 0) > 3:
            recommendations.append("Implement frequency capping across all campaigns")
            recommendations.append("Add prospect-level message history tracking")

        return recommendations


class TwilioSMSManager:
    """
    Twilio SMS Manager with delivery tracking
    """

    def __init__(self, account_sid: str, auth_token: str, from_phone: str):
        self.client = TwilioClient(account_sid, auth_token)
        self.from_phone = from_phone
        self.delivery_callbacks: Dict[str, callable] = {}
        self.message_cache: Dict[str, Dict[str, Any]] = {}

    async def send_sms(
        self, to_phone: str, message: str, scheduled_time: datetime = None, callback_url: str = None
    ) -> Optional[OutreachMessage]:
        """Send SMS message via Twilio"""
        try:
            # Send message
            if scheduled_time and scheduled_time > datetime.now(timezone.utc):
                # Twilio doesn't support scheduled messages directly
                # Would need to implement queue/scheduler
                logger.info(f"Message scheduled for {scheduled_time}, queuing for later delivery")
                return await self._queue_scheduled_message(to_phone, message, scheduled_time)

            # Send immediately
            twilio_message = self.client.messages.create(
                to=to_phone, from_=self.from_phone, body=message, status_callback=callback_url
            )

            # Create outreach message record
            outreach_message = OutreachMessage(
                channel=CommunicationChannel.SMS,
                content=message,
                recipient_phone=to_phone,
                platform_message_id=twilio_message.sid,
                status=DeliveryStatus.SENT,
                sent_time=datetime.now(timezone.utc),
                tcpa_compliant=True,  # Assuming pre-validated
                consent_verified=True,
            )

            # Cache for status tracking
            self.message_cache[twilio_message.sid] = {
                "outreach_message": outreach_message,
                "twilio_message": twilio_message,
            }

            logger.info(f"SMS sent successfully to {to_phone}, SID: {twilio_message.sid}")
            return outreach_message

        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {e}")

            # Create failed message record
            outreach_message = OutreachMessage(
                channel=CommunicationChannel.SMS,
                content=message,
                recipient_phone=to_phone,
                status=DeliveryStatus.FAILED,
                error_message=str(e),
            )

            return outreach_message

        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_phone}: {e}")
            return None

    async def get_message_status(self, platform_message_id: str) -> Dict[str, Any]:
        """Get message delivery status from Twilio"""
        try:
            twilio_message = self.client.messages(platform_message_id).fetch()

            # Map Twilio status to our status
            status_mapping = {
                "queued": DeliveryStatus.QUEUED,
                "sent": DeliveryStatus.SENT,
                "delivered": DeliveryStatus.DELIVERED,
                "undelivered": DeliveryStatus.FAILED,
                "failed": DeliveryStatus.FAILED,
            }

            our_status = status_mapping.get(twilio_message.status, DeliveryStatus.SENT)

            # Update cached message if exists
            if platform_message_id in self.message_cache:
                cached_message = self.message_cache[platform_message_id]["outreach_message"]
                cached_message.update_status(our_status)

            return {
                "platform_message_id": platform_message_id,
                "status": our_status.value,
                "twilio_status": twilio_message.status,
                "price": twilio_message.price,
                "error_code": twilio_message.error_code,
                "error_message": twilio_message.error_message,
                "date_sent": twilio_message.date_sent,
                "date_updated": twilio_message.date_updated,
            }

        except Exception as e:
            logger.error(f"Error fetching message status {platform_message_id}: {e}")
            return {"error": str(e)}

    async def handle_delivery_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery status webhook from Twilio"""
        try:
            message_sid = webhook_data.get("MessageSid")
            message_status = webhook_data.get("MessageStatus")

            if not message_sid:
                return {"error": "Missing MessageSid"}

            # Update message status
            status_result = await self.get_message_status(message_sid)

            # Call registered callbacks
            if message_sid in self.delivery_callbacks:
                callback = self.delivery_callbacks[message_sid]
                await callback(status_result)

            return {"processed": True, "message_sid": message_sid, "status": message_status}

        except Exception as e:
            logger.error(f"Error handling delivery webhook: {e}")
            return {"error": str(e)}

    async def _queue_scheduled_message(
        self, to_phone: str, message: str, scheduled_time: datetime
    ) -> OutreachMessage:
        """Queue message for scheduled delivery"""
        # In production, would use actual message queue (Redis, etc.)
        outreach_message = OutreachMessage(
            channel=CommunicationChannel.SMS,
            content=message,
            recipient_phone=to_phone,
            status=DeliveryStatus.QUEUED,
            scheduled_send_time=scheduled_time,
        )

        logger.info(f"Queued SMS for {to_phone} at {scheduled_time}")
        return outreach_message

    def register_delivery_callback(self, message_sid: str, callback: callable):
        """Register callback for message delivery updates"""
        self.delivery_callbacks[message_sid] = callback


class SMSCampaignOrchestrator:
    """
    SMS Campaign Orchestrator with TCPA compliance
    """

    def __init__(self, twilio_manager: TwilioSMSManager, compliance_engine: TCPAComplianceEngine):
        self.twilio_manager = twilio_manager
        self.compliance_engine = compliance_engine
        self.active_campaigns: Dict[str, Dict[str, Any]] = {}
        self.campaign_metrics: Dict[str, Dict[str, Any]] = {}

    async def launch_sms_campaign(
        self,
        campaign_id: str,
        prospects: List[Prospect],
        message_template: str,
        campaign_config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Launch SMS campaign with compliance validation"""
        config = campaign_config or {}

        launch_result = {
            "campaign_id": campaign_id,
            "prospects_targeted": len(prospects),
            "messages_queued": 0,
            "messages_blocked": 0,
            "compliance_violations": 0,
            "scheduled_messages": [],
            "blocked_messages": [],
        }

        # Process each prospect
        for prospect in prospects:
            try:
                # Personalize message
                personalized_message = await self._personalize_message(message_template, prospect)

                # Validate compliance
                compliance_result = await self.compliance_engine.validate_sms_outreach(
                    prospect, personalized_message
                )

                if compliance_result["compliant"]:
                    # Schedule message
                    outreach_message = await self.twilio_manager.send_sms(
                        prospect.phone,
                        personalized_message,
                        compliance_result["approved_send_time"],
                    )

                    if outreach_message:
                        launch_result["messages_queued"] += 1
                        launch_result["scheduled_messages"].append(
                            {
                                "prospect_id": prospect.prospect_id,
                                "message_id": outreach_message.message_id,
                                "scheduled_time": compliance_result["approved_send_time"],
                            }
                        )
                else:
                    # Block non-compliant message
                    launch_result["messages_blocked"] += 1
                    launch_result["compliance_violations"] += 1
                    launch_result["blocked_messages"].append(
                        {
                            "prospect_id": prospect.prospect_id,
                            "violations": compliance_result["violations"],
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing prospect {prospect.prospect_id}: {e}")
                launch_result["messages_blocked"] += 1

        # Store campaign tracking
        self.active_campaigns[campaign_id] = {
            "config": config,
            "launched_at": datetime.now(timezone.utc),
            "launch_result": launch_result,
        }

        logger.info(
            f"SMS campaign {campaign_id} launched: "
            f"{launch_result['messages_queued']} queued, "
            f"{launch_result['messages_blocked']} blocked"
        )

        return launch_result

    async def _personalize_message(self, template: str, prospect: Prospect) -> str:
        """Personalize message template with prospect data"""
        personalized = template

        # Replace common placeholders
        replacements = {
            "{first_name}": prospect.first_name,
            "{last_name}": prospect.last_name,
            "{company}": prospect.company,
            "{job_title}": prospect.job_title,
        }

        for placeholder, value in replacements.items():
            personalized = personalized.replace(placeholder, value)

        # Add opt-out instructions if not present
        if "stop" not in personalized.lower():
            personalized += "\n\nReply STOP to unsubscribe."

        return personalized

    async def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign performance metrics"""
        if campaign_id not in self.active_campaigns:
            return {"error": "Campaign not found"}

        campaign = self.active_campaigns[campaign_id]
        launch_result = campaign["launch_result"]

        # Calculate performance metrics
        # In production, would query actual message delivery status
        performance = {
            "campaign_id": campaign_id,
            "launched_at": campaign["launched_at"],
            "messages_sent": launch_result["messages_queued"],
            "messages_blocked": launch_result["messages_blocked"],
            "compliance_rate": (
                (
                    launch_result["messages_queued"]
                    / (launch_result["messages_queued"] + launch_result["messages_blocked"])
                )
                if (launch_result["messages_queued"] + launch_result["messages_blocked"]) > 0
                else 0.0
            ),
            "estimated_delivery_rate": 0.95,  # Mock metric
            "estimated_response_rate": 0.12,  # Mock metric
        }

        return performance

    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause active SMS campaign"""
        if campaign_id not in self.active_campaigns:
            return False

        # In production, would cancel queued messages
        self.active_campaigns[campaign_id]["paused_at"] = datetime.now(timezone.utc)
        logger.info(f"SMS campaign {campaign_id} paused")
        return True

    async def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary across all campaigns"""
        return await self.compliance_engine.generate_compliance_report()
