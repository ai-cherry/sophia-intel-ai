"""
Support System Module
=====================

Handles customer support, ticket management, knowledge base, and customer interactions.
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TicketStatus(Enum):
    """Ticket status states"""

    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_INTERNAL = "waiting_internal"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(Enum):
    """Ticket priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketCategory(Enum):
    """Ticket categories"""

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    QUESTION = "question"
    COMPLAINT = "complaint"
    BILLING = "billing"
    TECHNICAL = "technical"
    OTHER = "other"


class CustomerSentiment(Enum):
    """Customer sentiment analysis"""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class Customer:
    """Customer model"""

    id: str
    name: str
    email: str
    company: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    total_tickets: int = 0
    satisfaction_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert customer to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "total_tickets": self.total_tickets,
            "satisfaction_score": self.satisfaction_score,
        }


@dataclass
class Ticket:
    """Support ticket model"""

    id: str
    customer_id: str
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    first_response_time: Optional[float] = None
    resolution_time: Optional[float] = None
    messages: List[Dict] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    sentiment: CustomerSentiment = CustomerSentiment.NEUTRAL

    def to_dict(self) -> Dict:
        """Convert ticket to dictionary"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "category": self.category.value,
            "assignee": self.assignee,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "first_response_time": self.first_response_time,
            "resolution_time": self.resolution_time,
            "messages": self.messages,
            "attachments": self.attachments,
            "tags": self.tags,
            "sentiment": self.sentiment.value,
        }


@dataclass
class KnowledgeArticle:
    """Knowledge base article model"""

    id: str
    title: str
    content: str
    category: str
    author: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    views: int = 0
    helpful_votes: int = 0
    unhelpful_votes: int = 0
    tags: List[str] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert article to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "views": self.views,
            "helpful_votes": self.helpful_votes,
            "unhelpful_votes": self.unhelpful_votes,
            "tags": self.tags,
            "related_articles": self.related_articles,
        }


class SupportSystem:
    """
    Main customer support engine for Sophia.
    Handles ticket management, customer interactions, and knowledge base.
    """

    def __init__(self, llm_client=None):
        """Initialize the support system"""
        self.llm_client = llm_client
        self.tickets: Dict[str, Ticket] = {}
        self.customers: Dict[str, Customer] = {}
        self.knowledge_base: Dict[str, KnowledgeArticle] = {}
        self.agents: Dict[str, Dict] = {}
        self.auto_responses = self._load_auto_responses()

    def _load_auto_responses(self) -> Dict[str, str]:
        """Load automated response templates"""
        return {
            "greeting": "Thank you for contacting support. We've received your ticket and will respond shortly.",
            "resolved": "Your ticket has been resolved. Please let us know if you need further assistance.",
            "waiting_info": "We need additional information to proceed with your request. Please provide the requested details.",
            "escalated": "Your ticket has been escalated to our senior support team for priority handling.",
            "closed": "This ticket has been closed. Feel free to open a new ticket if you need assistance.",
        }

    def create_ticket(
        self,
        customer_email: str,
        subject: str,
        description: str,
        category: TicketCategory = TicketCategory.OTHER,
        priority: Optional[TicketPriority] = None,
    ) -> Ticket:
        """
        Create a new support ticket.

        Args:
            customer_email: Customer email
            subject: Ticket subject
            description: Issue description
            category: Ticket category
            priority: Ticket priority (auto-detected if not provided)

        Returns:
            Created ticket
        """
        # Get or create customer
        customer = self._get_or_create_customer(customer_email)

        # Auto-detect priority if not provided
        if priority is None:
            priority = self._detect_priority(subject, description)

        # Analyze sentiment
        sentiment = self._analyze_sentiment(description)

        ticket_id = str(uuid.uuid4())

        ticket = Ticket(
            id=ticket_id,
            customer_id=customer.id,
            subject=subject,
            description=description,
            status=TicketStatus.NEW,
            priority=priority,
            category=category,
            sentiment=sentiment,
        )

        # Extract tags from description
        ticket.tags = self._extract_tags(description)

        # Add initial message
        ticket.messages.append(
            {"sender": "customer", "message": description, "timestamp": datetime.now().isoformat()}
        )

        # Add auto response
        auto_response = self.auto_responses["greeting"]
        ticket.messages.append(
            {"sender": "system", "message": auto_response, "timestamp": datetime.now().isoformat()}
        )

        self.tickets[ticket_id] = ticket
        customer.total_tickets += 1

        # Auto-assign if possible
        self._auto_assign_ticket(ticket)

        return ticket

    def respond_to_ticket(
        self, ticket_id: str, message: str, sender: str = "agent", internal_note: bool = False
    ) -> bool:
        """
        Add a response to a ticket.

        Args:
            ticket_id: Ticket ID
            message: Response message
            sender: Message sender (agent/customer/system)
            internal_note: Whether this is an internal note

        Returns:
            Success status
        """
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]

        # Track first response time
        if sender == "agent" and ticket.first_response_time is None:
            elapsed = (datetime.now() - ticket.created_at).total_seconds() / 3600
            ticket.first_response_time = elapsed

        # Add message
        ticket.messages.append(
            {
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "internal": internal_note,
            }
        )

        # Update ticket status
        if (
            sender == "agent"
            and ticket.status == TicketStatus.NEW
            or sender == "customer"
            and ticket.status == TicketStatus.WAITING_CUSTOMER
        ):
            ticket.status = TicketStatus.IN_PROGRESS

        ticket.updated_at = datetime.now()

        return True

    def resolve_ticket(self, ticket_id: str, resolution: str) -> bool:
        """
        Resolve a ticket.

        Args:
            ticket_id: Ticket ID
            resolution: Resolution description

        Returns:
            Success status
        """
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]

        # Add resolution message
        self.respond_to_ticket(ticket_id, resolution, sender="agent")

        # Update ticket
        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = datetime.now()
        ticket.resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600

        # Send auto response
        self.respond_to_ticket(ticket_id, self.auto_responses["resolved"], sender="system")

        return True

    def escalate_ticket(self, ticket_id: str, reason: str) -> bool:
        """
        Escalate a ticket to higher priority.

        Args:
            ticket_id: Ticket ID
            reason: Escalation reason

        Returns:
            Success status
        """
        if ticket_id not in self.tickets:
            return False

        ticket = self.tickets[ticket_id]

        # Upgrade priority
        if ticket.priority == TicketPriority.LOW:
            ticket.priority = TicketPriority.MEDIUM
        elif ticket.priority == TicketPriority.MEDIUM:
            ticket.priority = TicketPriority.HIGH
        elif ticket.priority == TicketPriority.HIGH:
            ticket.priority = TicketPriority.CRITICAL

        # Add escalation note
        self.respond_to_ticket(
            ticket_id, f"Ticket escalated: {reason}", sender="system", internal_note=True
        )

        # Send customer notification
        self.respond_to_ticket(ticket_id, self.auto_responses["escalated"], sender="system")

        return True

    def search_knowledge_base(self, query: str, limit: int = 5) -> List[KnowledgeArticle]:
        """
        Search knowledge base for relevant articles.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of relevant articles
        """
        # Simple keyword matching (would use vector search in production)
        query_words = set(query.lower().split())
        scored_articles = []

        for article_id, article in self.knowledge_base.items():
            # Calculate relevance score
            title_words = set(article.title.lower().split())
            content_words = set(article.content.lower().split())
            tag_words = set(" ".join(article.tags).lower().split())

            score = (
                len(query_words & title_words) * 3
                + len(query_words & content_words) * 1
                + len(query_words & tag_words) * 2
            )

            if score > 0:
                scored_articles.append((score, article))

        # Sort by score and return top results
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scored_articles[:limit]]

    def suggest_resolution(self, ticket_id: str) -> Optional[str]:
        """
        Suggest a resolution based on similar past tickets.

        Args:
            ticket_id: Ticket ID

        Returns:
            Suggested resolution or None
        """
        if ticket_id not in self.tickets:
            return None

        ticket = self.tickets[ticket_id]

        # Search knowledge base
        relevant_articles = self.search_knowledge_base(f"{ticket.subject} {ticket.description}")

        if relevant_articles:
            # Format suggestion from top article
            top_article = relevant_articles[0]
            suggestion = f"""Based on similar issues, here's a suggested resolution:

**{top_article.title}**

{top_article.content[:500]}...

This resolution has helped {top_article.helpful_votes} other customers."""
            return suggestion

        # If LLM is available, generate suggestion
        if self.llm_client:
            return self._generate_llm_suggestion(ticket)

        return None

    def get_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """
        Get complete customer history.

        Args:
            customer_id: Customer ID

        Returns:
            Customer history including all tickets
        """
        if customer_id not in self.customers:
            return {"error": "Customer not found"}

        customer = self.customers[customer_id]

        # Get all customer tickets
        customer_tickets = [
            ticket for ticket in self.tickets.values() if ticket.customer_id == customer_id
        ]

        # Calculate statistics
        total_tickets = len(customer_tickets)
        resolved_tickets = sum(1 for t in customer_tickets if t.status == TicketStatus.RESOLVED)
        avg_resolution_time = 0

        if resolved_tickets > 0:
            total_time = sum(
                t.resolution_time for t in customer_tickets if t.resolution_time is not None
            )
            avg_resolution_time = total_time / resolved_tickets

        # Analyze sentiment trend
        sentiment_scores = {
            CustomerSentiment.VERY_POSITIVE: 5,
            CustomerSentiment.POSITIVE: 4,
            CustomerSentiment.NEUTRAL: 3,
            CustomerSentiment.NEGATIVE: 2,
            CustomerSentiment.VERY_NEGATIVE: 1,
        }

        avg_sentiment = 3
        if customer_tickets:
            total_sentiment = sum(sentiment_scores[t.sentiment] for t in customer_tickets)
            avg_sentiment = total_sentiment / len(customer_tickets)

        return {
            "customer": customer.to_dict(),
            "tickets": [t.to_dict() for t in customer_tickets],
            "statistics": {
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "open_tickets": total_tickets - resolved_tickets,
                "avg_resolution_time": avg_resolution_time,
                "avg_sentiment": avg_sentiment,
            },
        }

    def generate_support_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Generate support metrics for a given period.

        Args:
            period_days: Number of days to analyze

        Returns:
            Support metrics and KPIs
        """
        cutoff_date = datetime.now() - timedelta(days=period_days)

        # Filter tickets in period
        period_tickets = [
            ticket for ticket in self.tickets.values() if ticket.created_at >= cutoff_date
        ]

        if not period_tickets:
            return {"message": "No tickets in the specified period"}

        # Calculate metrics
        total_tickets = len(period_tickets)
        resolved_tickets = sum(1 for t in period_tickets if t.status == TicketStatus.RESOLVED)

        # Response time metrics
        response_times = [
            t.first_response_time for t in period_tickets if t.first_response_time is not None
        ]
        avg_first_response = sum(response_times) / len(response_times) if response_times else 0

        # Resolution time metrics
        resolution_times = [
            t.resolution_time for t in period_tickets if t.resolution_time is not None
        ]
        avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # Category breakdown
        category_counts = {}
        for ticket in period_tickets:
            category = ticket.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

        # Priority breakdown
        priority_counts = {}
        for ticket in period_tickets:
            priority = ticket.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Sentiment analysis
        sentiment_counts = {}
        for ticket in period_tickets:
            sentiment = ticket.sentiment.value
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

        return {
            "period": f"Last {period_days} days",
            "overview": {
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": (
                    (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
                ),
                "open_tickets": total_tickets - resolved_tickets,
            },
            "performance": {
                "avg_first_response_time": f"{avg_first_response:.2f} hours",
                "avg_resolution_time": f"{avg_resolution:.2f} hours",
            },
            "breakdown": {
                "by_category": category_counts,
                "by_priority": priority_counts,
                "by_sentiment": sentiment_counts,
            },
            "trends": self._calculate_trends(period_tickets),
        }

    def create_knowledge_article(
        self, title: str, content: str, category: str, author: str, tags: List[str] = None
    ) -> KnowledgeArticle:
        """
        Create a new knowledge base article.

        Args:
            title: Article title
            content: Article content
            category: Article category
            author: Author name
            tags: Article tags

        Returns:
            Created article
        """
        article_id = str(uuid.uuid4())

        article = KnowledgeArticle(
            id=article_id,
            title=title,
            content=content,
            category=category,
            author=author,
            tags=tags or [],
        )

        # Find related articles
        related = self.search_knowledge_base(title + " " + content, limit=3)
        article.related_articles = [a.id for a in related]

        self.knowledge_base[article_id] = article
        return article

    # Helper methods
    def _get_or_create_customer(self, email: str) -> Customer:
        """Get existing customer or create new one"""
        for customer in self.customers.values():
            if customer.email == email:
                return customer

        # Create new customer
        customer_id = str(uuid.uuid4())
        customer = Customer(
            id=customer_id, name=email.split("@")[0], email=email  # Use email prefix as name
        )

        self.customers[customer_id] = customer
        return customer

    def _detect_priority(self, subject: str, description: str) -> TicketPriority:
        """Auto-detect ticket priority based on content"""
        content = (subject + " " + description).lower()

        # Critical keywords
        critical_keywords = ["urgent", "emergency", "critical", "down", "broken", "crashed"]
        if any(keyword in content for keyword in critical_keywords):
            return TicketPriority.CRITICAL

        # High priority keywords
        high_keywords = ["important", "asap", "quickly", "immediate"]
        if any(keyword in content for keyword in high_keywords):
            return TicketPriority.HIGH

        # Low priority keywords
        low_keywords = ["question", "wondering", "curious", "minor"]
        if any(keyword in content for keyword in low_keywords):
            return TicketPriority.LOW

        return TicketPriority.MEDIUM

    def _analyze_sentiment(self, text: str) -> CustomerSentiment:
        """Analyze customer sentiment from text"""
        text_lower = text.lower()

        # Very negative indicators
        very_negative = ["terrible", "awful", "horrible", "worst", "unacceptable"]
        if any(word in text_lower for word in very_negative):
            return CustomerSentiment.VERY_NEGATIVE

        # Negative indicators
        negative = ["bad", "poor", "disappointed", "frustrated", "unhappy"]
        if any(word in text_lower for word in negative):
            return CustomerSentiment.NEGATIVE

        # Positive indicators
        positive = ["good", "great", "happy", "satisfied", "pleased"]
        if any(word in text_lower for word in positive):
            return CustomerSentiment.POSITIVE

        # Very positive indicators
        very_positive = ["excellent", "amazing", "fantastic", "wonderful", "perfect"]
        if any(word in text_lower for word in very_positive):
            return CustomerSentiment.VERY_POSITIVE

        return CustomerSentiment.NEUTRAL

    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        tags = []

        # Extract hashtags
        hashtags = re.findall(r"#(\w+)", text)
        tags.extend(hashtags)

        # Extract common technical terms
        tech_terms = ["api", "database", "server", "login", "payment", "error", "bug"]
        text_lower = text.lower()
        for term in tech_terms:
            if term in text_lower:
                tags.append(term)

        return list(set(tags))

    def _auto_assign_ticket(self, ticket: Ticket) -> bool:
        """Auto-assign ticket to appropriate agent"""
        # Simple round-robin assignment (would be more sophisticated in production)
        available_agents = [
            agent_id for agent_id, agent in self.agents.items() if agent.get("available", False)
        ]

        if available_agents:
            # Assign to agent with least tickets
            agent_loads = {}
            for agent_id in available_agents:
                agent_loads[agent_id] = sum(
                    1
                    for t in self.tickets.values()
                    if t.assignee == agent_id
                    and t.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]
                )

            best_agent = min(agent_loads, key=agent_loads.get)
            ticket.assignee = best_agent
            return True

        return False

    def _generate_llm_suggestion(self, ticket: Ticket) -> str:
        """Generate resolution suggestion using LLM"""
        # This would call the LLM with ticket context
        return "LLM-generated suggestion would appear here"

    def _calculate_trends(self, tickets: List[Ticket]) -> Dict:
        """Calculate ticket trends"""
        if not tickets:
            return {}

        # Group tickets by day
        daily_counts = {}
        for ticket in tickets:
            day = ticket.created_at.date()
            daily_counts[day] = daily_counts.get(day, 0) + 1

        # Calculate trend
        dates = sorted(daily_counts.keys())
        if len(dates) > 1:
            first_half = sum(daily_counts[d] for d in dates[: len(dates) // 2])
            second_half = sum(daily_counts[d] for d in dates[len(dates) // 2 :])
            trend = "increasing" if second_half > first_half else "decreasing"
        else:
            trend = "stable"

        return {
            "ticket_volume_trend": trend,
            "daily_average": sum(daily_counts.values()) / len(daily_counts),
        }
