"""
Classification engine for automatic knowledge categorization
"""

from __future__ import annotations

import re

from app.core.ai_logger import logger
from app.knowledge.models import (
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
)


class ClassificationEngine:
    """
    Intelligent classification of knowledge entities based on:
    - Content analysis
    - Keyword matching
    - Context patterns
    - Pay-Ready specific rules
    """

    def __init__(self):
        self.classification_rules = self._init_classification_rules()
        self.priority_rules = self._init_priority_rules()
        self.pay_ready_keywords = self._init_pay_ready_keywords()

    def _init_classification_rules(self) -> dict[KnowledgeClassification, dict]:
        """Initialize classification rules"""
        return {
            KnowledgeClassification.FOUNDATIONAL: {
                "keywords": [
                    "mission",
                    "vision",
                    "core",
                    "fundamental",
                    "principle",
                    "company overview",
                    "foundation",
                    "pillar",
                    "essence",
                    "pay ready",
                    "bootstrapped",
                    "profitable",
                    "$20B",
                ],
                "patterns": [
                    r"company\s+(mission|vision|values)",
                    r"core\s+(business|principle|value)",
                    r"fundamental\s+(strategy|approach)",
                    r"pay\s+ready.*platform",
                ],
                "categories": ["company_overview", "core_values", "mission_vision"],
            },
            KnowledgeClassification.STRATEGIC: {
                "keywords": [
                    "strategy",
                    "strategic",
                    "initiative",
                    "roadmap",
                    "plan",
                    "executive decision",
                    "board",
                    "investment",
                    "acquisition",
                    "market position",
                    "competitive",
                    "growth",
                ],
                "patterns": [
                    r"strategic\s+(initiative|plan|direction)",
                    r"executive\s+(decision|approval)",
                    r"board\s+(meeting|decision|presentation)",
                    r"market\s+(analysis|intelligence|position)",
                ],
                "categories": [
                    "strategic_initiatives",
                    "executive_decisions",
                    "market_intelligence",
                ],
            },
            KnowledgeClassification.OPERATIONAL: {
                "keywords": [
                    "process",
                    "procedure",
                    "workflow",
                    "task",
                    "operation",
                    "daily",
                    "routine",
                    "standard",
                    "implementation",
                    "metric",
                    "kpi",
                    "performance",
                    "report",
                ],
                "patterns": [
                    r"operational\s+(process|procedure)",
                    r"daily\s+(operation|task|report)",
                    r"standard\s+(procedure|workflow)",
                    r"performance\s+(metric|indicator)",
                ],
                "categories": ["operations", "processes", "metrics", "reports"],
            },
            KnowledgeClassification.REFERENCE: {
                "keywords": [
                    "reference",
                    "documentation",
                    "guide",
                    "manual",
                    "resource",
                    "policy",
                    "compliance",
                    "regulation",
                    "standard",
                    "template",
                    "example",
                    "best practice",
                ],
                "patterns": [
                    r"reference\s+(document|material)",
                    r"compliance\s+(requirement|standard)",
                    r"best\s+practice",
                    r"policy\s+(document|manual)",
                ],
                "categories": ["policies", "documentation", "compliance", "templates"],
            },
        }

    def _init_priority_rules(self) -> dict[KnowledgePriority, list[str]]:
        """Initialize priority determination rules"""
        return {
            KnowledgePriority.CRITICAL: [
                "ceo",
                "board",
                "investor",
                "acquisition",
                "merger",
                "crisis",
                "critical",
                "urgent",
                "immediate",
                "compliance violation",
                "legal",
                "security breach",
            ],
            KnowledgePriority.HIGH: [
                "strategic",
                "executive",
                "important",
                "priority",
                "key initiative",
                "major",
                "significant",
                "core",
                "foundational",
                "pay ready",
                "$20B",
                "100 employees",
            ],
            KnowledgePriority.MEDIUM: [
                "standard",
                "regular",
                "normal",
                "typical",
                "process",
                "procedure",
                "workflow",
                "operational",
            ],
            KnowledgePriority.LOW: [
                "minor",
                "trivial",
                "optional",
                "nice-to-have",
                "reference",
                "archive",
                "historical",
            ],
        }

    def _init_pay_ready_keywords(self) -> set[str]:
        """Pay-Ready specific keywords that indicate foundational knowledge"""
        return {
            "pay ready",
            "payready",
            "resident engagement",
            "multifamily housing",
            "property management",
            "pmc",
            "collections",
            "recovery platform",
            "bootstrapped",
            "profitable",
            "$20B",
            "rent processed",
            "ai-first",
            "financial operating system",
            "proptech",
            "lynn musil",
            "ceo",
            "founder",
            "executive team",
        }

    async def classify(self, entity: KnowledgeEntity) -> KnowledgeClassification:
        """
        Classify a knowledge entity based on content and context
        """
        # Combine all text for analysis
        text = self._extract_text(entity).lower()

        # Check for Pay-Ready specific content first
        if self._is_pay_ready_foundational(text):
            return KnowledgeClassification.FOUNDATIONAL

        # Score each classification
        scores = {}
        for classification, rules in self.classification_rules.items():
            score = 0

            # Keyword matching
            for keyword in rules["keywords"]:
                if keyword in text:
                    score += 2

            # Pattern matching
            for pattern in rules["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 3

            # Category matching
            if entity.category in rules["categories"]:
                score += 5

            scores[classification] = score

        # Return classification with highest score
        best_classification = max(scores, key=scores.get)

        # If score is too low, default to operational
        if scores[best_classification] < 3:
            best_classification = KnowledgeClassification.OPERATIONAL

        logger.debug(
            f"Classified {entity.name} as {best_classification.value} (scores: {scores})"
        )
        return best_classification

    async def determine_priority(self, entity: KnowledgeEntity) -> KnowledgePriority:
        """
        Determine priority level for knowledge entity
        """
        text = self._extract_text(entity).lower()

        # Check each priority level
        for priority, keywords in self.priority_rules.items():
            for keyword in keywords:
                if keyword in text:
                    return priority

        # Default based on classification
        if (
            entity.classification == KnowledgeClassification.FOUNDATIONAL
            or entity.classification == KnowledgeClassification.STRATEGIC
        ):
            return KnowledgePriority.HIGH
        elif entity.classification == KnowledgeClassification.OPERATIONAL:
            return KnowledgePriority.MEDIUM
        else:
            return KnowledgePriority.LOW

    async def suggest_tags(self, entity: KnowledgeEntity) -> list[str]:
        """
        Suggest relevant tags for knowledge entity
        """
        text = self._extract_text(entity).lower()
        tags = []

        # Add classification as tag
        tags.append(entity.classification.value)

        # Add priority as tag if high or critical
        if entity.priority >= KnowledgePriority.HIGH:
            tags.append(f"priority_{entity.priority.name.lower()}")

        # Check for Pay-Ready specific tags
        if "pay ready" in text or "payready" in text:
            tags.append("pay_ready")

        if "$20b" in text or "20 billion" in text:
            tags.append("scale_20b")

        if "bootstrapped" in text:
            tags.append("bootstrapped")

        if "profitable" in text:
            tags.append("profitable")

        # Technology tags
        tech_keywords = {
            "ai": "ai_powered",
            "machine learning": "ml",
            "automation": "automated",
            "api": "api",
            "integration": "integration",
            "platform": "platform",
        }

        for keyword, tag in tech_keywords.items():
            if keyword in text:
                tags.append(tag)

        # Business tags
        business_keywords = {
            "revenue": "revenue",
            "growth": "growth",
            "customer": "customer",
            "market": "market",
            "competitive": "competitive",
            "strategy": "strategic",
        }

        for keyword, tag in business_keywords.items():
            if keyword in text:
                tags.append(tag)

        # Remove duplicates and return
        return list(set(tags))

    async def detect_sensitivity(self, entity: KnowledgeEntity) -> dict[str, bool]:
        """
        Detect sensitive information in knowledge
        """
        text = self._extract_text(entity)

        sensitivity = {
            "contains_pii": self._contains_pii(text),
            "contains_financial": self._contains_financial(text),
            "contains_strategic": self._contains_strategic(text),
            "contains_legal": self._contains_legal(text),
            "is_confidential": False,
            "is_proprietary": False,
        }

        # Check for explicit confidentiality markers
        confidential_markers = [
            "confidential",
            "proprietary",
            "internal only",
            "do not share",
        ]
        for marker in confidential_markers:
            if marker in text.lower():
                sensitivity["is_confidential"] = True
                break

        # Pay-Ready strategic information is proprietary
        if self._is_pay_ready_foundational(text.lower()):
            sensitivity["is_proprietary"] = True

        return sensitivity

    def _extract_text(self, entity: KnowledgeEntity) -> str:
        """Extract all text from entity for analysis"""
        texts = [
            entity.name,
            entity.category,
            str(entity.content),
            str(entity.metadata),
        ]

        return " ".join(texts)

    def _is_pay_ready_foundational(self, text: str) -> bool:
        """Check if content is Pay-Ready foundational"""
        foundational_indicators = [
            "pay ready" in text and ("mission" in text or "vision" in text),
            "$20b" in text and "rent" in text,
            "bootstrapped" in text and "profitable" in text,
            "multifamily housing" in text and "platform" in text,
            "lynn musil" in text and "ceo" in text,
        ]

        return any(foundational_indicators)

    def _contains_pii(self, text: str) -> bool:
        """Check for personally identifiable information"""
        # Simple PII patterns - enhance for production
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone
            r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",  # Credit card
        ]

        return any(re.search(pattern, text) for pattern in pii_patterns)

    def _contains_financial(self, text: str) -> bool:
        """Check for financial information"""
        financial_keywords = [
            "revenue",
            "profit",
            "loss",
            "margin",
            "cost",
            "budget",
            "forecast",
            "financial",
            "earnings",
            "$",
            "dollar",
            "million",
            "billion",
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in financial_keywords)

    def _contains_strategic(self, text: str) -> bool:
        """Check for strategic information"""
        strategic_keywords = [
            "strategy",
            "roadmap",
            "initiative",
            "acquisition",
            "merger",
            "competitive",
            "confidential",
            "proprietary",
            "board",
            "investor",
            "executive decision",
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in strategic_keywords)

    def _contains_legal(self, text: str) -> bool:
        """Check for legal information"""
        legal_keywords = [
            "legal",
            "contract",
            "agreement",
            "compliance",
            "regulation",
            "lawsuit",
            "liability",
            "dispute",
            "patent",
            "trademark",
            "copyright",
            "nda",
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in legal_keywords)
