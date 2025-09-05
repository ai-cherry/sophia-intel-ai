"""
Semantic Role Classification System
=====================================

Advanced semantic classification using ML models and pattern matching
to automatically categorize code components based on their behavior and context.

AI Context:
- Uses embeddings for semantic similarity matching
- Learns from codebase patterns over time
- Critical for intelligent code routing and orchestration
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class CodePattern(Enum):
    """Common code patterns in the system"""
    
    # Architectural patterns
    SINGLETON = "singleton"
    FACTORY = "factory"
    OBSERVER = "observer"
    STRATEGY = "strategy"
    ADAPTER = "adapter"
    FACADE = "facade"
    DECORATOR = "decorator"
    PROXY = "proxy"
    
    # Behavioral patterns
    CHAIN_OF_RESPONSIBILITY = "chain_of_responsibility"
    COMMAND = "command"
    ITERATOR = "iterator"
    MEDIATOR = "mediator"
    MEMENTO = "memento"
    STATE = "state"
    TEMPLATE_METHOD = "template_method"
    VISITOR = "visitor"
    
    # Data patterns
    REPOSITORY = "repository"
    DTO = "data_transfer_object"
    ENTITY = "entity"
    VALUE_OBJECT = "value_object"
    AGGREGATE = "aggregate"
    
    # AI/ML patterns
    PIPELINE = "pipeline"
    TRANSFORMER = "transformer"
    EMBEDDING = "embedding"
    PROMPT_ENGINEERING = "prompt_engineering"
    VECTOR_SEARCH = "vector_search"
    RAG_PATTERN = "rag_pattern"


@dataclass
class SemanticSignature:
    """Semantic signature for code classification"""
    
    # Keywords that indicate role
    primary_keywords: Set[str] = field(default_factory=set)
    secondary_keywords: Set[str] = field(default_factory=set)
    
    # Method patterns
    method_patterns: List[re.Pattern] = field(default_factory=list)
    
    # Import patterns
    import_patterns: List[str] = field(default_factory=list)
    
    # Inheritance patterns
    base_classes: List[str] = field(default_factory=list)
    
    # Decorator patterns
    decorators: List[str] = field(default_factory=list)
    
    # Return type patterns
    return_types: List[str] = field(default_factory=list)
    
    # Confidence threshold
    min_confidence: float = 0.7


class SemanticClassifier:
    """Main classifier for semantic role detection"""
    
    def __init__(self):
        self.signatures = self._build_signatures()
        self.pattern_matchers = self._build_pattern_matchers()
        self.learned_patterns: Dict[str, SemanticSignature] = {}
        
    def _build_signatures(self) -> Dict[str, SemanticSignature]:
        """Build semantic signatures for each role"""
        return {
            "orchestrator": SemanticSignature(
                primary_keywords={"orchestrate", "coordinate", "manage", "direct", "control"},
                secondary_keywords={"flow", "pipeline", "sequence", "chain", "workflow"},
                method_patterns=[
                    re.compile(r".*orchestrate.*"),
                    re.compile(r".*coordinate.*"),
                    re.compile(r".*_flow$"),
                ],
                base_classes=["BaseOrchestrator", "Orchestrator", "Coordinator"],
                decorators=["orchestrator", "workflow"],
            ),
            
            "transformer": SemanticSignature(
                primary_keywords={"transform", "convert", "map", "translate", "adapt"},
                secondary_keywords={"input", "output", "format", "schema", "structure"},
                method_patterns=[
                    re.compile(r".*transform.*"),
                    re.compile(r".*convert.*"),
                    re.compile(r".*to_.*"),
                    re.compile(r".*from_.*"),
                ],
                import_patterns=["transformers", "sklearn.preprocessing"],
            ),
            
            "validator": SemanticSignature(
                primary_keywords={"validate", "verify", "check", "assert", "ensure"},
                secondary_keywords={"rule", "constraint", "requirement", "condition"},
                method_patterns=[
                    re.compile(r".*validate.*"),
                    re.compile(r".*verify.*"),
                    re.compile(r".*check.*"),
                    re.compile(r"is_.*"),
                ],
                base_classes=["BaseModel", "Validator", "Schema"],
                decorators=["validator", "field_validator"],
            ),
            
            "repository": SemanticSignature(
                primary_keywords={"repository", "store", "persist", "fetch", "query"},
                secondary_keywords={"database", "cache", "storage", "collection"},
                method_patterns=[
                    re.compile(r"^get_.*"),
                    re.compile(r"^find_.*"),
                    re.compile(r"^save.*"),
                    re.compile(r"^delete.*"),
                    re.compile(r"^update.*"),
                ],
                base_classes=["Repository", "BaseRepository", "Store"],
                import_patterns=["sqlalchemy", "asyncpg", "redis", "mongodb"],
            ),
            
            "api_endpoint": SemanticSignature(
                primary_keywords={"route", "endpoint", "api", "rest", "graphql"},
                secondary_keywords={"request", "response", "http", "get", "post"},
                decorators=["route", "get", "post", "put", "delete", "api", "endpoint"],
                import_patterns=["fastapi", "flask", "django.urls", "aiohttp"],
            ),
            
            "event_handler": SemanticSignature(
                primary_keywords={"handle", "on", "event", "trigger", "listen"},
                secondary_keywords={"emit", "dispatch", "subscribe", "publish"},
                method_patterns=[
                    re.compile(r"^on_.*"),
                    re.compile(r".*handle.*"),
                    re.compile(r".*_handler$"),
                ],
                decorators=["event", "handler", "listener"],
            ),
            
            "llm_interface": SemanticSignature(
                primary_keywords={"llm", "model", "ai", "generate", "complete"},
                secondary_keywords={"prompt", "token", "embedding", "inference"},
                method_patterns=[
                    re.compile(r".*generate.*"),
                    re.compile(r".*complete.*"),
                    re.compile(r".*embed.*"),
                ],
                import_patterns=["openai", "anthropic", "transformers", "langchain"],
            ),
            
            "prompt_template": SemanticSignature(
                primary_keywords={"prompt", "template", "instruction", "context"},
                secondary_keywords={"format", "variable", "placeholder", "system"},
                method_patterns=[
                    re.compile(r".*prompt.*"),
                    re.compile(r".*template.*"),
                    re.compile(r".*format.*"),
                ],
                return_types=["str", "PromptTemplate", "ChatPromptTemplate"],
            ),
            
            "vector_store": SemanticSignature(
                primary_keywords={"vector", "embedding", "similarity", "search", "index"},
                secondary_keywords={"faiss", "pinecone", "weaviate", "qdrant"},
                method_patterns=[
                    re.compile(r".*search.*"),
                    re.compile(r".*similarity.*"),
                    re.compile(r".*embed.*"),
                    re.compile(r".*index.*"),
                ],
                import_patterns=["faiss", "pinecone", "weaviate", "qdrant", "chromadb"],
            ),
        }
        
    def _build_pattern_matchers(self) -> Dict[CodePattern, SemanticSignature]:
        """Build matchers for design patterns"""
        return {
            CodePattern.SINGLETON: SemanticSignature(
                primary_keywords={"instance", "singleton"},
                method_patterns=[
                    re.compile(r"get_instance"),
                    re.compile(r"__new__"),
                ],
            ),
            
            CodePattern.FACTORY: SemanticSignature(
                primary_keywords={"create", "build", "factory", "make"},
                method_patterns=[
                    re.compile(r"^create_.*"),
                    re.compile(r"^build_.*"),
                    re.compile(r"^make_.*"),
                ],
            ),
            
            CodePattern.OBSERVER: SemanticSignature(
                primary_keywords={"observe", "notify", "subscribe", "listener"},
                method_patterns=[
                    re.compile(r"attach.*"),
                    re.compile(r"detach.*"),
                    re.compile(r"notify.*"),
                ],
            ),
            
            CodePattern.REPOSITORY: SemanticSignature(
                primary_keywords={"repository", "dao", "store"},
                method_patterns=[
                    re.compile(r"^find.*"),
                    re.compile(r"^save.*"),
                    re.compile(r"^delete.*"),
                ],
            ),
            
            CodePattern.PIPELINE: SemanticSignature(
                primary_keywords={"pipeline", "flow", "chain", "sequence"},
                method_patterns=[
                    re.compile(r".*pipeline.*"),
                    re.compile(r".*flow.*"),
                    re.compile(r".*step.*"),
                ],
            ),
            
            CodePattern.RAG_PATTERN: SemanticSignature(
                primary_keywords={"retrieval", "augmented", "generation", "rag"},
                secondary_keywords={"retrieve", "generate", "context", "document"},
                import_patterns=["langchain", "llama_index"],
            ),
        }
        
    def classify(
        self,
        name: str,
        content: str = "",
        imports: List[str] = None,
        base_classes: List[str] = None,
        decorators: List[str] = None,
        methods: List[str] = None,
    ) -> Tuple[Optional[str], float, List[CodePattern]]:
        """
        Classify a code element and return role, confidence, and patterns
        
        Returns:
            Tuple of (role, confidence, patterns)
        """
        imports = imports or []
        base_classes = base_classes or []
        decorators = decorators or []
        methods = methods or []
        
        # Score each signature
        scores = {}
        
        for role, signature in self.signatures.items():
            score = 0.0
            matches = 0
            
            # Check primary keywords (high weight)
            for keyword in signature.primary_keywords:
                if keyword in name.lower() or keyword in content.lower():
                    score += 0.3
                    matches += 1
                    
            # Check secondary keywords (medium weight)
            for keyword in signature.secondary_keywords:
                if keyword in name.lower() or keyword in content.lower():
                    score += 0.15
                    matches += 1
                    
            # Check method patterns
            for pattern in signature.method_patterns:
                for method in methods:
                    if pattern.match(method):
                        score += 0.2
                        matches += 1
                        break
                        
            # Check imports
            for import_pattern in signature.import_patterns:
                for imp in imports:
                    if import_pattern in imp:
                        score += 0.25
                        matches += 1
                        break
                        
            # Check base classes
            for base in signature.base_classes:
                if base in base_classes:
                    score += 0.35
                    matches += 1
                    
            # Check decorators
            for decorator in signature.decorators:
                if decorator in decorators:
                    score += 0.3
                    matches += 1
                    
            # Normalize score
            if matches > 0:
                scores[role] = min(score, 1.0)
                
        # Find best match
        if scores:
            best_role = max(scores, key=scores.get)
            confidence = scores[best_role]
            
            # Check if confidence meets threshold
            if confidence >= self.signatures[best_role].min_confidence:
                # Also detect patterns
                patterns = self._detect_patterns(
                    name, content, imports, base_classes, methods
                )
                return best_role, confidence, patterns
                
        # No confident match, try to detect patterns anyway
        patterns = self._detect_patterns(
            name, content, imports, base_classes, methods
        )
        
        # Default to helper/utility
        return "helper", 0.5, patterns
        
    def _detect_patterns(
        self,
        name: str,
        content: str,
        imports: List[str],
        base_classes: List[str],
        methods: List[str],
    ) -> List[CodePattern]:
        """Detect design patterns in code"""
        detected = []
        
        for pattern, signature in self.pattern_matchers.items():
            score = 0.0
            
            # Similar scoring logic as classify
            for keyword in signature.primary_keywords:
                if keyword in name.lower() or keyword in content.lower():
                    score += 0.4
                    
            for method_pattern in signature.method_patterns:
                for method in methods:
                    if method_pattern.match(method):
                        score += 0.3
                        break
                        
            for import_pattern in signature.import_patterns or []:
                for imp in imports:
                    if import_pattern in imp:
                        score += 0.3
                        break
                        
            if score >= 0.5:  # Lower threshold for pattern detection
                detected.append(pattern)
                
        return detected
        
    def learn_pattern(
        self, role: str, examples: List[Dict[str, Any]]
    ) -> None:
        """Learn new patterns from examples"""
        # Aggregate common features from examples
        all_keywords = []
        all_methods = []
        all_imports = []
        all_bases = []
        
        for example in examples:
            # Extract features from example
            name = example.get("name", "")
            content = example.get("content", "")
            
            # Extract keywords from name and content
            words = re.findall(r"\w+", (name + " " + content).lower())
            all_keywords.extend(words)
            
            # Collect other features
            all_methods.extend(example.get("methods", []))
            all_imports.extend(example.get("imports", []))
            all_bases.extend(example.get("base_classes", []))
            
        # Find most common features
        from collections import Counter
        
        keyword_counts = Counter(all_keywords)
        method_counts = Counter(all_methods)
        import_counts = Counter(all_imports)
        base_counts = Counter(all_bases)
        
        # Create learned signature
        signature = SemanticSignature(
            primary_keywords=set(
                k for k, v in keyword_counts.most_common(5) if v >= len(examples) * 0.5
            ),
            secondary_keywords=set(
                k for k, v in keyword_counts.most_common(10)[5:] if v >= len(examples) * 0.3
            ),
            import_patterns=[
                imp for imp, count in import_counts.most_common(3)
                if count >= len(examples) * 0.4
            ],
            base_classes=[
                base for base, count in base_counts.most_common(3)
                if count >= len(examples) * 0.4
            ],
        )
        
        # Store learned pattern
        self.learned_patterns[role] = signature
        
        # Merge with existing signatures
        if role in self.signatures:
            existing = self.signatures[role]
            existing.primary_keywords.update(signature.primary_keywords)
            existing.secondary_keywords.update(signature.secondary_keywords)
            existing.import_patterns.extend(signature.import_patterns)
            existing.base_classes.extend(signature.base_classes)
        else:
            self.signatures[role] = signature
            
        logger.info(f"Learned new pattern for role: {role}")
        
    def get_role_confidence_threshold(self, role: str) -> float:
        """Get the confidence threshold for a role"""
        if role in self.signatures:
            return self.signatures[role].min_confidence
        return 0.7
        
    def update_confidence_threshold(
        self, role: str, new_threshold: float
    ) -> None:
        """Update confidence threshold for a role"""
        if role in self.signatures:
            self.signatures[role].min_confidence = new_threshold
            logger.info(f"Updated confidence threshold for {role} to {new_threshold}")


# Global classifier instance
_classifier = None


def get_semantic_classifier() -> SemanticClassifier:
    """Get or create the global semantic classifier"""
    global _classifier
    if _classifier is None:
        _classifier = SemanticClassifier()
    return _classifier