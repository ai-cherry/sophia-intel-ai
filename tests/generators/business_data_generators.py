"""Realistic business data generators for testing integrations."""

import random
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

fake = Faker()


class BusinessDataGenerator:
    """Generate realistic business data for testing integrations."""

    @staticmethod
    def generate_notion_database() -> dict[str, Any]:
        """Generate realistic Notion database structure."""
        return {
            "object": "database",
            "id": str(uuid.uuid4()).replace("-", ""),
            "created_time": datetime.utcnow().isoformat(),
            "last_edited_time": datetime.utcnow().isoformat(),
            "title": [
                {
                    "type": "text",
                    "text": {"content": fake.company() + " Projects Database"},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                }
            ],
            "properties": {
                "Name": {"type": "title", "title": {}},
                "Status": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "Not Started", "color": "red"},
                            {"name": "In Progress", "color": "yellow"},
                            {"name": "Completed", "color": "green"},
                        ]
                    },
                },
                "Priority": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "High", "color": "red"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"},
                        ]
                    },
                },
                "Due Date": {"type": "date", "date": {}},
                "Assignee": {"type": "people", "people": {}},
                "Description": {"type": "rich_text", "rich_text": {}},
            },
        }

    @staticmethod
    def generate_notion_page(database_id: str) -> dict[str, Any]:
        """Generate realistic Notion page data."""
        return {
            "object": "page",
            "id": str(uuid.uuid4()).replace("-", ""),
            "created_time": datetime.utcnow().isoformat(),
            "last_edited_time": datetime.utcnow().isoformat(),
            "parent": {"type": "database_id", "database_id": database_id},
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [
                        {"type": "text", "text": {"content": fake.catch_phrase()}}
                    ],
                },
                "Status": {
                    "type": "select",
                    "select": {
                        "name": secrets.choice(
                            ["Not Started", "In Progress", "Completed"]
                        )
                    },
                },
                "Priority": {
                    "type": "select",
                    "select": {"name": secrets.choice(["High", "Medium", "Low"])},
                },
                "Due Date": {
                    "type": "date",
                    "date": {
                        "start": (
                            datetime.utcnow()
                            + timedelta(days=secrets.SystemRandom().randint(1, 30))
                        ).isoformat()
                    },
                },
                "Description": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": fake.text(max_nb_chars=200)},
                        }
                    ],
                },
            },
        }

    @staticmethod
    def generate_slack_message(channel: str) -> dict[str, Any]:
        """Generate realistic Slack message."""
        return {
            "type": "message",
            "text": fake.text(max_nb_chars=150),
            "user": f"U{fake.uuid4()[:8]}",
            "ts": str(datetime.utcnow().timestamp()),
            "channel": channel,
            "reactions": (
                [
                    {
                        "name": secrets.choice(["+1", "heart", "smile", "tada"]),
                        "count": secrets.SystemRandom().randint(1, 5),
                        "users": [
                            f"U{fake.uuid4()[:8]}"
                            for _ in range(secrets.SystemRandom().randint(1, 3))
                        ],
                    }
                ]
                if secrets.SystemRandom().random() > 0.5
                else []
            ),
        }

    @staticmethod
    def generate_linear_issue() -> dict[str, Any]:
        """Generate realistic Linear issue."""
        return {
            "id": str(uuid.uuid4()),
            "number": secrets.SystemRandom().randint(1000, 9999),
            "title": fake.sentence(nb_words=6),
            "description": fake.text(max_nb_chars=300),
            "state": {
                "id": str(uuid.uuid4()),
                "name": secrets.choice(["Backlog", "In Progress", "Done", "Blocked"]),
                "type": secrets.choice(
                    ["unstarted", "started", "completed", "canceled"]
                ),
            },
            "priority": secrets.SystemRandom().randint(1, 5),
            "assignee": (
                {"id": str(uuid.uuid4()), "name": fake.name(), "email": fake.email()}
                if secrets.SystemRandom().random() > 0.3
                else None
            ),
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "labels": {
                "nodes": [
                    {"id": str(uuid.uuid4()), "name": label}
                    for label in random.sample(
                        ["bug", "feature", "enhancement", "documentation"],
                        secrets.SystemRandom().randint(1, 3),
                    )
                ]
            },
        }

    @staticmethod
    def generate_hubspot_contact() -> dict[str, Any]:
        """Generate realistic HubSpot contact."""
        return {
            "id": str(secrets.SystemRandom().randint(1000000, 9999999)),
            "properties": {
                "firstname": fake.first_name(),
                "lastname": fake.last_name(),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "company": fake.company(),
                "jobtitle": fake.job(),
                "createdate": datetime.utcnow().isoformat(),
                "lastmodifieddate": datetime.utcnow().isoformat(),
                "hs_lead_status": secrets.choice(
                    ["NEW", "OPEN", "IN_PROGRESS", "OPEN_DEAL", "UNQUALIFIED"]
                ),
                "hs_analytics_source": secrets.choice(
                    ["ORGANIC_SEARCH", "SOCIAL_MEDIA", "EMAIL_MARKETING", "PAID_SEARCH"]
                ),
            },
        }

    @staticmethod
    def generate_salesforce_opportunity() -> dict[str, Any]:
        """Generate realistic Salesforce opportunity."""
        return {
            "Id": str(uuid.uuid4()),
            "Name": f"{fake.company()} - {fake.catch_phrase()}",
            "Description": fake.text(max_nb_chars=250),
            "StageName": secrets.choice(
                [
                    "Prospecting",
                    "Qualification",
                    "Needs Analysis",
                    "Value Proposition",
                    "Id. Decision Makers",
                    "Proposal/Price Quote",
                    "Negotiation/Review",
                    "Closed Won",
                    "Closed Lost",
                ]
            ),
            "Amount": secrets.SystemRandom().randint(10000, 500000),
            "Probability": secrets.SystemRandom().randint(10, 100),
            "CloseDate": (
                datetime.utcnow()
                + timedelta(days=secrets.SystemRandom().randint(30, 180))
            ).isoformat(),
            "CreatedDate": datetime.utcnow().isoformat(),
            "LastModifiedDate": datetime.utcnow().isoformat(),
            "LeadSource": secrets.choice(
                ["Web", "Phone Inquiry", "Partner Referral", "Purchased List", "Other"]
            ),
        }

    @staticmethod
    def generate_asana_task() -> dict[str, Any]:
        """Generate realistic Asana task."""
        return {
            "gid": str(uuid.uuid4()),
            "name": fake.sentence(nb_words=5),
            "notes": fake.text(max_nb_chars=200),
            "completed": secrets.choice([True, False]),
            "assignee": (
                {"gid": str(uuid.uuid4()), "name": fake.name()}
                if secrets.SystemRandom().random() > 0.4
                else None
            ),
            "due_on": (
                datetime.utcnow()
                + timedelta(days=secrets.SystemRandom().randint(1, 60))
            ).strftime("%Y-%m-%d"),
            "created_at": datetime.utcnow().isoformat(),
            "modified_at": datetime.utcnow().isoformat(),
            "projects": [{"gid": str(uuid.uuid4()), "name": fake.catch_phrase()}],
        }

    @staticmethod
    def generate_gong_call() -> dict[str, Any]:
        """Generate realistic Gong call data."""
        return {
            "id": str(uuid.uuid4()),
            "started": datetime.utcnow().isoformat(),
            "duration": secrets.SystemRandom().randint(1800, 7200),  # 30-120 minutes
            "title": f"{fake.company()} - {fake.catch_phrase()}",
            "direction": secrets.choice(["inbound", "outbound"]),
            "parties": [
                {
                    "name": fake.name(),
                    "email": fake.email(),
                    "title": fake.job(),
                    "affiliation": fake.company(),
                }
                for _ in range(secrets.SystemRandom().randint(2, 5))
            ],
            "topics": random.sample(
                ["pricing", "features", "competition", "timeline", "next_steps"],
                secrets.SystemRandom().randint(2, 4),
            ),
            "outcome": secrets.choice(["positive", "neutral", "negative"]),
        }

    @classmethod
    def generate_batch_data(
        cls, integration: str, count: int = 10
    ) -> list[dict[str, Any]]:
        """Generate batch data for specified integration."""
        generators = {
            "notion": lambda: cls.generate_notion_page(
                str(uuid.uuid4()).replace("-", "")
            ),
            "slack": lambda: cls.generate_slack_message(f"#{fake.word()}"),
            "linear": cls.generate_linear_issue,
            "hubspot": cls.generate_hubspot_contact,
            "salesforce": cls.generate_salesforce_opportunity,
            "asana": cls.generate_asana_task,
            "gong": cls.generate_gong_call,
        }

        if integration not in generators:
            raise ValueError(f"Unknown integration: {integration}")

        return [generators[integration]() for _ in range(count)]

    @classmethod
    def generate_realistic_timeline(cls, days: int = 30) -> list[datetime]:
        """Generate realistic timeline for data generation."""
        now = datetime.utcnow()
        return [now - timedelta(days=i) for i in range(days)]
