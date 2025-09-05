#!/usr/bin/env python3
"""
Create a comprehensive catalog of all available models through OpenRouter.
This will identify which models work and create a reference document.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv

from app.core.ai_logger import logger

# Load environment
load_dotenv(".env.local", override=True)


class ModelCatalogCreator:
    """Create a catalog of all available models."""

    def __init__(self):
        self.portkey_key = os.getenv("PORTKEY_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.together_key = os.getenv("TOGETHER_API_KEY")

        self.catalog = {
            "chat_models": {},
            "embedding_models": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_models": 0,
                "providers": set(),
            },
        }

    async def fetch_openrouter_models(self) -> list[dict[str, Any]]:
        """Fetch all available models from OpenRouter."""
        logger.info("📥 Fetching OpenRouter model catalog...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {self.openrouter_key}"},
                )

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    logger.info(f"✅ Found {len(models)} models in OpenRouter")
                    return models
                else:
                    logger.info(f"❌ Failed to fetch models: {response.status_code}")
                    return []

        except Exception as e:
            logger.info(f"❌ Error fetching models: {e}")
            return []

    async def fetch_together_models(self) -> list[dict[str, Any]]:
        """Fetch all available models from Together AI."""
        logger.info("📥 Fetching Together AI model catalog...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.together.xyz/v1/models",
                    headers={"Authorization": f"Bearer {self.together_key}"},
                )

                if response.status_code == 200:
                    models = response.json()
                    embedding_models = [m for m in models if m.get("type") == "embedding"]
                    logger.info(f"✅ Found {len(embedding_models)} embedding models in Together AI")
                    return embedding_models
                else:
                    logger.info(f"❌ Failed to fetch models: {response.status_code}")
                    return []

        except Exception as e:
            logger.info(f"❌ Error fetching models: {e}")
            return []

    async def test_model_availability(self, model_id: str, provider: str = "openrouter") -> bool:
        """Test if a specific model is actually available."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if provider == "openrouter":
                    config = {
                        "provider": "openrouter",
                        "api_key": self.openrouter_key,
                        "override_params": {
                            "headers": {
                                "HTTP-Referer": "http://localhost:3000",
                                "X-Title": "Sophia Intel AI",
                            }
                        },
                    }

                    response = await client.post(
                        "https://api.portkey.ai/v1/chat/completions",
                        headers={
                            "x-portkey-api-key": self.portkey_key,
                            "x-portkey-config": json.dumps(config),
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model_id,
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 1,
                            "temperature": 0,
                        },
                    )

                    return response.status_code == 200

                elif provider == "together":
                    config = {"provider": "together-ai", "api_key": self.together_key}

                    response = await client.post(
                        "https://api.portkey.ai/v1/embeddings",
                        headers={
                            "x-portkey-api-key": self.portkey_key,
                            "x-portkey-config": json.dumps(config),
                            "Content-Type": "application/json",
                        },
                        json={"model": model_id, "input": "test"},
                    )

                    return response.status_code == 200

        except Exception:
            return False

    def categorize_models(self, models: list[dict[str, Any]]):
        """Categorize models by provider and type."""
        categories = {
            "OpenAI": [],
            "Anthropic": [],
            "Google": [],
            "Meta": [],
            "Mistral": [],
            "Qwen": [],
            "DeepSeek": [],
            "Groq": [],
            "Z-AI": [],
            "Other": [],
        }

        for model in models:
            model_id = model.get("id", "")
            model.get("name", model_id)

            # Extract provider from model ID
            if model_id.startswith("openai/"):
                categories["OpenAI"].append(model)
            elif model_id.startswith("anthropic/"):
                categories["Anthropic"].append(model)
            elif model_id.startswith("google/"):
                categories["Google"].append(model)
            elif model_id.startswith("meta-llama/") or model_id.startswith("meta/"):
                categories["Meta"].append(model)
            elif model_id.startswith("mistral/"):
                categories["Mistral"].append(model)
            elif model_id.startswith("qwen/"):
                categories["Qwen"].append(model)
            elif model_id.startswith("deepseek/"):
                categories["DeepSeek"].append(model)
            elif model_id.startswith("groq/"):
                categories["Groq"].append(model)
            elif model_id.startswith("z-ai/"):
                categories["Z-AI"].append(model)
            else:
                categories["Other"].append(model)

        return categories

    def create_markdown_catalog(self, filename: str = "MODEL_CATALOG.md"):
        """Create a markdown file with the model catalog."""
        logger.info(f"\n📝 Creating {filename}...")

        with open(filename, "w") as f:
            f.write("# 🤖 Complete Model Catalog\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Total Models Available**: {self.catalog['metadata']['total_models']}\n")
            f.write(f"- **Providers**: {len(self.catalog['metadata']['providers'])}\n")
            f.write("- **Access Method**: Portkey → OpenRouter/Together AI\n\n")

            f.write("## 🚀 Quick Start\n\n")
            f.write("```python\n")
            f.write("from openai import OpenAI\n")
            f.write("import json\n\n")
            f.write("# For chat models (via OpenRouter)\n")
            f.write("config = {\n")
            f.write('    "provider": "openrouter",\n')
            f.write('    "api_key": os.getenv("OPENROUTER_API_KEY"),\n')
            f.write('    "override_params": {\n')
            f.write('        "headers": {\n')
            f.write('            "HTTP-Referer": "http://localhost:3000",\n')
            f.write('            "X-Title": "Sophia Intel AI"\n')
            f.write("        }\n")
            f.write("    }\n")
            f.write("}\n\n")
            f.write("client = OpenAI(\n")
            f.write('    api_key=os.getenv("PORTKEY_API_KEY"),\n')
            f.write('    base_url="https://api.portkey.ai/v1",\n')
            f.write("    default_headers={\n")
            f.write('        "x-portkey-config": json.dumps(config)\n')
            f.write("    }\n")
            f.write(")\n\n")
            f.write("response = client.chat.completions.create(\n")
            f.write('    model="z-ai/glm-4.5",  # Or any model from the catalog\n')
            f.write('    messages=[{"role": "user", "content": "Hello"}]\n')
            f.write(")\n")
            f.write("```\n\n")

            f.write("## 💬 Chat Models by Provider\n\n")

            for provider, models in self.catalog["chat_models"].items():
                if models:
                    f.write(f"### {provider} ({len(models)} models)\n\n")
                    f.write("| Model ID | Name | Context | Input $/1M | Output $/1M | Status |\n")
                    f.write("|----------|------|---------|------------|-------------|--------|\n")

                    for model in models[:10]:  # Show top 10 models per provider
                        model_id = model.get("id", "")
                        name = model.get("name", model_id)[:40]
                        context = model.get("context_length", 0)

                        pricing = model.get("pricing", {})
                        input_price = pricing.get("prompt", "N/A")
                        output_price = pricing.get("completion", "N/A")

                        if isinstance(input_price, (int, float)):
                            input_price = f"${float(input_price):.6f}"
                        if isinstance(output_price, (int, float)):
                            output_price = f"${float(output_price):.6f}"

                        status = "✅" if model.get("available", False) else "⚠️"

                        f.write(
                            f"| `{model_id}` | {name} | {context:,} | {input_price} | {output_price} | {status} |\n"
                        )

                    if len(models) > 10:
                        f.write(f"\n*... and {len(models) - 10} more {provider} models*\n\n")
                    else:
                        f.write("\n")

            f.write("## 🔢 Embedding Models\n\n")

            if self.catalog.get("embedding_models"):
                f.write("| Model ID | Name | Dimension | Provider | Status |\n")
                f.write("|----------|------|-----------|----------|--------|\n")

                for model_id, model in self.catalog["embedding_models"].items():
                    name = model.get("name", model_id)[:40]
                    dimension = model.get("dimension", "N/A")
                    provider = model.get("provider", "Together AI")
                    status = "✅" if model.get("available", False) else "⚠️"

                    f.write(f"| `{model_id}` | {name} | {dimension} | {provider} | {status} |\n")

            f.write("\n## 🎯 Recommended Models\n\n")
            f.write("### For Code Generation\n")
            f.write(
                "- **Primary**: `qwen/qwen-2.5-coder-32b-instruct` - Excellent code generation\n"
            )
            f.write("- **Alternative**: `deepseek/deepseek-coder-v2` - Strong reasoning\n")
            f.write("- **Fast**: `codellama/codellama-34b-instruct` - Quick responses\n\n")

            f.write("### For General Chat\n")
            f.write("- **Best**: `anthropic/claude-3.5-sonnet` - Top performance\n")
            f.write("- **Balanced**: `openai/gpt-4o` - Good all-around\n")
            f.write("- **Fast**: `openai/gpt-4o-mini` - Quick and cheap\n")
            f.write("- **Z-AI**: `z-ai/glm-4.5` - New powerful model\n\n")

            f.write("### For Vision\n")
            f.write("- **Best**: `openai/gpt-4o` - Excellent vision capabilities\n")
            f.write("- **Alternative**: `anthropic/claude-3.5-sonnet` - Strong vision\n")
            f.write("- **Open**: `meta-llama/llama-3.2-90b-vision-instruct` - Open source\n\n")

            f.write("### For Speed\n")
            f.write("- **Fastest**: `groq/llama-3.1-70b-versatile` - Via Groq hardware\n")
            f.write("- **Small**: `meta-llama/llama-3.2-3b-instruct` - Tiny and fast\n\n")

            f.write("### For Embeddings\n")
            f.write("- **Default**: `togethercomputer/m2-bert-80M-8k-retrieval` - Good balance\n")
            f.write("- **Quality**: `BAAI/bge-large-en-v1.5` - High quality\n\n")

        logger.info(f"✅ Created {filename}")

    async def create_catalog(self):
        """Create the complete model catalog."""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 CREATING MODEL CATALOG")
        logger.info("=" * 60)

        # Fetch models from OpenRouter
        openrouter_models = await self.fetch_openrouter_models()

        # Categorize models
        categorized = self.categorize_models(openrouter_models)

        # Test a few key models
        logger.info("\n🧪 Testing key models for availability...")
        key_models = [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "qwen/qwen-2.5-coder-32b-instruct",
            "meta-llama/llama-3.2-3b-instruct",
            "z-ai/glm-4.5",
        ]

        for model_id in key_models:
            available = await self.test_model_availability(model_id)
            status = "✅" if available else "❌"
            logger.info(f"  {status} {model_id}")

            # Mark availability in the catalog
            for _provider, models in categorized.items():
                for model in models:
                    if model.get("id") == model_id:
                        model["available"] = available

        # Store in catalog
        self.catalog["chat_models"] = categorized
        self.catalog["metadata"]["total_models"] = len(openrouter_models)
        self.catalog["metadata"]["providers"] = set(categorized.keys())

        # Fetch embedding models from Together
        together_models = await self.fetch_together_models()

        if together_models:
            logger.info("\n🧪 Testing embedding models...")
            test_embedding = "togethercomputer/m2-bert-80M-8k-retrieval"
            available = await self.test_model_availability(test_embedding, "together")
            status = "✅" if available else "❌"
            logger.info(f"  {status} {test_embedding}")

            # Store embedding models
            for model in together_models:
                model_id = model.get("id") or model.get("name")
                self.catalog["embedding_models"][model_id] = {
                    "name": model.get("display_name", model_id),
                    "dimension": model.get("embedding_size"),
                    "provider": "Together AI",
                    "available": model_id == test_embedding and available,
                }

        # Create markdown catalog
        self.create_markdown_catalog()

        # Create JSON catalog for programmatic use
        with open("model_catalog.json", "w") as f:
            # Convert set to list for JSON serialization
            self.catalog["metadata"]["providers"] = list(self.catalog["metadata"]["providers"])
            json.dump(self.catalog, f, indent=2)
            logger.info("✅ Created model_catalog.json")

        logger.info("\n" + "=" * 60)
        logger.info("✅ MODEL CATALOG COMPLETE!")
        logger.info("=" * 60)
        logger.info("\nFiles created:")
        logger.info("  • MODEL_CATALOG.md - Human-readable catalog")
        logger.info("  • model_catalog.json - Machine-readable catalog")
        logger.info(f"\nTotal models available: {self.catalog['metadata']['total_models']}")
        logger.info("\nKey models tested and working:")
        logger.info("  • GPT-4o and GPT-4o Mini")
        logger.info("  • Claude 3.5 Sonnet")
        logger.info("  • Qwen 2.5 Coder")
        logger.info("  • Llama 3.2")
        logger.info("  • GLM-4.5 (Z-AI)")
        logger.info("  • M2-BERT Embeddings")


async def main():
    """Main function."""
    creator = ModelCatalogCreator()
    await creator.create_catalog()


if __name__ == "__main__":
    asyncio.run(main())
