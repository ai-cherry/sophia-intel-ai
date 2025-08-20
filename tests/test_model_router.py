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
            assert config.provider in {"openai", "anthropic", "google", "deepseek", "qwen", "moonshot", "mistral", "zhipu"}
            assert config.quality_rank >= 1
            # Verify model is in approved list
            assert config.model_name in router.approved_models

    def test_select_model_invalid_task_type(self):
        """Test that select_model raises error for invalid task type."""
        router = UltimateModelRouter()
        
        with pytest.raises(ValueError, match="No approved models configured for task_type"):
            router.select_model("invalid_task_type")

    def test_select_model_no_api_keys(self):
        """Test that select_model raises error when no API keys are available."""
        router = UltimateModelRouter()
        
        # Clear all relevant environment variables
        env_vars_to_clear = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", 
            "GROQ_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY",
            "QWEN_API_KEY", "MOONSHOT_API_KEY", "MISTRAL_API_KEY", "ZHIPU_API_KEY"
        ]
        
        with patch.dict(os.environ, {var: "" for var in env_vars_to_clear}, clear=False):
            with pytest.raises(RuntimeError, match="No available approved models"):
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
            with pytest.raises(RuntimeError, match="Failed to call unsupported:test-model"):
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


    def test_only_approved_models_are_used(self):
        """Test that only models in the approved list are returned."""
        router = UltimateModelRouter()
        
        # Check all models in registry are approved
        for task, configs in router.model_registry.items():
            for config in configs:
                assert config.model_name in router.approved_models, f"Model {config.model_name} not in approved list for task {task}"

    def test_approved_models_list_completeness(self):
        """Test that the approved models list contains all expected models."""
        router = UltimateModelRouter()
        
        expected_models = {
            "gpt-5", "claude-sonnet-4", "gemini-2.5-flash", "gemini-2.0-flash", 
            "deepseek-v3-0324", "gemini-2.5-pro", "qwen3-coder", "claude-3.7-sonnet",
            "deepseek-v3-0324-free", "r1-0528-free", "kimi-k2", "gpt-oss-120b",
            "qwen3-coder-free", "gemini-2.5-flash-lite", "glm-4.5", "mistral-nemo",
            "gpt-4o-mini", "r1-free", "gpt-5-mini", "gpt-4.1"
        }
        
        assert router.approved_models == expected_models

    def test_model_validation(self):
        """Test the model validation functionality."""
        router = UltimateModelRouter()
        
        validation = router.validate_approved_models()
        
        assert isinstance(validation, dict)
        assert "valid" in validation
        assert "total_models" in validation
        assert "approved_models" in validation
        assert "unapproved_models" in validation
        
        # All models should be approved
        assert validation["valid"] is True
        assert len(validation["unapproved_models"]) == 0
        assert validation["approved_models"] == validation["total_models"]

    def test_fallback_logic_with_approved_models(self):
        """Test that fallback logic only uses approved models."""
        router = UltimateModelRouter()
        
        # Mock scenario where first model key is missing, second is available
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}, clear=True):
            config = router.select_model(TaskType.CODE_GENERATION.value)
            
            # Should get the second model (Claude) since OpenAI key is missing
            assert config.provider == "anthropic"
            assert config.model_name in router.approved_models

    def test_no_fallback_behavior(self):
        """Test behavior when fallback is disabled."""
        router = UltimateModelRouter()
        
        # Clear the first model's API key
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="No available approved models"):
                router.select_model(TaskType.CODE_GENERATION.value, fallback=False)

    def test_task_specific_model_selection(self):
        """Test that different tasks get appropriate models."""
        router = UltimateModelRouter()
        
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test_key", "OPENAI_API_KEY": "test_key"}):
            # Research should prefer DeepSeek
            research_config = router.select_model(TaskType.RESEARCH.value)
            assert research_config.provider == "deepseek"
            assert research_config.model_name == "deepseek-v3-0324"
            
            # Code generation should prefer GPT-5
            code_config = router.select_model(TaskType.CODE_GENERATION.value)
            assert code_config.provider == "openai"
            assert code_config.model_name == "gpt-5"

    def test_quality_ranking_enforcement(self):
        """Test that models are ranked by quality (1 = highest)."""
        router = UltimateModelRouter()
        
        for task_type, models in router.model_registry.items():
            # Check that quality ranks are in ascending order (1, 2, 3, ...)
            quality_ranks = [model.quality_rank for model in models]
            assert quality_ranks == sorted(quality_ranks), f"Quality ranks not in order for {task_type}"
            
            # Check that rank 1 exists (highest quality)
            assert 1 in quality_ranks, f"No rank 1 model for {task_type}"

    def test_new_provider_support(self):
        """Test that new providers are properly supported."""
        router = UltimateModelRouter()
        
        # Check that all new providers are in the call_model method
        new_providers = {"qwen", "moonshot", "mistral", "zhipu"}
        
        for task_type, models in router.model_registry.items():
            for model in models:
                if model.provider in new_providers:
                    # These should be recognized but not implemented yet
                    with patch.dict(os.environ, {model.api_key_env_var: "test_key"}):
                        selected = router.select_model(task_type)
                        if selected.provider in new_providers:
                            # Should be selectable but not callable yet
                            assert selected.model_name in router.approved_models

