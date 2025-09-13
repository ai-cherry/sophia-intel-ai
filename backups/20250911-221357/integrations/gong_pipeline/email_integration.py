"""
Comprehensive Gong Email Integration
Handles email data extraction, processing, and pipeline integration with proper threading and context
"""
import asyncio
import hashlib
import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
logger = logging.getLogger(__name__)
class EmailDirection(str, Enum):
    """Email direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"
class EmailPriority(str, Enum):
    """Email priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
class EmailProcessingStatus(str, Enum):
    """Email processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
@dataclass
class EmailParticipant:
    """Email participant information"""
    email: str
    name: str
    role: str = "participant"  # sender, recipient, cc, bcc
    is_internal: bool = True
    department: Optional[str] = None
@dataclass
class EmailThread:
    """Email thread information"""
    thread_id: str
    subject: str
    participant_count: int
    email_count: int
    first_email_date: datetime
    last_email_date: datetime
    is_active: bool = True
    # Related business context
    related_deals: list[str] = None
    related_contacts: list[str] = None
    related_calls: list[str] = None
    def __post_init__(self):
        if self.related_deals is None:
            self.related_deals = []
        if self.related_contacts is None:
            self.related_contacts = []
        if self.related_calls is None:
            self.related_calls = []
@dataclass
class ProcessedEmail:
    """Processed email with enhanced metadata"""
    # Basic email properties
    email_id: str
    thread_id: str
    subject: str
    body_html: str
    body_plain: str
    # Participants
    from_participant: EmailParticipant
    to_participants: list[EmailParticipant]
    cc_participants: list[EmailParticipant]
    bcc_participants: list[EmailParticipant]
    # Metadata
    direction: EmailDirection
    priority: EmailPriority
    sent_at: datetime
    received_at: datetime
    # Content analysis
    topics: list[str]
    keywords: list[str]
    entities: list[str]
    sentiment_score: Optional[float]
    urgency_score: Optional[float]
    # Attachments
    has_attachments: bool
    attachment_names: list[str]
    attachment_types: list[str]
    # Business context
    deal_id: Optional[str] = None
    account_id: Optional[str] = None
    contact_ids: list[str] = None
    opportunity_stage: Optional[str] = None
    # Email chain context
    is_reply: bool = False
    is_forward: bool = False
    reply_to_id: Optional[str] = None
    forwarded_from_id: Optional[str] = None
    # Processing metadata
    processing_status: EmailProcessingStatus = EmailProcessingStatus.PENDING
    processed_at: Optional[datetime] = None
    def __post_init__(self):
        if self.topics is None:
            self.topics = []
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []
        if self.attachment_names is None:
            self.attachment_names = []
        if self.attachment_types is None:
            self.attachment_types = []
        if self.contact_ids is None:
            self.contact_ids = []
class GongEmailExtractor:
    """Extracts email data from Gong API"""
    def __init__(self, gong_config: dict[str, str]):
        self.api_url = gong_config.get("api_url", "https://api.gong.io")
        self.access_key = gong_config["access_key"]
        self.client_secret = gong_config["client_secret"]
        # Email domain mapping for internal/external classification
        self.internal_domains = set()
        self.department_mapping = {}
    def set_internal_domains(self, domains: list[str]):
        """Set internal email domains for classification"""
        self.internal_domains = {domain.lower() for domain in domains}
    def set_department_mapping(self, mapping: dict[str, str]):
        """Set email to department mapping"""
        self.department_mapping = {
            email.lower(): dept for email, dept in mapping.items()
        }
    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers"""
        import base64
        auth_string = base64.b64encode(
            f"{self.access_key}:{self.client_secret}".encode()
        ).decode()
        return {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
        }
    async def extract_emails(
        self, start_date: datetime = None, end_date: datetime = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Extract emails from Gong API"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        headers = await self.get_auth_headers()
        params = {
            "fromDateTime": start_date.isoformat(),
            "toDateTime": end_date.isoformat(),
            "limit": limit,
        }
        try:
            import aiohttp
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.api_url}/v2/emails", headers=headers, params=params
                ) as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    emails = data.get("emails", [])
                    logger.info(f"Extracted {len(emails)} emails from Gong")
                    return emails
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to extract emails: {response.status} - {error_text}"
                    )
                    return []
        except Exception as e:
            logger.error(f"Error extracting emails from Gong: {e}")
            return []
    async def get_email_details(self, email_id: str) -> Optional[dict[str, Any]]:
        """Get detailed email information"""
        headers = await self.get_auth_headers()
        try:
            import aiohttp
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.api_url}/v2/emails/{email_id}", headers=headers
                ) as response,
            ):
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get email details: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return None
class EmailProcessor:
    """Processes and enriches email data"""
    def __init__(
        self,
        internal_domains: list[str] = None,
        department_mapping: dict[str, str] = None,
    ):
        self.internal_domains = set(internal_domains or [])
        self.department_mapping = department_mapping or {}
        # Email parsing patterns
        self.reply_patterns = [
            re.compile(r"^(re|RE):\s*", re.IGNORECASE),
            re.compile(r"^\s*>.*$", re.MULTILINE),  # Quoted text
        ]
        self.forward_patterns = [
            re.compile(r"^(fwd|FWD|fw|FW):\s*", re.IGNORECASE),
            re.compile(r"---------- Forwarded message ----------", re.IGNORECASE),
        ]
        # Content analysis patterns
        self.urgency_keywords = [
            "urgent",
            "asap",
            "immediately",
            "critical",
            "emergency",
            "high priority",
            "time sensitive",
            "deadline",
            "rush",
            "important",
        ]
        self.action_keywords = [
            "action required",
            "please review",
            "need approval",
            "follow up",
            "schedule",
            "meeting",
            "call",
            "discuss",
            "decision",
            "next steps",
        ]
    def _is_internal_email(self, email: str) -> bool:
        """Check if email address is internal"""
        if not email or "@" not in email:
            return False
        domain = email.split("@")[1].lower()
        return domain in self.internal_domains
    def _get_department(self, email: str) -> Optional[str]:
        """Get department for email address"""
        return self.department_mapping.get(email.lower())
    def _create_participant(
        self, email_addr: str, name: str = "", role: str = "participant"
    ) -> EmailParticipant:
        """Create email participant object"""
        if not name:
            name = email_addr.split("@")[0].replace(".", " ").title()
        return EmailParticipant(
            email=email_addr,
            name=name,
            role=role,
            is_internal=self._is_internal_email(email_addr),
            department=self._get_department(email_addr),
        )
    def _extract_plain_text(self, html_content: str) -> str:
        """Extract plain text from HTML email"""
        if not html_content:
            return ""
        try:
            # Remove HTML tags
            text = re.sub(r"<[^>]+>", "", html_content)
            # Decode HTML entities
            text = html.unescape(text)
            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception as e:
            logger.error(f"Error extracting plain text: {e}")
            return html_content
    def _analyze_content(
        self, content: str
    ) -> tuple[list[str], list[str], list[str], float, float]:
        """Analyze email content for topics, keywords, entities, sentiment, urgency"""
        content_lower = content.lower()
        # Extract keywords (simplified)
        words = re.findall(r"\b\w+\b", content_lower)
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "cannot",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
            "this",
            "that",
            "these",
            "those",
            "a",
            "an",
        }
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        # Get most frequent keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        top_keywords = [word for word, count in keyword_counts.most_common(10)]
        # Extract topics (simplified)
        topics = []
        topic_patterns = {
            "sales": [
                "deal",
                "price",
                "contract",
                "proposal",
                "quote",
                "revenue",
                "purchase",
                "sales",
            ],
            "support": [
                "issue",
                "problem",
                "bug",
                "error",
                "help",
                "support",
                "troubleshoot",
            ],
            "meeting": [
                "meeting",
                "call",
                "schedule",
                "agenda",
                "discuss",
                "zoom",
                "teams",
            ],
            "product": ["product", "feature", "demo", "functionality", "requirements"],
            "legal": [
                "contract",
                "agreement",
                "terms",
                "legal",
                "compliance",
                "privacy",
            ],
            "finance": ["invoice", "payment", "budget", "cost", "expense", "billing"],
        }
        for topic, patterns in topic_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                topics.append(topic)
        # Extract entities (simplified)
        entities = []
        # Email addresses
        email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        entities.extend(email_pattern.findall(content))
        # Phone numbers
        phone_pattern = re.compile(
            r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
        )
        entities.extend(phone_pattern.findall(content))
        # URLs
        url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        entities.extend(url_pattern.findall(content))
        # Calculate urgency score
        urgency_score = 0.0
        urgency_indicators = 0
        for keyword in self.urgency_keywords:
            if keyword in content_lower:
                urgency_indicators += content_lower.count(keyword)
        urgency_score = min(urgency_indicators * 0.2, 1.0)  # Scale to 0-1
        # Calculate sentiment score (simplified)
        positive_words = [
            "great",
            "excellent",
            "good",
            "happy",
            "pleased",
            "satisfied",
            "wonderful",
            "fantastic",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "disappointed",
            "angry",
            "frustrated",
            "problem",
            "issue",
        ]
        positive_count = sum(content_lower.count(word) for word in positive_words)
        negative_count = sum(content_lower.count(word) for word in negative_words)
        if positive_count + negative_count > 0:
            sentiment_score = (positive_count - negative_count) / (
                positive_count + negative_count
            )
        else:
            sentiment_score = 0.0
        return topics, top_keywords, list(set(entities)), sentiment_score, urgency_score
    def _detect_email_type(
        self, subject: str, content: str
    ) -> tuple[bool, bool, EmailDirection]:
        """Detect if email is reply, forward, and determine direction"""
        is_reply = any(pattern.search(subject) for pattern in self.reply_patterns)
        is_forward = any(pattern.search(subject) for pattern in self.forward_patterns)
        # Direction detection would need more context (internal domains, sender/recipient analysis)
        # For now, simplified logic
        direction = EmailDirection.OUTBOUND  # Default
        return is_reply, is_forward, direction
    def _extract_thread_id(self, email_data: dict[str, Any]) -> str:
        """Extract or generate thread ID"""
        # Gong might provide thread ID directly
        if "thread_id" in email_data:
            return email_data["thread_id"]
        # Generate from subject (simplified)
        subject = email_data.get("subject", "")
        # Remove re: fw: etc. and use cleaned subject as thread ID
        cleaned_subject = re.sub(
            r"^(re|fw|fwd):\s*", "", subject, flags=re.IGNORECASE
        ).strip()
        # Generate hash from cleaned subject
        return hashlib.md5(cleaned_subject.encode()).hexdigest()[:16]
    async def process_email(self, raw_email: dict[str, Any]) -> ProcessedEmail:
        """Process raw email data into structured format"""
        try:
            # Extract basic information
            email_id = raw_email.get("id", "")
            subject = raw_email.get("subject", "")
            body_html = raw_email.get("body_html", "")
            body_plain = raw_email.get("body_plain", "") or self._extract_plain_text(
                body_html
            )
            # Parse participants
            from_email_data = raw_email.get("from", {})
            from_participant = self._create_participant(
                from_email_data.get("email", ""),
                from_email_data.get("name", ""),
                "sender",
            )
            to_participants = [
                self._create_participant(
                    p.get("email", ""), p.get("name", ""), "recipient"
                )
                for p in raw_email.get("to", [])
            ]
            cc_participants = [
                self._create_participant(p.get("email", ""), p.get("name", ""), "cc")
                for p in raw_email.get("cc", [])
            ]
            bcc_participants = [
                self._create_participant(p.get("email", ""), p.get("name", ""), "bcc")
                for p in raw_email.get("bcc", [])
            ]
            # Parse timestamps
            sent_at = raw_email.get("sent_at")
            if isinstance(sent_at, str):
                sent_at = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
            elif sent_at is None:
                sent_at = datetime.now()
            received_at = raw_email.get("received_at", sent_at)
            if isinstance(received_at, str):
                received_at = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
            # Analyze content
            full_content = f"{subject} {body_plain}"
            topics, keywords, entities, sentiment_score, urgency_score = (
                self._analyze_content(full_content)
            )
            # Detect email characteristics
            is_reply, is_forward, direction = self._detect_email_type(
                subject, body_plain
            )
            # Extract thread ID
            thread_id = self._extract_thread_id(raw_email)
            # Process attachments
            attachments = raw_email.get("attachments", [])
            has_attachments = len(attachments) > 0
            attachment_names = [att.get("name", "") for att in attachments]
            attachment_types = [att.get("type", "") for att in attachments]
            # Determine priority (simplified)
            priority = (
                EmailPriority.HIGH if urgency_score > 0.7 else EmailPriority.NORMAL
            )
            return ProcessedEmail(
                email_id=email_id,
                thread_id=thread_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                from_participant=from_participant,
                to_participants=to_participants,
                cc_participants=cc_participants,
                bcc_participants=bcc_participants,
                direction=direction,
                priority=priority,
                sent_at=sent_at,
                received_at=received_at,
                topics=topics,
                keywords=keywords,
                entities=entities,
                sentiment_score=sentiment_score,
                urgency_score=urgency_score,
                has_attachments=has_attachments,
                attachment_names=attachment_names,
                attachment_types=attachment_types,
                deal_id=raw_email.get("deal_id"),
                account_id=raw_email.get("account_id"),
                contact_ids=raw_email.get("contact_ids", []),
                opportunity_stage=raw_email.get("opportunity_stage"),
                is_reply=is_reply,
                is_forward=is_forward,
                processing_status=EmailProcessingStatus.COMPLETED,
                processed_at=datetime.now(),
            )
        except Exception as e:
            logger.error(
                f"Error processing email {raw_email.get('id', 'unknown')}: {e}"
            )
            raise
class EmailThreadAnalyzer:
    """Analyzes email threads and relationships"""
    def __init__(self):
        pass
    async def analyze_threads(
        self, processed_emails: list[ProcessedEmail]
    ) -> list[EmailThread]:
        """Analyze email threads from processed emails"""
        threads = {}
        for email in processed_emails:
            thread_id = email.thread_id
            if thread_id not in threads:
                # Create new thread
                threads[thread_id] = {
                    "thread_id": thread_id,
                    "subject": email.subject,
                    "emails": [],
                    "participants": set(),
                    "first_date": email.sent_at,
                    "last_date": email.sent_at,
                    "related_deals": set(),
                    "related_contacts": set(),
                    "related_calls": set(),
                }
            thread = threads[thread_id]
            thread["emails"].append(email)
            # Add participants
            thread["participants"].add(email.from_participant.email)
            thread["participants"].update(p.email for p in email.to_participants)
            thread["participants"].update(p.email for p in email.cc_participants)
            # Update date range
            if email.sent_at < thread["first_date"]:
                thread["first_date"] = email.sent_at
            if email.sent_at > thread["last_date"]:
                thread["last_date"] = email.sent_at
            # Collect business context
            if email.deal_id:
                thread["related_deals"].add(email.deal_id)
            if email.contact_ids:
                thread["related_contacts"].update(email.contact_ids)
        # Convert to EmailThread objects
        email_threads = []
        for thread_data in threads.values():
            email_thread = EmailThread(
                thread_id=thread_data["thread_id"],
                subject=thread_data["subject"],
                participant_count=len(thread_data["participants"]),
                email_count=len(thread_data["emails"]),
                first_email_date=thread_data["first_date"],
                last_email_date=thread_data["last_date"],
                is_active=thread_data["last_date"]
                > datetime.now() - timedelta(days=30),
                related_deals=list(thread_data["related_deals"]),
                related_contacts=list(thread_data["related_contacts"]),
                related_calls=list(thread_data["related_calls"]),
            )
            email_threads.append(email_thread)
        logger.info(
            f"Analyzed {len(email_threads)} email threads from {len(processed_emails)} emails"
        )
        return email_threads
class GongEmailPipeline:
    """Complete pipeline for Gong email processing"""
    def __init__(
        self,
        gong_config: dict[str, str],
        internal_domains: list[str] = None,
        department_mapping: dict[str, str] = None,
    ):
        self.extractor = GongEmailExtractor(gong_config)
        self.processor = EmailProcessor(internal_domains, department_mapping)
        self.thread_analyzer = EmailThreadAnalyzer()
        if internal_domains:
            self.extractor.set_internal_domains(internal_domains)
        if department_mapping:
            self.extractor.set_department_mapping(department_mapping)
    async def run_full_pipeline(
        self, start_date: datetime = None, end_date: datetime = None, limit: int = 100
    ) -> tuple[list[ProcessedEmail], list[EmailThread]]:
        """Run complete email processing pipeline"""
        logger.info("Starting Gong email processing pipeline")
        # Extract emails
        logger.info("Extracting emails from Gong...")
        raw_emails = await self.extractor.extract_emails(start_date, end_date, limit)
        if not raw_emails:
            logger.warning("No emails extracted")
            return [], []
        # Process emails
        logger.info(f"Processing {len(raw_emails)} emails...")
        processed_emails = []
        for raw_email in raw_emails:
            try:
                processed_email = await self.processor.process_email(raw_email)
                processed_emails.append(processed_email)
            except Exception as e:
                logger.error(
                    f"Failed to process email {raw_email.get('id', 'unknown')}: {e}"
                )
                continue
        logger.info(f"Successfully processed {len(processed_emails)} emails")
        # Analyze threads
        logger.info("Analyzing email threads...")
        email_threads = await self.thread_analyzer.analyze_threads(processed_emails)
        logger.info(
            f"Pipeline completed: {len(processed_emails)} emails, {len(email_threads)} threads"
        )
        return processed_emails, email_threads
    def prepare_for_weaviate(
        self, processed_emails: list[ProcessedEmail]
    ) -> list[dict[str, Any]]:
        """Prepare processed emails for Weaviate ingestion"""
        weaviate_objects = []
        for email in processed_emails:
            # Convert to Weaviate-compatible format using schema
            from app.integrations.gong_pipeline.schemas import create_email_object
            email_data = {
                "id": email.email_id,
                "subject": email.subject,
                "body_html": email.body_html,
                "body_plain": email.body_plain,
                "from_email": email.from_participant.email,
                "from_name": email.from_participant.name,
                "to_emails": [p.email for p in email.to_participants],
                "cc_emails": [p.email for p in email.cc_participants],
                "bcc_emails": [p.email for p in email.bcc_participants],
                "email_type": email.direction.value,
                "thread_id": email.thread_id,
                "is_reply": email.is_reply,
                "is_forward": email.is_forward,
                "priority": email.priority.value,
                "has_attachments": email.has_attachments,
                "attachment_names": email.attachment_names,
                "sent_at": email.sent_at,
                "received_at": email.received_at,
                "deal_id": email.deal_id,
                "opportunity_stage": email.opportunity_stage,
                "contact_ids": email.contact_ids,
                "account_id": email.account_id,
                "sentiment": (
                    "positive"
                    if email.sentiment_score > 0.1
                    else "negative" if email.sentiment_score < -0.1 else "neutral"
                ),
                "sentiment_score": email.sentiment_score,
                "urgency_score": email.urgency_score,
                "topics": email.topics,
                "keywords": email.keywords,
                "entities": email.entities,
                "is_internal": email.from_participant.is_internal,
                "department_from": email.from_participant.department,
                "departments_to": [
                    p.department for p in email.to_participants if p.department
                ],
            }
            weaviate_obj = create_email_object(email_data)
            weaviate_objects.append(weaviate_obj)
        return weaviate_objects
# Example usage and testing
async def main():
    """Example usage of Gong email integration"""
    # Configuration
    gong_config = {
        "access_key": "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N",
        "client_secret": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU",
        "api_url": "https://api.gong.io",
    }
    internal_domains = ["payready.com", "company.com"]
    department_mapping = {
        "john@payready.com": "Sales",
        "jane@payready.com": "Marketing",
        "support@payready.com": "Support",
    }
    # Create pipeline
    pipeline = GongEmailPipeline(
        gong_config=gong_config,
        internal_domains=internal_domains,
        department_mapping=department_mapping,
    )
    try:
        # Run pipeline
        processed_emails, email_threads = await pipeline.run_full_pipeline(
            start_date=datetime.now() - timedelta(days=7), limit=50
        )
        logger.info("Pipeline results:")
        logger.info(f"- Processed emails: {len(processed_emails)}")
        logger.info(f"- Email threads: {len(email_threads)}")
        # Prepare for Weaviate
        weaviate_objects = pipeline.prepare_for_weaviate(processed_emails)
        logger.info(f"- Prepared {len(weaviate_objects)} objects for Weaviate")
        # Show sample results
        if processed_emails:
            sample_email = processed_emails[0]
            logger.info(
                f"Sample email: {sample_email.subject} from {sample_email.from_participant.email}"
            )
            logger.info(f"Topics: {sample_email.topics}")
            logger.info(f"Sentiment: {sample_email.sentiment_score:.2f}")
    except Exception as e:
        logger.error(f"Email pipeline failed: {e}")
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
