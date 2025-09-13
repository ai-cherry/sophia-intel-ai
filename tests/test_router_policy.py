import pytest

from router.top25 import ModelRouter, ModelInfo


def test_router_recency_and_caps_filters():
    r = ModelRouter(redis_url="redis://localhost:6379/15")  # isolated DB
    models = [
        ModelInfo(
            id="openai/gpt-4o",
            provider="openai",
            name="GPT-4o",
            weekly_token_share=0.5,
            capabilities=["tool_use", "structured_output"],
            context_length=128000,
            last_updated=r.MIN_LAST_UPDATED,
        ),
        ModelInfo(
            id="openai/gpt-3.5-turbo",
            provider="openai",
            name="GPT-3.5",
            weekly_token_share=0.4,
            capabilities=["structured_output"],
            context_length=128000,
            last_updated=r.MIN_LAST_UPDATED,
        ),
        ModelInfo(
            id="legacy/bad",
            provider="legacy",
            name="legacy",
            weekly_token_share=0.1,
            capabilities=["tool_use", "structured_output"],
            context_length=64000,
            last_updated=r.MIN_LAST_UPDATED,
        ),
    ]
    filtered = r._filter_models(models)
    ids = {m.id for m in filtered}
    assert "openai/gpt-4o" in ids
    assert "openai/gpt-3.5-turbo" not in ids  # missing tool_use and banned pattern
    assert "legacy/bad" not in ids  # context too short

