"""
Tests for OpenRouter Top-25 Model Router
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from router.top25 import ModelRouter, ModelInfo


@pytest.fixture
def router():
    """Create router instance"""
    return ModelRouter(redis_url="redis://localhost:6379/0")


@pytest.mark.asyncio
async def test_fetch_top_models(router):
    """Test fetching top 25 models"""
    # Mock the scraper
    with patch.object(router, '_scrape_openrouter') as mock_scrape:
        mock_scrape.return_value = [
            ModelInfo(
                id=f"provider{i}/model{i}",
                provider=f"provider{i}",
                name=f"Model {i}",
                weekly_token_share=float(25-i),
                capabilities=["tool_use", "structured_output"],
                context_length=128000
            )
            for i in range(30)
        ]
        
        models = await router.fetch_top_models()
        
        # Should return exactly 25 models
        assert len(models) == 25
        
        # Should be sorted by token share
        for i in range(len(models) - 1):
            assert models[i].weekly_token_share >= models[i+1].weekly_token_share


def test_banlist_filtering(router):
    """Test banlist pattern matching"""
    # Test banned models
    banned_models = [
        "anthropic/claude-3-opus",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-3.5-turbo",
        "openai/gpt-4-0613",
        "google/gemini-1.5-pro"
    ]
    
    for model_id in banned_models:
        assert any(
            router._matches_pattern(model_id, pattern) 
            for pattern in router.BANLIST_PATTERNS
        )
    
    # Test allowed models
    allowed_models = [
        "anthropic/claude-4-sonnet-20250522",
        "openai/gpt-4o",
        "google/gemini-2.5-pro"
    ]
    
    for model_id in allowed_models:
        assert not any(
            router._matches_pattern(model_id, pattern) 
            for pattern in router.BANLIST_PATTERNS
        )


def test_task_mapping(router):
    """Test model selection for tasks"""
    # Mock cached models
    with patch.object(router, '_get_cached_models') as mock_cache:
        mock_cache.return_value = [
            ModelInfo(id="anthropic/claude-4-sonnet-20250522", provider="anthropic", name="Claude 4"),
            ModelInfo(id="x-ai/grok-code-fast-1", provider="x-ai", name="Grok Code"),
            ModelInfo(id="google/gemini-2.5-flash", provider="google", name="Gemini Flash"),
        ]
        
        # Test planning task
        model = router.get_model_for_task("planning")
        assert model == "anthropic/claude-4-sonnet-20250522"
        
        # Test codegen task
        model = router.get_model_for_task("codegen")
        assert model == "x-ai/grok-code-fast-1"
        
        # Test research task
        model = router.get_model_for_task("research")
        assert model == "google/gemini-2.5-flash"


def test_offline_fallback(router):
    """Test offline fallback models"""
    models = router._get_offline_models()
    
    # Should return predefined list
    assert len(models) == len(router.OFFLINE_FALLBACK)
    
    # All should have required capabilities
    for model in models:
        assert "tool_use" in model.capabilities
        assert "structured_output" in model.capabilities
        assert model.context_length >= 128000


@pytest.mark.asyncio
async def test_cache_operations(router):
    """Test cache read/write operations"""
    test_models = [
        ModelInfo(id="test/model1", provider="test", name="Test 1"),
        ModelInfo(id="test/model2", provider="test", name="Test 2"),
    ]
    
    # Test cache write
    router._cache_models(test_models)
    
    # Test cache read
    cached = router._get_cached_models()
    
    # If Redis is available, should return cached models
    # Otherwise will return None (memory cache test would need time mock)
    if router.cache_enabled:
        assert cached is not None
        assert len(cached) == len(test_models)


@pytest.mark.asyncio
async def test_refresh_cache(router):
    """Test cache refresh"""
    with patch.object(router, 'fetch_top_models') as mock_fetch:
        mock_fetch.return_value = []
        
        await router.refresh_cache()
        
        # Should call fetch_top_models
        mock_fetch.assert_called_once()


def test_get_task_type(router):
    """Test getting task type for a model"""
    assert router.get_task_type("anthropic/claude-4-sonnet-20250522") == "planning"
    assert router.get_task_type("x-ai/grok-code-fast-1") == "codegen"
    assert router.get_task_type("google/gemini-2.5-flash") == "research"
    assert router.get_task_type("unknown/model") == "general"


def test_check_banlist(router):
    """Test checking current models against banlist"""
    with patch.object(router, '_get_cached_models') as mock_cache:
        mock_cache.return_value = [
            ModelInfo(id="anthropic/claude-3-opus", provider="anthropic", name="Claude 3"),
            ModelInfo(id="openai/gpt-4o", provider="openai", name="GPT-4o"),
        ]
        
        banned = router.check_banlist()
        
        assert len(banned) == 1
        assert "anthropic/claude-3-opus" in banned
        assert "openai/gpt-4o" not in banned