#!/usr/bin/env python3
"""
Update Models and LLM Strategy - INTERNAL USE ONLY
This script scrapes model information from OpenRouter API and updates the
Continue.dev configuration with optimal model strategy based on performance and cost.
Designed to be run as a scheduled GitHub Actions workflow.
"""
import argparse
import json
import logging
import os
from datetime import datetime
from typing import Dict, List
import requests
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("model_updates.log"), logging.StreamHandler()],
)
logger = logging.getLogger("model_updater")
# Constants
CONFIG_FILE = ".continue/config.json"
STRATEGY_FILE = ".continue/llm_strategy.json"
MAX_COST_THRESHOLD = 0.55  # $ per million tokens
PERFORMANCE_WEIGHT = 0.7
COST_WEIGHT = 0.3
API_URL = "https://openrouter.ai/api/v1/models"
def load_config() -> Dict:
    """Load the Continue.dev configuration file"""
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}
def save_config(config: Dict) -> bool:
    """Save the Continue.dev configuration file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Updated config saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False
def get_model_rankings() -> List[Dict]:
    """
    Get model rankings from OpenRouter API
    Returns a list of models with calculated scores
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in environment")
        return []
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        # Calculate scores based on formula
        models = []
        for model in data:
            tokens_processed = model.get("tokens_processed", 0)
            cost_per_million = model.get("pricing", {}).get("output", 0) * 1000000
            # Skip models exceeding our cost threshold
            if cost_per_million > MAX_COST_THRESHOLD * 1000000:
                continue
            if cost_per_million > 0:
                score = (tokens_processed * PERFORMANCE_WEIGHT) - (
                    cost_per_million * COST_WEIGHT
                )
            else:
                score = tokens_processed * PERFORMANCE_WEIGHT
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
        return models
    except Exception as e:
        logger.error(f"Error fetching model rankings: {e}")
        return []
def update_continue_config(models: List[Dict]) -> bool:
    """
    Update Continue.dev configuration with optimal models based on rankings
    Returns True if successful
    """
    if not models:
        logger.error("No models to update")
        return False
    try:
        config = load_config()
        if not config:
            return False
        # Map model types to categories
        model_categories = {
            "claude": "strategy",
            "gpt": "strategy",
            "gemini": "strategy",
            "qwen": "coding",
            "coder": "coding",
            "deepseek": "debug",
            "mistral": "debug",
            "llama": "local",
        }
        # Find best model for each category
        best_models = {}
        for model in models:
            model_id = model["id"].lower()
            for key, category in model_categories.items():
                if key in model_id and category not in best_models:
                    best_models[category] = model
        # Update model configurations
        if "models" in config:
            updated_models = []
            # First, update existing models if they match our categories
            for model in config["models"]:
                if "title" in model:
                    title = model["title"].lower()
                    for category in ["strategy", "coding", "debug", "local"]:
                        if category in title and category in best_models:
                            # Update this model with the best in category
                            best = best_models[category]
                            model["model"] = best["id"]
                            logger.info(f"Updated {model['title']} to use {best['id']}")
                            best_models.pop(category)  # Remove so we don't add it again
                    updated_models.append(model)
            # Add any remaining best models as new entries
            for category, model in best_models.items():
                category_title = category.capitalize()
                temp = (
                    0.3
                    if category == "strategy"
                    else (0.2 if category == "coding" else 0.1)
                )
                system_prompt = {
                    "strategy": "Deep Strategist: Use step-by-step reasoning to break down complex problems. Consider various approaches, analyzing pros and cons of each option.",
                    "coding": "Meticulous Coder: Create clean, maintainable code. Follow best practices like PEP8 for Python. Add explanatory comments. Focus on performance, security, and readability.",
                    "debug": "Precision Debugger: Identify and fix issues methodically. Provide step-by-step reproduction of issues, analyze root causes, and suggest the most minimal effective fix.",
                    "local": "Offline Helper: Provide assistance while working offline. Focus on practical solutions that don't require external API calls.",
                }.get(
                    category,
                    "Expert Assistant: Provide clear and helpful responses based on your expertise.",
                )
                new_model = {
                    "title": f"{category_title}Best",
                    "provider": "openrouter" if category != "local" else "ollama",
                    "model": model["id"] if category != "local" else "codellama:70b",
                    "completionOptions": {"temperature": temp, "maxTokens": 2000},
                    "systemPrompt": system_prompt,
                }
                updated_models.append(new_model)
                logger.info(
                    f"Added new model {new_model['title']} using {new_model['model']}"
                )
            config["models"] = updated_models
            # Save LLM strategy to a separate file for MCP server
            strategy_data = {
                "updated_at": datetime.now().isoformat(),
                "models": {m["id"]: m["score"] for m in models[:10]},
                "categories": {
                    category: best["id"] for category, best in best_models.items()
                },
                "formula": f"{PERFORMANCE_WEIGHT} * performance - {COST_WEIGHT} * cost",
                "max_cost_threshold": MAX_COST_THRESHOLD,
            }
            try:
                with open(STRATEGY_FILE, "w") as f:
                    json.dump(strategy_data, f, indent=2)
                logger.info(f"Saved LLM strategy to {STRATEGY_FILE}")
            except Exception as e:
                logger.error(f"Error saving strategy data: {e}")
            return save_config(config)
    except Exception as e:
        logger.error(f"Error updating Continue.dev config: {e}")
        return False
def self_audit() -> Dict:
    """
    Run a self-audit on the configuration to identify issues
    Returns audit results
    """
    config = load_config()
    issues = []
    recommendations = []
    if not config:
        issues.append("Could not load configuration")
        return {"issues": issues, "recommendations": recommendations}
    # Check models
    if "models" in config:
        models = config["models"]
        # Check for unused models
        used_models = set()
        if "tasks" in config:
            for task in config["tasks"]:
                if "model" in task:
                    used_models.add(task["model"])
        if "defaultModel" in config:
            used_models.add(config["defaultModel"])
        if "tabAutocompleteModel" in config:
            used_models.add(config["tabAutocompleteModel"])
        for model in models:
            if "title" in model and model["title"] not in used_models:
                issues.append(f"Unused model: {model['title']}")
                recommendations.append(
                    f"Consider removing unused model {model['title']} or assign it to tasks"
                )
    # Check fallbacks
    if "modelFallbacks" not in config:
        issues.append("No model fallbacks defined")
        recommendations.append("Add model fallbacks to ensure reliability")
    return {"issues": issues, "recommendations": recommendations}
def main():
    parser = argparse.ArgumentParser(
        description="Update model rankings and Continue.dev configuration"
    )
    parser.add_argument(
        "--audit", action="store_true", help="Run a self-audit on the configuration"
    )
    args = parser.parse_args()
    if args.audit:
        logger.info("Running self-audit...")
        audit_results = self_audit()
        if audit_results["issues"]:
            logger.warning(f"Found {len(audit_results['issues'])} issues:")
            for issue in audit_results["issues"]:
                logger.warning(f" - {issue}")
        else:
            logger.info("No issues found in configuration")
        if audit_results["recommendations"]:
            logger.info("Recommendations:")
            for rec in audit_results["recommendations"]:
                logger.info(f" - {rec}")
    else:
        logger.info("Fetching model rankings...")
        models = get_model_rankings()
        if models:
            logger.info(f"Found {len(models)} models")
            top_models = models[:5]
            logger.info("Top 5 models by score:")
            for i, model in enumerate(top_models):
                logger.info(
                    f"{i+1}. {model['name']} (ID: {model['id']}) - Score: {model['score']}"
                )
            logger.info("Updating Continue.dev configuration...")
            success = update_continue_config(models)
            if success:
                logger.info("Configuration updated successfully")
            else:
                logger.error("Failed to update configuration")
        else:
            logger.error("No models found")
if __name__ == "__main__":
    main()
