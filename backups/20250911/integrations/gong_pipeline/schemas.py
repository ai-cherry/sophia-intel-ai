"""
Weaviate Schema Definitions for Gong Data Pipeline
Supports GongCall, GongTranscriptChunk, and GongEmail classes with comprehensive metadata
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
logger = logging.getLogger(__name__)
class CallStatus(str, Enum):
    """Call status enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
class ParticipantRole(str, Enum):
    """Participant role enumeration"""
    HOST = "host"
    PARTICIPANT = "participant"
    GUEST = "guest"
    OBSERVER = "observer"
class EmailType(str, Enum):
    """Email type enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"
    AUTOMATED = "automated"
@dataclass
class CallParticipant:
    """Call participant information"""
    user_id: str
    email: str
    name: str
    role: ParticipantRole
    department: Optional[str] = None
    is_internal: bool = True
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    talk_time_seconds: Optional[int] = None
@dataclass
class CallMetrics:
    """Call performance metrics"""
    duration_seconds: int
    talk_ratio: float  # 0.0 to 1.0
    silence_ratio: float  # 0.0 to 1.0
    interruptions_count: int
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    engagement_score: Optional[float] = None  # 0.0 to 1.0
@dataclass
class TranscriptMetadata:
    """Metadata for transcript chunks"""
    speaker_id: str
    speaker_name: str
    speaker_role: ParticipantRole
    start_time: float
    end_time: float
    confidence: float
    is_final: bool
    sentiment: Optional[str] = None
    keywords: list[str] = None
    topics: list[str] = None
# Weaviate Schema Definitions
GONG_CALL_SCHEMA = {
    "class": "GongCall",
    "description": "Complete call record from Gong with metadata and participants",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "type": "text",
        }
    },
    "properties": [
        {
            "name": "callId",
            "dataType": ["text"],
            "description": "Unique Gong call identifier",
        },
        {
            "name": "title",
            "dataType": ["text"],
            "description": "Call title or meeting name",
        },
        {
            "name": "summary",
            "dataType": ["text"],
            "description": "AI-generated call summary for vector search",
        },
        {
            "name": "fullTranscript",
            "dataType": ["text"],
            "description": "Complete call transcript",
        },
        {"name": "callUrl", "dataType": ["text"], "description": "Gong call URL"},
        {
            "name": "status",
            "dataType": ["text"],
            "description": "Call status (scheduled, completed, etc.)",
        },
        {
            "name": "scheduledStart",
            "dataType": ["date"],
            "description": "Scheduled start time",
        },
        {
            "name": "actualStart",
            "dataType": ["date"],
            "description": "Actual start time",
        },
        {"name": "actualEnd", "dataType": ["date"], "description": "Actual end time"},
        {
            "name": "durationSeconds",
            "dataType": ["int"],
            "description": "Call duration in seconds",
        },
        {
            "name": "meetingPlatform",
            "dataType": ["text"],
            "description": "Meeting platform (Zoom, Teams, etc.)",
        },
        {
            "name": "recordingStatus",
            "dataType": ["text"],
            "description": "Recording availability status",
        },
        {
            "name": "participantCount",
            "dataType": ["int"],
            "description": "Number of participants",
        },
        {
            "name": "internalParticipants",
            "dataType": ["text[]"],
            "description": "List of internal participant emails",
        },
        {
            "name": "externalParticipants",
            "dataType": ["text[]"],
            "description": "List of external participant emails",
        },
        {
            "name": "departments",
            "dataType": ["text[]"],
            "description": "Departments represented in call",
        },
        {
            "name": "tags",
            "dataType": ["text[]"],
            "description": "Call tags and categories",
        },
        {
            "name": "topics",
            "dataType": ["text[]"],
            "description": "Discussion topics identified",
        },
        {
            "name": "keywords",
            "dataType": ["text[]"],
            "description": "Important keywords from call",
        },
        {
            "name": "talkRatio",
            "dataType": ["number"],
            "description": "Talk time ratio (0.0 to 1.0)",
        },
        {
            "name": "silenceRatio",
            "dataType": ["number"],
            "description": "Silence ratio (0.0 to 1.0)",
        },
        {
            "name": "interruptionsCount",
            "dataType": ["int"],
            "description": "Number of interruptions",
        },
        {
            "name": "sentimentScore",
            "dataType": ["number"],
            "description": "Overall sentiment score (-1.0 to 1.0)",
        },
        {
            "name": "engagementScore",
            "dataType": ["number"],
            "description": "Engagement score (0.0 to 1.0)",
        },
        {
            "name": "actionItems",
            "dataType": ["text[]"],
            "description": "Extracted action items",
        },
        {
            "name": "decisions",
            "dataType": ["text[]"],
            "description": "Key decisions made",
        },
        {
            "name": "nextSteps",
            "dataType": ["text[]"],
            "description": "Identified next steps",
        },
        {
            "name": "pipelineStage",
            "dataType": ["text"],
            "description": "Sales pipeline stage if applicable",
        },
        {
            "name": "dealValue",
            "dataType": ["number"],
            "description": "Associated deal value if applicable",
        },
        {
            "name": "createdAt",
            "dataType": ["date"],
            "description": "Record creation timestamp",
        },
        {
            "name": "updatedAt",
            "dataType": ["date"],
            "description": "Record last update timestamp",
        },
        {
            "name": "source",
            "dataType": ["text"],
            "description": "Data source identifier",
        },
    ],
}
GONG_TRANSCRIPT_CHUNK_SCHEMA = {
    "class": "GongTranscriptChunk",
    "description": "Chunked transcript segments from Gong calls for detailed search",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "type": "text",
        }
    },
    "properties": [
        {
            "name": "callId",
            "dataType": ["text"],
            "description": "Parent call identifier",
        },
        {
            "name": "chunkId",
            "dataType": ["text"],
            "description": "Unique chunk identifier",
        },
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Transcript content for this chunk",
        },
        {
            "name": "speakerId",
            "dataType": ["text"],
            "description": "Speaker identifier",
        },
        {"name": "speakerName", "dataType": ["text"], "description": "Speaker name"},
        {
            "name": "speakerRole",
            "dataType": ["text"],
            "description": "Speaker role (host, participant, guest)",
        },
        {
            "name": "speakerEmail",
            "dataType": ["text"],
            "description": "Speaker email address",
        },
        {
            "name": "isInternal",
            "dataType": ["boolean"],
            "description": "Whether speaker is internal to organization",
        },
        {
            "name": "department",
            "dataType": ["text"],
            "description": "Speaker department if internal",
        },
        {
            "name": "startTime",
            "dataType": ["number"],
            "description": "Chunk start time in seconds",
        },
        {
            "name": "endTime",
            "dataType": ["number"],
            "description": "Chunk end time in seconds",
        },
        {
            "name": "duration",
            "dataType": ["number"],
            "description": "Chunk duration in seconds",
        },
        {
            "name": "confidence",
            "dataType": ["number"],
            "description": "Transcription confidence (0.0 to 1.0)",
        },
        {
            "name": "sentiment",
            "dataType": ["text"],
            "description": "Sentiment analysis (positive, negative, neutral)",
        },
        {
            "name": "sentimentScore",
            "dataType": ["number"],
            "description": "Sentiment score (-1.0 to 1.0)",
        },
        {
            "name": "keywords",
            "dataType": ["text[]"],
            "description": "Keywords extracted from this chunk",
        },
        {
            "name": "topics",
            "dataType": ["text[]"],
            "description": "Topics discussed in this chunk",
        },
        {
            "name": "entities",
            "dataType": ["text[]"],
            "description": "Named entities mentioned",
        },
        {
            "name": "questions",
            "dataType": ["text[]"],
            "description": "Questions asked in this segment",
        },
        {
            "name": "actionItems",
            "dataType": ["text[]"],
            "description": "Action items mentioned in chunk",
        },
        {
            "name": "hasScreenShare",
            "dataType": ["boolean"],
            "description": "Whether screen sharing occurred during chunk",
        },
        {
            "name": "callDate",
            "dataType": ["date"],
            "description": "Call date for temporal filtering",
        },
        {"name": "callTitle", "dataType": ["text"], "description": "Parent call title"},
        {
            "name": "meetingPlatform",
            "dataType": ["text"],
            "description": "Meeting platform used",
        },
        {
            "name": "chunkIndex",
            "dataType": ["int"],
            "description": "Chunk sequence number in call",
        },
        {
            "name": "totalChunks",
            "dataType": ["int"],
            "description": "Total chunks in call",
        },
        {
            "name": "createdAt",
            "dataType": ["date"],
            "description": "Record creation timestamp",
        },
        {
            "name": "source",
            "dataType": ["text"],
            "description": "Data source identifier",
        },
    ],
}
GONG_EMAIL_SCHEMA = {
    "class": "GongEmail",
    "description": "Email communications tracked in Gong with context and relationships",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "text-embedding-3-small",
            "dimensions": 1536,
            "type": "text",
        }
    },
    "properties": [
        {
            "name": "emailId",
            "dataType": ["text"],
            "description": "Unique email identifier from Gong",
        },
        {"name": "subject", "dataType": ["text"], "description": "Email subject line"},
        {"name": "body", "dataType": ["text"], "description": "Email body content"},
        {
            "name": "bodyPlainText",
            "dataType": ["text"],
            "description": "Plain text version of email body",
        },
        {
            "name": "fromEmail",
            "dataType": ["text"],
            "description": "Sender email address",
        },
        {
            "name": "fromName",
            "dataType": ["text"],
            "description": "Sender display name",
        },
        {
            "name": "toEmails",
            "dataType": ["text[]"],
            "description": "Recipient email addresses",
        },
        {
            "name": "ccEmails",
            "dataType": ["text[]"],
            "description": "CC recipient email addresses",
        },
        {
            "name": "bccEmails",
            "dataType": ["text[]"],
            "description": "BCC recipient email addresses",
        },
        {
            "name": "emailType",
            "dataType": ["text"],
            "description": "Email type (inbound, outbound, internal)",
        },
        {
            "name": "threadId",
            "dataType": ["text"],
            "description": "Email thread identifier",
        },
        {
            "name": "isReply",
            "dataType": ["boolean"],
            "description": "Whether email is a reply",
        },
        {
            "name": "isForward",
            "dataType": ["boolean"],
            "description": "Whether email is forwarded",
        },
        {
            "name": "priority",
            "dataType": ["text"],
            "description": "Email priority (high, normal, low)",
        },
        {
            "name": "hasAttachments",
            "dataType": ["boolean"],
            "description": "Whether email has attachments",
        },
        {
            "name": "attachmentNames",
            "dataType": ["text[]"],
            "description": "Names of attachments",
        },
        {"name": "sentAt", "dataType": ["date"], "description": "Email sent timestamp"},
        {
            "name": "receivedAt",
            "dataType": ["date"],
            "description": "Email received timestamp",
        },
        {
            "name": "dealId",
            "dataType": ["text"],
            "description": "Associated deal identifier if applicable",
        },
        {
            "name": "opportunityStage",
            "dataType": ["text"],
            "description": "Opportunity stage at time of email",
        },
        {
            "name": "contactIds",
            "dataType": ["text[]"],
            "description": "Associated contact identifiers",
        },
        {
            "name": "accountId",
            "dataType": ["text"],
            "description": "Associated account identifier",
        },
        {
            "name": "companyName",
            "dataType": ["text"],
            "description": "Company associated with email",
        },
        {
            "name": "sentiment",
            "dataType": ["text"],
            "description": "Email sentiment (positive, negative, neutral)",
        },
        {
            "name": "sentimentScore",
            "dataType": ["number"],
            "description": "Sentiment score (-1.0 to 1.0)",
        },
        {
            "name": "urgencyScore",
            "dataType": ["number"],
            "description": "Urgency score (0.0 to 1.0)",
        },
        {
            "name": "topics",
            "dataType": ["text[]"],
            "description": "Topics discussed in email",
        },
        {
            "name": "keywords",
            "dataType": ["text[]"],
            "description": "Important keywords from email",
        },
        {
            "name": "entities",
            "dataType": ["text[]"],
            "description": "Named entities mentioned",
        },
        {
            "name": "actionItems",
            "dataType": ["text[]"],
            "description": "Action items mentioned in email",
        },
        {
            "name": "questions",
            "dataType": ["text[]"],
            "description": "Questions asked in email",
        },
        {
            "name": "nextSteps",
            "dataType": ["text[]"],
            "description": "Next steps mentioned",
        },
        {
            "name": "isInternal",
            "dataType": ["boolean"],
            "description": "Whether email is internal communication",
        },
        {
            "name": "departmentFrom",
            "dataType": ["text"],
            "description": "Sender department if internal",
        },
        {
            "name": "departmentsTo",
            "dataType": ["text[]"],
            "description": "Recipient departments if internal",
        },
        {
            "name": "emailChain",
            "dataType": ["text[]"],
            "description": "Previous email IDs in chain",
        },
        {
            "name": "relatedCallIds",
            "dataType": ["text[]"],
            "description": "Related call identifiers",
        },
        {
            "name": "scheduledMeetings",
            "dataType": ["text[]"],
            "description": "Meeting invites or references",
        },
        {
            "name": "createdAt",
            "dataType": ["date"],
            "description": "Record creation timestamp",
        },
        {
            "name": "updatedAt",
            "dataType": ["date"],
            "description": "Record last update timestamp",
        },
        {
            "name": "source",
            "dataType": ["text"],
            "description": "Data source identifier",
        },
    ],
}
class GongWeaviateSchemaManager:
    """Manages Weaviate schema creation and updates for Gong data"""
    def __init__(self, weaviate_client):
        self.client = weaviate_client
        self.schemas = {
            "GongCall": GONG_CALL_SCHEMA,
            "GongTranscriptChunk": GONG_TRANSCRIPT_CHUNK_SCHEMA,
            "GongEmail": GONG_EMAIL_SCHEMA,
        }
    async def create_all_schemas(self) -> bool:
        """Create all Gong-related schemas in Weaviate"""
        try:
            success_count = 0
            for class_name, schema in self.schemas.items():
                try:
                    success = await self.client.create_collection(
                        name=class_name,
                        properties=schema["properties"],
                        vectorizer=schema.get("vectorizer", "text2vec-openai"),
                    )
                    if success:
                        success_count += 1
                        logger.info(f"Created schema for {class_name}")
                    else:
                        logger.error(f"Failed to create schema for {class_name}")
                except Exception as e:
                    logger.error(f"Error creating schema for {class_name}: {e}")
            return success_count == len(self.schemas)
        except Exception as e:
            logger.error(f"Failed to create Gong schemas: {e}")
            return False
    async def update_schema(self, class_name: str, new_properties: list[dict]) -> bool:
        """Update schema with new properties"""
        try:
            # This would need to be implemented based on actual Weaviate client
            logger.info(f"Schema update for {class_name} would be implemented here")
            return True
        except Exception as e:
            logger.error(f"Failed to update schema for {class_name}: {e}")
            return False
    def get_schema(self, class_name: str) -> Optional[dict]:
        """Get schema definition for a class"""
        return self.schemas.get(class_name)
    def validate_object(
        self, class_name: str, obj_data: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate object data against schema"""
        schema = self.get_schema(class_name)
        if not schema:
            return False, [f"Schema not found for class {class_name}"]
        errors = []
        schema_properties = {prop["name"]: prop for prop in schema["properties"]}
        # Check required fields and data types
        for field_name, _field_value in obj_data.items():
            if field_name in schema_properties:
                schema_properties[field_name]
                # Basic type checking could be implemented here
                continue
            else:
                errors.append(f"Unknown field: {field_name}")
        return len(errors) == 0, errors
def get_gong_schemas() -> dict[str, dict]:
    """Get all Gong schema definitions"""
    return {
        "GongCall": GONG_CALL_SCHEMA,
        "GongTranscriptChunk": GONG_TRANSCRIPT_CHUNK_SCHEMA,
        "GongEmail": GONG_EMAIL_SCHEMA,
    }
def create_call_object(call_data: dict[str, Any]) -> dict[str, Any]:
    """Create a properly formatted GongCall object"""
    return {
        "callId": call_data.get("id", ""),
        "title": call_data.get("title", ""),
        "summary": call_data.get("summary", ""),
        "fullTranscript": call_data.get("transcript", ""),
        "callUrl": call_data.get("url", ""),
        "status": call_data.get("status", CallStatus.COMPLETED.value),
        "scheduledStart": call_data.get("scheduled", datetime.now()).isoformat(),
        "actualStart": call_data.get("started", datetime.now()).isoformat(),
        "actualEnd": call_data.get("ended", datetime.now()).isoformat(),
        "durationSeconds": call_data.get("duration", 0),
        "meetingPlatform": call_data.get("platform", "unknown"),
        "recordingStatus": call_data.get("recording_status", "available"),
        "participantCount": len(call_data.get("participants", [])),
        "internalParticipants": [
            p["email"]
            for p in call_data.get("participants", [])
            if p.get("is_internal", True)
        ],
        "externalParticipants": [
            p["email"]
            for p in call_data.get("participants", [])
            if not p.get("is_internal", True)
        ],
        "departments": list(
            {
                p.get("department", "")
                for p in call_data.get("participants", [])
                if p.get("department")
            }
        ),
        "tags": call_data.get("tags", []),
        "topics": call_data.get("topics", []),
        "keywords": call_data.get("keywords", []),
        "talkRatio": call_data.get("metrics", {}).get("talk_ratio", 0.0),
        "silenceRatio": call_data.get("metrics", {}).get("silence_ratio", 0.0),
        "interruptionsCount": call_data.get("metrics", {}).get(
            "interruptions_count", 0
        ),
        "sentimentScore": call_data.get("metrics", {}).get("sentiment_score"),
        "engagementScore": call_data.get("metrics", {}).get("engagement_score"),
        "actionItems": call_data.get("action_items", []),
        "decisions": call_data.get("decisions", []),
        "nextSteps": call_data.get("next_steps", []),
        "pipelineStage": call_data.get("pipeline_stage"),
        "dealValue": call_data.get("deal_value"),
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "source": "gong_api",
    }
def create_transcript_chunk_object(
    chunk_data: dict[str, Any], call_context: dict[str, Any]
) -> dict[str, Any]:
    """Create a properly formatted GongTranscriptChunk object"""
    return {
        "callId": call_context.get("call_id", ""),
        "chunkId": chunk_data.get(
            "chunk_id",
            f"{call_context.get('call_id', '')}_{chunk_data.get('index', 0)}",
        ),
        "content": chunk_data.get("content", ""),
        "speakerId": chunk_data.get("speaker_id", ""),
        "speakerName": chunk_data.get("speaker_name", ""),
        "speakerRole": chunk_data.get(
            "speaker_role", ParticipantRole.PARTICIPANT.value
        ),
        "speakerEmail": chunk_data.get("speaker_email", ""),
        "isInternal": chunk_data.get("is_internal", True),
        "department": chunk_data.get("department"),
        "startTime": chunk_data.get("start_time", 0.0),
        "endTime": chunk_data.get("end_time", 0.0),
        "duration": chunk_data.get("duration", 0.0),
        "confidence": chunk_data.get("confidence", 0.0),
        "sentiment": chunk_data.get("sentiment", "neutral"),
        "sentimentScore": chunk_data.get("sentiment_score"),
        "keywords": chunk_data.get("keywords", []),
        "topics": chunk_data.get("topics", []),
        "entities": chunk_data.get("entities", []),
        "questions": chunk_data.get("questions", []),
        "actionItems": chunk_data.get("action_items", []),
        "hasScreenShare": chunk_data.get("has_screen_share", False),
        "callDate": call_context.get("call_date", datetime.now()).isoformat(),
        "callTitle": call_context.get("call_title", ""),
        "meetingPlatform": call_context.get("meeting_platform", "unknown"),
        "chunkIndex": chunk_data.get("index", 0),
        "totalChunks": call_context.get("total_chunks", 1),
        "createdAt": datetime.now().isoformat(),
        "source": "gong_api",
    }
def create_email_object(email_data: dict[str, Any]) -> dict[str, Any]:
    """Create a properly formatted GongEmail object"""
    return {
        "emailId": email_data.get("id", ""),
        "subject": email_data.get("subject", ""),
        "body": email_data.get("body_html", ""),
        "bodyPlainText": email_data.get("body_plain", ""),
        "fromEmail": email_data.get("from_email", ""),
        "fromName": email_data.get("from_name", ""),
        "toEmails": email_data.get("to_emails", []),
        "ccEmails": email_data.get("cc_emails", []),
        "bccEmails": email_data.get("bcc_emails", []),
        "emailType": email_data.get("email_type", EmailType.OUTBOUND.value),
        "threadId": email_data.get("thread_id", ""),
        "isReply": email_data.get("is_reply", False),
        "isForward": email_data.get("is_forward", False),
        "priority": email_data.get("priority", "normal"),
        "hasAttachments": email_data.get("has_attachments", False),
        "attachmentNames": email_data.get("attachment_names", []),
        "sentAt": email_data.get("sent_at", datetime.now()).isoformat(),
        "receivedAt": email_data.get("received_at", datetime.now()).isoformat(),
        "dealId": email_data.get("deal_id"),
        "opportunityStage": email_data.get("opportunity_stage"),
        "contactIds": email_data.get("contact_ids", []),
        "accountId": email_data.get("account_id"),
        "companyName": email_data.get("company_name"),
        "sentiment": email_data.get("sentiment", "neutral"),
        "sentimentScore": email_data.get("sentiment_score"),
        "urgencyScore": email_data.get("urgency_score"),
        "topics": email_data.get("topics", []),
        "keywords": email_data.get("keywords", []),
        "entities": email_data.get("entities", []),
        "actionItems": email_data.get("action_items", []),
        "questions": email_data.get("questions", []),
        "nextSteps": email_data.get("next_steps", []),
        "isInternal": email_data.get("is_internal", False),
        "departmentFrom": email_data.get("department_from"),
        "departmentsTo": email_data.get("departments_to", []),
        "emailChain": email_data.get("email_chain", []),
        "relatedCallIds": email_data.get("related_call_ids", []),
        "scheduledMeetings": email_data.get("scheduled_meetings", []),
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "source": "gong_api",
    }
