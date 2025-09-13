"""
OpenRouter Top-25 Model Spider
Fetches and filters top weekly models from OpenRouter
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from redis import Redis
import structlog

logger = structlog.get_logger(__name__)


class ModelInfo(BaseModel):
    """Model information from OpenRouter"""
    id: str
    provider: str
    name: str
    weekly_token_share: float = Field(default=0.0)
    capabilities: List[str] = Field(default_factory=list)
    context_length: int = Field(default=128000)
    last_updated: Optional[datetime] = None
    status: str = Field(default="active")


class ModelRouter:
    """OpenRouter Top-25 model management"""
    MIN_LAST_UPDATED = datetime(2025, 6, 1)

    # Banlist patterns - legacy and deprecated models
    BANLIST_PATTERNS = [
        "anthropic/claude-3*",
        "anthropic/claude-3.5*",
        "openai/gpt-3.5*",
        "openai/gpt-4-0613*",
        "openai/gpt-4-turbo*",
        "google/gemini-1*",
        "google/gemini-1.5*",
    ]
    
    # Enhanced 2025 Task to Model Mapping
    TASK_MAPPING = {
        "planning": {
            "preferred": [
                "openai/o3-mini",  # NEW: 2025 reasoning model
                "anthropic/claude-4-sonnet-20250522",
                "deepseek/deepseek-r1",  # NEW: DeepSeek R1 for planning
                "google/gemini-2.5-pro",
                "openai/gpt-4o"
            ],
            "fallbacks": [
                "x-ai/grok-3-alpha",  # NEW: Grok-3 fallback
                "mistralai/mistral-small-3.1-24b-instruct-2503",
                "z-ai/glm-4.5",
                "openrouter/sonoma-dusk-alpha"
            ]
        },
        "codegen": {
            "preferred": [
                "deepseek/deepseek-r1",  # NEW: R1 excellent for coding
                "x-ai/grok-code-fast-1",
                "deepseek/deepseek-coder-v2.5",  # NEW: Latest coder
                "qwen/qwen3-30b-a3b-instruct-2507"
            ],
            "fallbacks": [
                "groq/llama-3.1-70b-versatile",  # NEW: Fast coding fallback
                "deepseek/deepseek-chat-v3-0324",
                "openai/gpt-4.1-mini-2025-04-14",
                "together/meta-llama-3.1-70b-instruct-turbo"  # NEW
            ]
        },
        "research": {
            "preferred": [
                "perplexity/sonar-large-32k-online",  # NEW: Real-time research
                "google/gemini-2.5-flash",
                "x-ai/grok-3-alpha",  # NEW: Real-time capabilities
                "google/gemini-2.5-flash-lite"
            ],
            "fallbacks": [
                "anthropic/claude-3.5-sonnet",  # Reliable research
                "z-ai/glm-4.5v",
                "openai/gpt-4o-mini"
            ]
        },
        "reasoning": {  # NEW: Dedicated reasoning category
            "preferred": [
                "openai/o3-mini",
                "deepseek/deepseek-r1", 
                "anthropic/claude-4-sonnet-20250522"
            ],
            "fallbacks": [
                "x-ai/grok-3-alpha",
                "anthropic/claude-3.5-sonnet"
            ]
        },
        "fast": {  # NEW: Speed-optimized category
            "preferred": [
                "groq/llama-3.1-70b-versatile",
                "groq/llama-3.1-8b-instant",
                "x-ai/grok-3-fast",
                "together/meta-llama-3.1-70b-instruct-turbo"
            ],
            "fallbacks": [
                "deepseek/deepseek-chat",
                "openai/gpt-4o-mini"
            ]
        },
        "cheap": {  # NEW: Cost-optimized category  
            "preferred": [
                "deepseek/deepseek-chat",
                "groq/llama-3.1-8b-instant",
                "together/meta-llama-3.1-8b-instruct-turbo",
                "mistral/ministral-8b-2410"
            ],
            "fallbacks": [
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku-20240307"
            ]
        }
    }
    
    # Offline fallback allowlist
    OFFLINE_FALLBACK = [
        "anthropic/claude-4-sonnet-20250522",
        "x-ai/grok-code-fast-1",
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
        "openai/gpt-4o",
        "qwen/qwen3-30b-a3b-instruct-2507",
        "deepseek/deepseek-chat-v3-0324",
        "z-ai/glm-4.5",
        "z-ai/glm-4.5v",
        "mistralai/mistral-small-3.1-24b-instruct-2503",
        "openrouter/sonoma-dusk-alpha"
    ]
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize router with optional Redis cache"""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.cache_key = "openrouter:top25:models"
        self.cache_ttl = 86400  # 24 hours
        
        try:
            self.redis = Redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            self.cache_enabled = True
        except Exception as e:
            logger.warning(f"Redis unavailable, using memory cache: {e}")
            self.cache_enabled = False
            self.memory_cache = {}
    
    async def fetch_top_models(self) -> List[ModelInfo]:
        """Fetch top 25 weekly models from OpenRouter"""
        # Check cache first
        cached = self._get_cached_models()
        if cached:
            logger.info(f"Using cached models: {len(cached)} found")
            return cached
        
        try:
            # Fetch from OpenRouter
            models = await self._scrape_openrouter()
            
            # Filter and sort
            filtered = self._filter_models(models)
            top25 = sorted(filtered, key=lambda m: m.weekly_token_share, reverse=True)[:25]
            
            # Cache results
            self._cache_models(top25)
            
            logger.info(f"Fetched {len(top25)} top models from OpenRouter")
            return top25
            
        except Exception as e:
            logger.error(f"Failed to fetch models, using offline fallback: {e}")
            return self._get_offline_models()
    
    async def _scrape_openrouter(self) -> List[ModelInfo]:
        """Scrape OpenRouter rankings page"""
        models: List[ModelInfo] = []
        
        timeout = httpx.Timeout(8.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try to fetch weekly rankings pages for global and programming
            try:
                rankings_resp = await client.get("https://openrouter.ai/models?o=top-weekly")
                rankings_soup = BeautifulSoup(rankings_resp.text, "html.parser")
            except Exception:
                rankings_soup = None
            try:
                prog_resp = await client.get("https://openrouter.ai/models?o=top-weekly&category=programming")
                prog_soup = BeautifulSoup(prog_resp.text, "html.parser")
            except Exception:
                prog_soup = None
            
            # Parse models (simplified - actual implementation would parse HTML)
            # For now, use API if available
            try:
                api_resp = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}"}
                )
                if api_resp.status_code == 200:
                    data = api_resp.json()
                    for model_data in data.get("data", []):
                        # Normalize fields defensively
                        mid = model_data.get("id", "")
                        name = model_data.get("name", mid)
                        provider = mid.split("/")[0] if "/" in mid else model_data.get("provider", "")
                        context = model_data.get("context_length") or model_data.get("context") or 128000
                        share = model_data.get("weekly_token_share") or model_data.get("token_share") or 0.0
                        last = model_data.get("last_updated") or model_data.get("updated_at")
                        try:
                            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00")) if isinstance(last, str) else None
                        except Exception:
                            last_dt = None
                        caps = model_data.get("capabilities") or []
                        # Some APIs expose modalities separately
                        modality = model_data.get("modality") or []
                        if isinstance(modality, str):
                            modality = [modality]
                        caps = list({*caps, *modality})

                        models.append(ModelInfo(
                            id=mid,
                            provider=provider,
                            name=name,
                            weekly_token_share=float(share) if share is not None else 0.0,
                            capabilities=caps,
                            context_length=int(context) if context is not None else 128000,
                            last_updated=last_dt,
                        ))
            except Exception as e:
                logger.warning(f"API fetch failed, using fallback: {e}")
                # Use offline fallback
                return self._get_offline_models()
        
        # Merge token shares from rankings pages if available
        try:
            merged: Dict[str, float] = {}
            def _extract_page(soup):
                if not soup:
                    return {}
                shares = {}
                # Look for model cards/rows with share data
                # Try multiple selectors for robustness
                selectors = [
                    # Common patterns on OpenRouter
                    ('div[data-model-id]', 'data-model-id', 'data-token-share'),
                    ('div.model-card', 'data-id', 'data-share'),
                    ('tr[data-model]', 'data-model', 'data-weekly-share'),
                    # Fallback: look for model links with share spans
                    ('a[href*="/models/"]', 'href', None)
                ]
                
                for selector, id_attr, share_attr in selectors:
                    for tag in soup.select(selector):
                        # Extract model ID
                        if id_attr == 'href':
                            href = tag.get('href', '')
                            if '/models/' in href:
                                mid = href.split('/models/')[-1].strip('/')
                            else:
                                continue
                        else:
                            mid = tag.get(id_attr)
                        
                        if not mid:
                            continue
                        
                        # Extract share value
                        if share_attr:
                            share_val = tag.get(share_attr)
                        else:
                            # Look for share in text (e.g., "15.2%")
                            share_text = tag.find(text=lambda t: '%' in str(t))
                            if share_text:
                                try:
                                    share_val = float(str(share_text).strip().rstrip('%')) / 100
                                except:
                                    share_val = None
                            else:
                                share_val = None
                        
                        try:
                            share_float = float(share_val) if share_val else None
                        except:
                            share_float = None
                        
                        if mid and share_float is not None:
                            shares[mid] = share_float
                
                return shares
            
            global_shares = _extract_page(rankings_soup) if rankings_soup else {}
            prog_shares = _extract_page(prog_soup) if prog_soup else {}
            
            # Merge: take max share per model across pages
            for mid, val in {**global_shares, **prog_shares}.items():
                merged[mid] = max(val, merged.get(mid, 0.0))
            
            if merged:
                logger.info(f"Merged token shares for {len(merged)} models")
                # Project shares onto models list
                by_id = {m.id: m for m in models}
                for mid, share in merged.items():
                    if mid in by_id:
                        by_id[mid].weekly_token_share = max(share, by_id[mid].weekly_token_share)
                
                # If some ranked models weren't in API list, add stubs
                for mid, share in merged.items():
                    if mid not in by_id and share > 0.01:  # Only add if significant share
                        models.append(ModelInfo(
                            id=mid,
                            provider=mid.split("/")[0] if "/" in mid else "",
                            name=mid,
                            weekly_token_share=share,
                            capabilities=["tool_use", "structured_output"],  # Assume capable if ranked
                            context_length=128000,
                        ))
        except Exception as e:
            logger.warning(f"Rankings merge failed: {e}")

        # De-duplicate by model id, keeping highest token share
        dedup: Dict[str, ModelInfo] = {}
        for m in models:
            if m.id in dedup:
                if m.weekly_token_share > dedup[m.id].weekly_token_share:
                    dedup[m.id] = m
            else:
                dedup[m.id] = m
        return list(dedup.values())
    
    def _filter_models(self, models: List[ModelInfo]) -> List[ModelInfo]:
        """Apply filters and banlist"""
        filtered = []
        
        for model in models:
            # Check banlist
            if any(self._matches_pattern(model.id, pattern) for pattern in self.BANLIST_PATTERNS):
                logger.debug(f"Rejected banned model: {model.id}")
                continue
        
            # Check capabilities
            required_caps = {"tool_use", "structured_output"}
            caps = set((model.capabilities or []))
            if not required_caps.issubset(caps):
                if model.id not in self.OFFLINE_FALLBACK:
                    logger.debug(f"Rejected model lacking capabilities: {model.id} -> {caps}")
                    continue

            # Check context length
            if model.context_length < 128000:
                if model.id not in self.OFFLINE_FALLBACK:
                    logger.debug(f"Rejected model with short context: {model.id}")
                    continue

            # Check last updated recency (reject stale models)
            if model.last_updated is not None and model.last_updated < self.MIN_LAST_UPDATED:
                if model.id not in self.OFFLINE_FALLBACK:
                    logger.debug(f"Rejected stale model (last_updated={model.last_updated.isoformat()}): {model.id}")
                    continue

            # Check deprecated status
            if model.status == "deprecated":
                logger.debug(f"Rejected deprecated model: {model.id}")
                continue
            
            filtered.append(model)
        
        return filtered
    
    def _matches_pattern(self, model_id: str, pattern: str) -> bool:
        """Check if model ID matches banlist pattern"""
        import fnmatch
        return fnmatch.fnmatch(model_id, pattern)
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get best model for a task type"""
        mapping = self.TASK_MAPPING.get(task_type, self.TASK_MAPPING["planning"])
        
        # Try preferred models first
        models = self._get_cached_models() or self._get_offline_models()
        model_ids = [m.id for m in models]
        
        for preferred in mapping["preferred"]:
            if preferred in model_ids:
                return preferred
        
        # Try fallbacks
        for fallback in mapping["fallbacks"]:
            if fallback in model_ids:
                return fallback
        
        # Default to first available
        return models[0].id if models else "openai/gpt-4o"
    
    def get_task_type(self, model_id: str) -> str:
        """Get task type for a model"""
        for task_type, mapping in self.TASK_MAPPING.items():
            if model_id in mapping["preferred"] or model_id in mapping["fallbacks"]:
                return task_type
        return "general"
    
    def get_model_for_mode(self, mode: str) -> str:
        """Get best model for a provider mode (reasoning, fast, cheap, etc.)"""
        if mode in self.TASK_MAPPING:
            mapping = self.TASK_MAPPING[mode]
            
            # Try preferred models first
            models = self._get_cached_models() or self._get_offline_models()
            model_ids = [m.id for m in models]
            
            for preferred in mapping["preferred"]:
                if preferred in model_ids:
                    return preferred
            
            # Try fallbacks
            for fallback in mapping["fallbacks"]:
                if fallback in model_ids:
                    return fallback
        
        # Default fallback
        return "openai/gpt-4o"
    
    def get_reasoning_models(self) -> List[str]:
        """Get all reasoning-capable models for complex tasks"""
        return self.TASK_MAPPING["reasoning"]["preferred"] + self.TASK_MAPPING["reasoning"]["fallbacks"]
    
    def get_fast_models(self) -> List[str]:
        """Get all speed-optimized models"""
        return self.TASK_MAPPING["fast"]["preferred"] + self.TASK_MAPPING["fast"]["fallbacks"]
    
    def get_cheap_models(self) -> List[str]:
        """Get all cost-optimized models"""
        return self.TASK_MAPPING["cheap"]["preferred"] + self.TASK_MAPPING["cheap"]["fallbacks"]
    
    def _get_cached_models(self) -> Optional[List[ModelInfo]]:
        """Get models from cache"""
        if self.cache_enabled:
            try:
                data = self.redis.get(self.cache_key)
                if data:
                    models_data = json.loads(data)
                    return [ModelInfo(**m) for m in models_data]
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        elif self.memory_cache:
            cache_time, models = self.memory_cache.get("models", (None, None))
            if cache_time and (datetime.now() - cache_time).seconds < self.cache_ttl:
                return models
        
        return None
    
    def _cache_models(self, models: List[ModelInfo]):
        """Cache models"""
        models_data = [m.model_dump() for m in models]
        
        if self.cache_enabled:
            try:
                self.redis.setex(
                    self.cache_key,
                    self.cache_ttl,
                    json.dumps(models_data, default=str)
                )
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
        else:
            self.memory_cache["models"] = (datetime.now(), models)
    
    def _get_offline_models(self) -> List[ModelInfo]:
        """Get offline fallback models"""
        return [
            ModelInfo(
                id=model_id,
                provider=model_id.split("/")[0],
                name=model_id,
                capabilities=["tool_use", "structured_output"],
                context_length=128000
            )
            for model_id in self.OFFLINE_FALLBACK
        ]
    
    async def refresh_cache(self):
        """Force refresh of model cache"""
        if self.cache_enabled:
            self.redis.delete(self.cache_key)
        else:
            self.memory_cache.clear()
        
        await self.fetch_top_models()
    
    def check_banlist(self) -> List[str]:
        """Check for any banned models in current list"""
        models = self._get_cached_models() or []
        banned = []
        
        for model in models:
            for pattern in self.BANLIST_PATTERNS:
                if self._matches_pattern(model.id, pattern):
                    banned.append(model.id)
                    break
        
        return banned

    def analyze(self) -> Dict[str, Any]:
        """Return a report of current model list against policy filters."""
        result = {
            "total": 0,
            "banned": 0,
            "short_context": 0,
            "missing_caps": 0,
            "stale": 0,
        }
        models = self._get_cached_models() or []
        result["total"] = len(models)
        for m in models:
            if any(self._matches_pattern(m.id, p) for p in self.BANLIST_PATTERNS):
                result["banned"] += 1
            if (m.capabilities is None) or (not {"tool_use", "structured_output"}.issubset(set(m.capabilities))):
                if m.id not in self.OFFLINE_FALLBACK:
                    result["missing_caps"] += 1
            if m.context_length < 128000:
                if m.id not in self.OFFLINE_FALLBACK:
                    result["short_context"] += 1
            if m.last_updated is not None and m.last_updated < self.MIN_LAST_UPDATED:
                if m.id not in self.OFFLINE_FALLBACK:
                    result["stale"] += 1
        return result

    def analyze_verbose(self) -> List[Dict[str, Any]]:
        """Return per-model diagnostics detailing which filters pass/fail."""
        out: List[Dict[str, Any]] = []
        models = self._get_cached_models() or []
        for m in models:
            caps = set(m.capabilities or [])
            banned = any(self._matches_pattern(m.id, p) for p in self.BANLIST_PATTERNS)
            missing_caps = not {"tool_use", "structured_output"}.issubset(caps)
            short_ctx = (m.context_length or 0) < 128000
            stale = m.last_updated is not None and m.last_updated < self.MIN_LAST_UPDATED
            out.append({
                "id": m.id,
                "provider": m.provider,
                "share": m.weekly_token_share,
                "banned": banned,
                "missing_caps": missing_caps and (m.id not in self.OFFLINE_FALLBACK),
                "short_context": short_ctx and (m.id not in self.OFFLINE_FALLBACK),
                "stale": stale and (m.id not in self.OFFLINE_FALLBACK),
                "last_updated": m.last_updated.isoformat() if m.last_updated else None,
            })
        return out


class ModelScheduler:
    """Scheduler for periodic model refresh"""
    
    def __init__(self, router: ModelRouter):
        self.router = router
        self.refresh_interval = 86400  # 24 hours
        self.running = False
    
    async def start(self):
        """Start scheduler"""
        self.running = True
        logger.info("Model scheduler started")
        
        while self.running:
            try:
                # Refresh models
                await self.router.refresh_cache()
                logger.info("Model cache refreshed by scheduler")
                
                # Wait for next refresh
                await asyncio.sleep(self.refresh_interval)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        logger.info("Model scheduler stopped")
