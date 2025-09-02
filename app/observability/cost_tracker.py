"""
Cost Tracking System for LLM Operations
Tracks token usage, costs, and provides analytics.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class CostEventType(Enum):
    """Types of cost events."""
    LLM_COMPLETION = "llm_completion"
    EMBEDDING = "embedding"
    SWARM_EXECUTION = "swarm_execution"
    API_CALL = "api_call"


@dataclass
class CostEvent:
    """A single cost event record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    trace_id: Optional[str] = None
    event_type: CostEventType = CostEventType.LLM_COMPLETION
    
    # Model and provider info
    model: str = "unknown"
    provider: str = "unknown"
    
    # Token usage
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # Cost information
    cost_usd: float = 0.0
    cost_per_1k_prompt: Optional[float] = None
    cost_per_1k_completion: Optional[float] = None
    
    # Context information
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "event_type": self.event_type.value,
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "cost_per_1k_prompt": self.cost_per_1k_prompt,
            "cost_per_1k_completion": self.cost_per_1k_completion,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "request_size_bytes": self.request_size_bytes,
            "response_size_bytes": self.response_size_bytes,
            "metadata": self.metadata
        }


@dataclass
class CostSummary:
    """Cost summary for a time period."""
    period_start: datetime
    period_end: datetime
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    
    # Breakdown by type
    llm_completion_cost: float = 0.0
    embedding_cost: float = 0.0
    swarm_execution_cost: float = 0.0
    api_call_cost: float = 0.0
    
    # Breakdown by model
    model_costs: Dict[str, float] = field(default_factory=dict)
    model_tokens: Dict[str, int] = field(default_factory=dict)
    
    # Breakdown by provider
    provider_costs: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ModelPricing:
    """Model pricing configuration."""
    
    # OpenAI pricing (per 1K tokens)
    OPENAI_PRICING = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    }
    
    # OpenRouter pricing (estimated)
    OPENROUTER_PRICING = {
        "openai/gpt-4": {"prompt": 0.03, "completion": 0.06},
        "openai/gpt-5": {"prompt": 0.05, "completion": 0.10},  # Estimated
        "google/gemini-2.5-flash": {"prompt": 0.001, "completion": 0.002},
        "google/gemini-2.5-pro": {"prompt": 0.002, "completion": 0.004},
        "deepseek/deepseek-chat-v3-0324": {"prompt": 0.0001, "completion": 0.0002},
        "deepseek/deepseek-chat-v3.1": {"prompt": 0.0001, "completion": 0.0002},
        "x-ai/grok-code-fast-1": {"prompt": 0.0005, "completion": 0.001},
        "qwen/qwen3-30b-a3b": {"prompt": 0.0003, "completion": 0.0006},
        "qwen/qwen3-coder": {"prompt": 0.0003, "completion": 0.0006},
        "deepseek/deepseek-r1-0528:free": {"prompt": 0.0, "completion": 0.0},  # Free tier
        "z-ai/glm-4.5": {"prompt": 0.0002, "completion": 0.0004},
    }
    
    # Together AI embedding pricing (per 1K tokens)
    TOGETHER_EMBEDDING_PRICING = {
        "togethercomputer/m2-bert-80M-32k-retrieval": 0.00008,
        "togethercomputer/m2-bert-80M-8k-retrieval": 0.00008,
        "togethercomputer/m2-bert-80M-2k-retrieval": 0.00008,
        "BAAI/bge-large-en-v1.5": 0.00008,
        "BAAI/bge-base-en-v1.5": 0.00008,
        "WhereIsAI/UAE-Large-V1": 0.00008,
        "Alibaba-NLP/gte-modernbert-base": 0.00008,
        "intfloat/multilingual-e5-large-instruct": 0.00008,
    }
    
    @classmethod
    def get_model_pricing(cls, model: str, provider: str = "openrouter") -> Dict[str, float]:
        """Get pricing for a model."""
        if provider == "openai":
            return cls.OPENAI_PRICING.get(model, {"prompt": 0.001, "completion": 0.002})
        elif provider == "openrouter":
            return cls.OPENROUTER_PRICING.get(model, {"prompt": 0.001, "completion": 0.002})
        elif provider == "together-ai":
            cost_per_1k = cls.TOGETHER_EMBEDDING_PRICING.get(model, 0.0001)
            return {"prompt": cost_per_1k, "completion": 0}
        else:
            # Default fallback pricing
            return {"prompt": 0.001, "completion": 0.002}
    
    @classmethod
    def calculate_cost(
        cls,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        provider: str = "openrouter"
    ) -> float:
        """Calculate cost for token usage."""
        pricing = cls.get_model_pricing(model, provider)
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost


class CostTracker:
    """
    Tracks and analyzes costs for LLM operations.
    Stores events in memory and persists to JSON files.
    """
    
    def __init__(self, storage_path: str = "data/cost_tracking"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.events: List[CostEvent] = []
        self._load_events()
        
        # Background task for periodic persistence
        self._save_task = None
        
    def _load_events(self):
        """Load existing events from storage."""
        try:
            events_file = self.storage_path / "cost_events.jsonl"
            if events_file.exists():
                with open(events_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line.strip())
                            event = self._dict_to_cost_event(data)
                            self.events.append(event)
                
                logger.info(f"Loaded {len(self.events)} cost events from storage")
        except Exception as e:
            logger.error(f"Failed to load cost events: {e}")
    
    def _dict_to_cost_event(self, data: Dict[str, Any]) -> CostEvent:
        """Convert dictionary back to CostEvent."""
        return CostEvent(
            id=data.get("id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            trace_id=data.get("trace_id"),
            event_type=CostEventType(data["event_type"]),
            model=data.get("model", "unknown"),
            provider=data.get("provider", "unknown"),
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            cost_usd=data.get("cost_usd", 0.0),
            cost_per_1k_prompt=data.get("cost_per_1k_prompt"),
            cost_per_1k_completion=data.get("cost_per_1k_completion"),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            endpoint=data.get("endpoint"),
            request_size_bytes=data.get("request_size_bytes", 0),
            response_size_bytes=data.get("response_size_bytes", 0),
            metadata=data.get("metadata", {})
        )
    
    def _save_events(self):
        """Persist events to storage."""
        try:
            events_file = self.storage_path / "cost_events.jsonl"
            
            # Write all events (append-only for now, can optimize later)
            with open(events_file, 'w') as f:
                for event in self.events:
                    f.write(json.dumps(event.to_dict()) + '\n')
                    
            logger.debug(f"Saved {len(self.events)} cost events to storage")
        except Exception as e:
            logger.error(f"Failed to save cost events: {e}")
    
    def record_llm_completion(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        provider: str = "openrouter",
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEvent:
        """Record an LLM completion cost event."""
        # Calculate cost
        cost_usd = ModelPricing.calculate_cost(model, prompt_tokens, completion_tokens, provider)
        pricing = ModelPricing.get_model_pricing(model, provider)
        
        event = CostEvent(
            trace_id=trace_id,
            event_type=CostEventType.LLM_COMPLETION,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            cost_per_1k_prompt=pricing["prompt"],
            cost_per_1k_completion=pricing["completion"],
            session_id=session_id,
            endpoint=endpoint,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        logger.info(f"Recorded LLM completion: {model} - ${cost_usd:.6f} ({prompt_tokens}+{completion_tokens} tokens)")
        
        return event
    
    def record_embedding(
        self,
        model: str,
        tokens: int,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        provider: str = "together-ai",
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostEvent:
        """Record an embedding cost event."""
        # Calculate cost (embeddings only have input tokens)
        cost_usd = ModelPricing.calculate_cost(model, tokens, 0, provider)
        pricing = ModelPricing.get_model_pricing(model, provider)
        
        event = CostEvent(
            trace_id=trace_id,
            event_type=CostEventType.EMBEDDING,
            model=model,
            provider=provider,
            prompt_tokens=tokens,
            completion_tokens=0,
            total_tokens=tokens,
            cost_usd=cost_usd,
            cost_per_1k_prompt=pricing["prompt"],
            cost_per_1k_completion=0,
            session_id=session_id,
            endpoint=endpoint,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        logger.info(f"Recorded embedding: {model} - ${cost_usd:.6f} ({tokens} tokens)")
        
        return event
    
    def get_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None
    ) -> CostSummary:
        """Get cost summary for a time period."""
        if start_time is None:
            start_time = datetime.now() - timedelta(days=30)  # Last 30 days
        if end_time is None:
            end_time = datetime.now()
        
        # Filter events
        filtered_events = [
            e for e in self.events
            if start_time <= e.timestamp <= end_time
            and (session_id is None or e.session_id == session_id)
        ]
        
        summary = CostSummary(
            period_start=start_time,
            period_end=end_time,
            total_requests=len(filtered_events)
        )
        
        for event in filtered_events:
            summary.total_cost_usd += event.cost_usd
            summary.total_tokens += event.total_tokens
            
            # By event type
            if event.event_type == CostEventType.LLM_COMPLETION:
                summary.llm_completion_cost += event.cost_usd
            elif event.event_type == CostEventType.EMBEDDING:
                summary.embedding_cost += event.cost_usd
            elif event.event_type == CostEventType.SWARM_EXECUTION:
                summary.swarm_execution_cost += event.cost_usd
            elif event.event_type == CostEventType.API_CALL:
                summary.api_call_cost += event.cost_usd
            
            # By model
            if event.model not in summary.model_costs:
                summary.model_costs[event.model] = 0.0
                summary.model_tokens[event.model] = 0
            summary.model_costs[event.model] += event.cost_usd
            summary.model_tokens[event.model] += event.total_tokens
            
            # By provider
            if event.provider not in summary.provider_costs:
                summary.provider_costs[event.provider] = 0.0
            summary.provider_costs[event.provider] += event.cost_usd
        
        return summary
    
    def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily cost breakdown for the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        daily_costs = {}
        
        for event in self.events:
            event_date = event.timestamp.date()
            if start_date <= event_date <= end_date:
                date_str = event_date.isoformat()
                if date_str not in daily_costs:
                    daily_costs[date_str] = {
                        "date": date_str,
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "requests": 0,
                        "llm_cost": 0.0,
                        "embedding_cost": 0.0
                    }
                
                daily_costs[date_str]["total_cost"] += event.cost_usd
                daily_costs[date_str]["total_tokens"] += event.total_tokens
                daily_costs[date_str]["requests"] += 1
                
                if event.event_type == CostEventType.LLM_COMPLETION:
                    daily_costs[date_str]["llm_cost"] += event.cost_usd
                elif event.event_type == CostEventType.EMBEDDING:
                    daily_costs[date_str]["embedding_cost"] += event.cost_usd
        
        return list(daily_costs.values())
    
    def get_top_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top models by cost."""
        model_stats = {}
        
        for event in self.events:
            if event.model not in model_stats:
                model_stats[event.model] = {
                    "model": event.model,
                    "provider": event.provider,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "requests": 0
                }
            
            model_stats[event.model]["total_cost"] += event.cost_usd
            model_stats[event.model]["total_tokens"] += event.total_tokens
            model_stats[event.model]["requests"] += 1
        
        # Sort by cost and return top N
        sorted_models = sorted(
            model_stats.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )
        
        return sorted_models[:limit]
    
    async def start_background_save(self, interval_seconds: int = 60):
        """Start background task to periodically save events."""
        async def save_loop():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    self._save_events()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in background save: {e}")
        
        if self._save_task:
            self._save_task.cancel()
        
        self._save_task = asyncio.create_task(save_loop())
        logger.info(f"Started background cost tracking save (every {interval_seconds}s)")
    
    def stop_background_save(self):
        """Stop background save task."""
        if self._save_task:
            self._save_task.cancel()
            self._save_task = None
            logger.info("Stopped background cost tracking save")
    
    def save_now(self):
        """Immediately save events to storage."""
        self._save_events()


# Global singleton instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker