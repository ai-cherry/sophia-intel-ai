"""
Tests for UltimateModelRouter
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sophia.core.ultimate_model_router import UltimateModelRouter, ModelConfig, TaskType

class TestUltimateModelRouter:
    """Test cases for UltimateModelRouter."""

    def test_router_initialization(self):
        """Test that router initializes correctly."""
        router = UltimateModelRouter()
        assert router is not None
        assert isinstance(router.model_registry, dict)
        assert len(router.model_registry) > 0

    def test_select_model_returns_config(self):
        """Test that select_model returns a valid ModelConfig."""
        router = UltimateModelRouter()
        
        # Mock environment variable for testing
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            config = router.select_model(TaskType.CODE_GENERATION.value)
            assert isinstance(config, ModelConfig)
            assert config.provider in {"openai", "anthropic", "google", "groq", "deepseek"}
            assert config.quality_rank >= 1

    def test_select_model_invalid_task_type(self):
        """Test that select_model raises error for invalid task type."""
        router = UltimateModelRouter()
        
        with pytest.raises(ValueError, match="No models configured for task_type"):
            router.select_model("invalid_task_type")

    def test_select_model_no_api_keys(self):
        """Test that select_model raises error when no API keys are available."""
        router = UltimateModelRouter()
        
        # Clear all relevant environment variables
        env_vars_to_clear = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", 
            "GROQ_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY"
        ]
        
        with patch.dict(os.environ, {var: "" for var in env_vars_to_clear}, clear=False):
            with pytest.raises(EnvironmentError, match="No API keys found"):
                router.select_model(TaskType.CODE_GENERATION.value)

    def test_get_available_models(self):
        """Test getting available models for a task type."""
        router = UltimateModelRouter()
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            available = router.get_available_models(TaskType.CODE_GENERATION.value)
            assert isinstance(available, list)
            assert len(available) >= 1
            assert all(isinstance(model, ModelConfig) for model in available)

    def test_get_model_info(self):
        """Test getting model information."""
        router = UltimateModelRouter()
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            info = router.get_model_info(TaskType.CODE_GENERATION.value)
            assert isinstance(info, dict)
            assert "task_type" in info
            assert "total_models" in info
            assert "available_models" in info
            assert "models" in info
            assert info["task_type"] == TaskType.CODE_GENERATION.value

    @pytest.mark.asyncio
    async def test_call_model_missing_api_key(self):
        """Test that call_model raises error for missing API key."""
        router = UltimateModelRouter()
        config = ModelConfig("test", "test-model", 1, 1000, 0.001, "MISSING_API_KEY")
        
        with pytest.raises(EnvironmentError, match="Missing API key"):
            await router.call_model(config, "test prompt")

    @pytest.mark.asyncio
    async def test_call_model_unsupported_provider(self):
        """Test that call_model raises error for unsupported provider."""
        router = UltimateModelRouter()
        config = ModelConfig("unsupported", "test-model", 1, 1000, 0.001, "TEST_API_KEY")
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            with pytest.raises(NotImplementedError, match="Provider unsupported not yet implemented"):
                await router.call_model(config, "test prompt")

    def test_task_type_enum(self):
        """Test that TaskType enum has expected values."""
        expected_types = [
            "code_generation", "research", "deployment", 
            "creative", "reasoning", "analysis"
        ]
        
        for task_type in expected_types:
            assert hasattr(TaskType, task_type.upper())
            assert TaskType[task_type.upper()].value == task_type

    def test_model_config_dataclass(self):
        """Test ModelConfig dataclass functionality."""
        config = ModelConfig(
            provider="test",
            model_name="test-model",
            quality_rank=1,
            max_tokens=1000,
            cost_per_1k=0.001,
            api_key_env_var="TEST_KEY"
        )
        
        assert config.provider == "test"
        assert config.model_name == "test-model"
        assert config.quality_rank == 1
        assert config.max_tokens == 1000
        assert config.cost_per_1k == 0.001
        assert config.api_key_env_var == "TEST_KEY"
        assert config.temperature_default == 0.3  # default value

    def test_all_task_types_have_models(self):
        """Test that all task types have at least one model configured."""
        router = UltimateModelRouter()
        
        for task_type in TaskType:
            models = router.model_registry.get(task_type.value, [])
            assert len(models) > 0, f"No models configured for {task_type.value}"
            
            # Check that models are sorted by quality rank
            for i in range(len(models) - 1):
                assert models[i].quality_rank <= models[i + 1].quality_rank

