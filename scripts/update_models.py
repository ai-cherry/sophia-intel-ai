#!/usr/bin/env python3
"""
Model Updater Background Script
SOLO DEVELOPER USE ONLY - NOT FOR DISTRIBUTION

Periodically scrapes model information from OpenRouter and updates
Continue.dev configuration with performance-optimized model rankings.
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logs/update_models.log",
    filemode="a",
)
logger = logging.getLogger("update_models")

# Constants
CONTINUE_CONFIG_PATH = Path(".continue/config.json")
MODEL_SCORING_FORMULA = "(tokens_processed * 0.7) - (cost_per_million * 0.3)"
COST_THRESHOLD = 0.55  # $ per million tokens
LOCAL_MODEL = "meta-llama/CodeLlama-70b"


def get_model_rankings() -> List[Dict[str, Any]]:
    """
    Get model rankings from OpenRouter API
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY not set")
        return []

    try:
        logger.info("Fetching models from OpenRouter...")
        headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"}
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        data = response.json().get("data", [])

        # Calculate scores based on formula
        models = []
        for model in data:
            tokens_processed = model.get("tokens_processed", 0)
            cost_per_million = model.get("pricing", {}).get("output", 0) * 1000000

            if cost_per_million > 0:
                score = (tokens_processed * 0.7) - (cost_per_million * 0.3)
            else:
                score = tokens_processed * 0.7

            # Skip models that are too expensive
            if cost_per_million > COST_THRESHOLD * 1000000:
                logger.debug(
                    f"Skipping {model.get('id')}: too expensive (${cost_per_million/1000000:.4f}/1M tokens)"
                )
                continue

            models.append(
                {
                    "id": model.get("id", "unknown"),
                    "name": model.get("name", "Unknown Model"),
                    "tokens_processed": tokens_processed,
                    "cost_per_million": cost_per_million,
                    "score": score,
                    "context_length": model.get("context_length", 0),
                }
            )

        # Sort by score
        models.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Found {len(models)} models meeting criteria")

        # Save to cache
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)

        with open(cache_dir / "model_rankings.json", "w") as f:
            json.dump(models, f)

        return models
    except Exception as e:
        logger.error(f"Error fetching model rankings: {e}")

        # Try to load from cache
        try:
            cache_dir = Path("cache")
            if (cache_dir / "model_rankings.json").exists():
                with open(cache_dir / "model_rankings.json") as f:
                    return json.load(f)
        except Exception as cache_err:
            logger.error(f"Error loading cached rankings: {cache_err}")

        return []


def update_continue_config(models: List[Dict[str, Any]]) -> bool:
    """
    Update Continue.dev configuration with ranked models
    """
    if not CONTINUE_CONFIG_PATH.exists():
        logger.error(f"Continue config not found at {CONTINUE_CONFIG_PATH}")
        return False

    try:
        # Load existing config
        with open(CONTINUE_CONFIG_PATH) as f:
            config = json.load(f)

        if len(models) < 3:
            logger.error("Not enough models to update configuration")
            return False

        # Update config with top models
        # 1. Strategy: Claude Sonnet (temp 0.3) - "Deep Strategist" with CoT
        # 2. Coding: Qwen3 Coder (temp 0.2) - "Meticulous Coder" for precision
        # 3. Debug: DeepSeek (temp 0.1) - "Precision Debugger" for low-variance troubleshooting

        # Find appropriate models for each role
        strategy_model = next(
            (m for m in models if "claude" in m["id"].lower()), models[0]
        )
        coding_model = next(
            (
                m
                for m in models
                if "coder" in m["id"].lower() or "code" in m["id"].lower()
            ),
            models[0],
        )
        debug_model = next(
            (m for m in models if "deepseek" in m["id"].lower()), models[1]
        )

        # Update model configurations
        if "models" not in config:
            config["models"] = []

        # Remove existing models (keep non-OpenRouter ones)
        config["models"] = [
            m for m in config["models"] if not m.get("provider") == "openrouter"
        ]

        # Add updated models
        config["models"].extend(
            [
                {
                    "title": "Deep Strategist",
                    "provider": "openrouter",
                    "model": strategy_model["id"],
                    "completionOptions": {
                        "temperature": 0.3,
                        "topP": 0.8,
                        "presencePenalty": 0.1,
                        "frequencyPenalty": 0.1,
                    },
                },
                {
                    "title": "Meticulous Coder",
                    "provider": "openrouter",
                    "model": coding_model["id"],
                    "completionOptions": {
                        "temperature": 0.2,
                        "topP": 0.9,
                        "presencePenalty": 0.0,
                        "frequencyPenalty": 0.2,
                    },
                },
                {
                    "title": "Precision Debugger",
                    "provider": "openrouter",
                    "model": debug_model["id"],
                    "completionOptions": {
                        "temperature": 0.1,
                        "topP": 0.95,
                        "presencePenalty": 0.0,
                        "frequencyPenalty": 0.0,
                    },
                },
            ]
        )

        # Add local model as fallback if not already present
        if not any(m.get("provider") == "ollama" for m in config["models"]):
            config["models"].append(
                {
                    "title": "Local Fallback",
                    "provider": "ollama",
                    "model": "codellama:70b",
                    "completionOptions": {"temperature": 0.2},
                }
            )

        # Save updated config
        with open(CONTINUE_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        logger.info("Successfully updated Continue.dev configuration")
        return True
    except Exception as e:
        logger.error(f"Error updating Continue.dev configuration: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update model rankings and Continue.dev configuration"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force update even if recently updated"
    )
    args = parser.parse_args()

    logger.info("Starting model update process")

    # Check if update is needed
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)

    last_update_file = cache_dir / "last_model_update"
    current_time = time.time()

    if not args.force and last_update_file.exists():
        with open(last_update_file) as f:
            try:
                last_update = float(f.read().strip())
                hours_since_update = (current_time - last_update) / 3600

                if hours_since_update < 6:  # Update every 6 hours
                    logger.info(
                        f"Skipping update, last update was {hours_since_update:.1f} hours ago"
                    )
                    return
            except Exception:
                pass  # Continue with update if file is invalid

    # Get model rankings
    models = get_model_rankings()

    if not models:
        logger.error("No models returned, aborting update")
        return

    # Update Continue.dev config
    success = update_continue_config(models)

    if success:
        # Record update time
        with open(last_update_file, "w") as f:
            f.write(str(current_time))

        logger.info("Model update completed successfully")

        # Self-audit
        try:
            with open(CONTINUE_CONFIG_PATH) as f:
                config = json.load(f)

            # Check if config has expected models
            model_count = len(
                [
                    m
                    for m in config.get("models", [])
                    if m.get("provider") == "openrouter"
                ]
            )

            if model_count >= 3:
                logger.info(
                    f"Self-audit passed: {model_count} OpenRouter models configured"
                )
            else:
                logger.warning(
                    f"Self-audit warning: Only {model_count} OpenRouter models configured"
                )
        except Exception as e:
            logger.error(f"Error during self-audit: {e}")
    else:
        logger.error("Failed to update model configuration")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    main()
