#!/usr/bin/env python3
"""
Comprehensive monitoring script for the Portkey + OpenRouter + Together AI setup.
This script verifies that all components are working and provides real-time status.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Load environment
load_dotenv('.env.local', override=True)

console = Console()

class PortkeySystemMonitor:
    """Monitor the complete Portkey system with all providers."""

    def __init__(self):
        self.portkey_key = os.getenv("PORTKEY_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.together_key = os.getenv("TOGETHER_API_KEY")

        self.status = {
            "portkey": "🔄 Checking...",
            "openrouter": "🔄 Checking...",
            "together": "🔄 Checking...",
            "models": {},
            "embeddings": "🔄 Checking...",
            "last_check": None
        }

        # Critical models to monitor
        self.critical_models = [
            {"name": "GPT-4o", "id": "openai/gpt-4o", "type": "chat"},
            {"name": "GPT-4o Mini", "id": "openai/gpt-4o-mini", "type": "chat"},
            {"name": "Claude 3.5 Sonnet", "id": "anthropic/claude-3.5-sonnet", "type": "chat"},
            {"name": "Claude 3 Haiku", "id": "anthropic/claude-3-haiku-20240307", "type": "chat"},
            {"name": "Qwen 2.5 Coder", "id": "qwen/qwen-2.5-coder-32b-instruct", "type": "chat"},
            {"name": "DeepSeek Coder", "id": "deepseek/deepseek-coder-v2", "type": "chat"},
            {"name": "Llama 3.2", "id": "meta-llama/llama-3.2-3b-instruct", "type": "chat"},
            {"name": "GLM-4.5", "id": "z-ai/glm-4.5", "type": "chat"},
            {"name": "Groq Llama", "id": "groq/llama-3.1-70b-versatile", "type": "chat"},
            {"name": "M2-BERT", "id": "togethercomputer/m2-bert-80M-8k-retrieval", "type": "embedding"}
        ]

    async def check_portkey_health(self) -> bool:
        """Check if Portkey gateway is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Simple health check using Portkey
                config = {
                    "provider": "openrouter",
                    "api_key": self.openrouter_key
                }

                response = await client.get(
                    "https://api.portkey.ai/v1/models",
                    headers={
                        "x-portkey-api-key": self.portkey_key,
                        "x-portkey-config": json.dumps(config)
                    }
                )

                if response.status_code == 200:
                    self.status["portkey"] = "✅ Online"
                    return True
                else:
                    self.status["portkey"] = f"⚠️ Status {response.status_code}"
                    return False
        except Exception as e:
            self.status["portkey"] = f"❌ Error: {str(e)[:30]}"
            return False

    async def check_openrouter_health(self) -> bool:
        """Check OpenRouter direct access."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}"
                    }
                )

                if response.status_code == 200:
                    models = response.json().get("data", [])
                    self.status["openrouter"] = f"✅ Online ({len(models)} models)"
                    return True
                else:
                    self.status["openrouter"] = f"⚠️ Status {response.status_code}"
                    return False
        except Exception as e:
            self.status["openrouter"] = f"❌ Error: {str(e)[:30]}"
            return False

    async def check_together_health(self) -> bool:
        """Check Together AI direct access."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.together.xyz/v1/models",
                    headers={
                        "Authorization": f"Bearer {self.together_key}"
                    }
                )

                if response.status_code == 200:
                    self.status["together"] = "✅ Online"
                    return True
                else:
                    self.status["together"] = f"⚠️ Status {response.status_code}"
                    return False
        except Exception as e:
            self.status["together"] = f"❌ Error: {str(e)[:30]}"
            return False

    async def test_model(self, model: dict[str, str]) -> bool:
        """Test a specific model through Portkey."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if model["type"] == "chat":
                    # Test chat model
                    config = {
                        "provider": "openrouter",
                        "api_key": self.openrouter_key,
                        "override_params": {
                            "headers": {
                                "HTTP-Referer": "http://localhost:3000",
                                "X-Title": "Sophia Intel AI"
                            }
                        }
                    }

                    response = await client.post(
                        "https://api.portkey.ai/v1/chat/completions",
                        headers={
                            "x-portkey-api-key": self.portkey_key,
                            "x-portkey-config": json.dumps(config),
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model["id"],
                            "messages": [{"role": "user", "content": "Say 'OK' in one word"}],
                            "max_tokens": 5,
                            "temperature": 0.1
                        }
                    )

                elif model["type"] == "embedding":
                    # Test embedding model
                    config = {
                        "provider": "together-ai",
                        "api_key": self.together_key
                    }

                    response = await client.post(
                        "https://api.portkey.ai/v1/embeddings",
                        headers={
                            "x-portkey-api-key": self.portkey_key,
                            "x-portkey-config": json.dumps(config),
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model["id"],
                            "input": "Test"
                        }
                    )

                if response.status_code == 200:
                    self.status["models"][model["name"]] = "✅"
                    return True
                else:
                    self.status["models"][model["name"]] = f"⚠️ {response.status_code}"
                    return False

        except Exception:
            self.status["models"][model["name"]] = "❌"
            return False

    async def test_all_models(self):
        """Test all critical models."""
        tasks = []
        for model in self.critical_models:
            tasks.append(self.test_model(model))

        results = await asyncio.gather(*tasks)
        return all(results)

    async def get_model_pricing(self) -> dict[str, Any]:
        """Get pricing information for popular models."""
        pricing = {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}"
                    }
                )

                if response.status_code == 200:
                    models = response.json().get("data", [])

                    # Get pricing for our critical models
                    for model in models:
                        model_id = model.get("id")
                        if any(m["id"] == model_id for m in self.critical_models):
                            pricing[model_id] = {
                                "prompt": model.get("pricing", {}).get("prompt"),
                                "completion": model.get("pricing", {}).get("completion"),
                                "context": model.get("context_length", 0)
                            }

        except Exception:
            pass

        return pricing

    def create_status_table(self) -> Table:
        """Create a status table for display."""
        table = Table(title="🔐 Portkey System Status", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        table.add_row("Portkey Gateway", self.status["portkey"])
        table.add_row("OpenRouter", self.status["openrouter"])
        table.add_row("Together AI", self.status["together"])

        return table

    def create_models_table(self) -> Table:
        """Create a models status table."""
        table = Table(title="🤖 Model Availability", show_header=True)
        table.add_column("Model", style="cyan")
        table.add_column("Status", style="green")

        for name, status in self.status["models"].items():
            table.add_row(name, status)

        return table

    async def continuous_monitor(self, interval: int = 30):
        """Continuously monitor the system."""
        console.print(Panel.fit(
            "[bold cyan]Portkey System Monitor[/bold cyan]\n"
            "Monitoring all components and models...",
            border_style="cyan"
        ))

        while True:
            # Update status
            await self.check_portkey_health()
            await self.check_openrouter_health()
            await self.check_together_health()
            await self.test_all_models()

            self.status["last_check"] = datetime.now().strftime("%H:%M:%S")

            # Clear and display
            console.clear()

            # Display header
            console.print(Panel.fit(
                f"[bold cyan]Portkey System Monitor[/bold cyan]\n"
                f"Last check: {self.status['last_check']}",
                border_style="cyan"
            ))

            # Display status tables
            console.logger.info(self.create_status_table())
            console.logger.info()
            console.logger.info(self.create_models_table())

            # Display summary
            all_good = (
                "✅" in self.status["portkey"] and
                "✅" in self.status["openrouter"] and
                "✅" in self.status["together"] and
                all("✅" in v for v in self.status["models"].values())
            )

            if all_good:
                console.print(Panel.fit(
                    "[bold green]✅ All Systems Operational[/bold green]\n"
                    "• 300+ models available via OpenRouter\n"
                    "• Embeddings available via Together AI\n"
                    "• Portkey gateway providing caching & observability",
                    border_style="green"
                ))
            else:
                issues = []
                if "✅" not in self.status["portkey"]:
                    issues.append("• Portkey gateway issue")
                if "✅" not in self.status["openrouter"]:
                    issues.append("• OpenRouter connection issue")
                if "✅" not in self.status["together"]:
                    issues.append("• Together AI connection issue")

                failed_models = [k for k, v in self.status["models"].items() if "✅" not in v]
                if failed_models:
                    issues.append(f"• {len(failed_models)} models unavailable")

                console.print(Panel.fit(
                    "[bold yellow]⚠️ Issues Detected[/bold yellow]\n" +
                    "\n".join(issues),
                    border_style="yellow"
                ))

            # Wait for next check
            console.logger.info(f"\nNext check in {interval} seconds... (Press Ctrl+C to exit)")
            await asyncio.sleep(interval)

    async def quick_test(self):
        """Run a quick test of all components."""
        console.print(Panel.fit(
            "[bold cyan]Quick System Test[/bold cyan]",
            border_style="cyan"
        ))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Test Portkey
            task = progress.add_task("Testing Portkey Gateway...", total=1)
            portkey_ok = await self.check_portkey_health()
            progress.update(task, completed=1)

            # Test OpenRouter
            task = progress.add_task("Testing OpenRouter...", total=1)
            openrouter_ok = await self.check_openrouter_health()
            progress.update(task, completed=1)

            # Test Together
            task = progress.add_task("Testing Together AI...", total=1)
            together_ok = await self.check_together_health()
            progress.update(task, completed=1)

            # Test Models
            task = progress.add_task("Testing Models...", total=len(self.critical_models))
            for model in self.critical_models:
                await self.test_model(model)
                progress.advance(task)

        # Display results
        console.logger.info()
        console.logger.info(self.create_status_table())
        console.logger.info()
        console.logger.info(self.create_models_table())

        # Get pricing info
        console.logger.info("\n[bold cyan]Fetching pricing information...[/bold cyan]")
        pricing = await self.get_model_pricing()

        if pricing:
            pricing_table = Table(title="💰 Model Pricing (per 1M tokens)")
            pricing_table.add_column("Model", style="cyan")
            pricing_table.add_column("Input", style="yellow")
            pricing_table.add_column("Output", style="yellow")
            pricing_table.add_column("Context", style="magenta")

            for model_id, info in pricing.items():
                model_name = next((m["name"] for m in self.critical_models if m["id"] == model_id), model_id)
                # Handle pricing which might be string or float
                prompt_val = info.get('prompt')
                completion_val = info.get('completion')

                if prompt_val and isinstance(prompt_val, (int, float)):
                    input_price = f"${float(prompt_val):.2f}"
                elif prompt_val:
                    input_price = str(prompt_val)
                else:
                    input_price = "N/A"

                if completion_val and isinstance(completion_val, (int, float)):
                    output_price = f"${float(completion_val):.2f}"
                elif completion_val:
                    output_price = str(completion_val)
                else:
                    output_price = "N/A"

                context = f"{info['context']:,}" if info.get('context') else "N/A"
                pricing_table.add_row(model_name, input_price, output_price, context)

            console.logger.info()
            console.logger.info(pricing_table)

        # Summary
        all_good = (
            portkey_ok and openrouter_ok and together_ok and
            all("✅" in v for v in self.status["models"].values())
        )

        console.logger.info()
        if all_good:
            console.print(Panel.fit(
                "[bold green]✅ All Systems Operational![/bold green]\n\n"
                "Your Portkey setup is fully functional:\n"
                "• Access to 300+ models via OpenRouter\n"
                "• High-quality embeddings via Together AI\n"
                "• Unified gateway with caching & observability\n"
                "• z-ai/glm-4.5 model available\n\n"
                "[dim]Run with --monitor for continuous monitoring[/dim]",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                "[bold red]❌ Issues Detected[/bold red]\n\n"
                "Please check the status table above for details.\n"
                "Common fixes:\n"
                "• Verify API keys in .env.local\n"
                "• Check network connectivity\n"
                "• Ensure providers are not experiencing outages",
                border_style="red"
            ))


async def main():
    """Main monitoring function."""
    import sys

    monitor = PortkeySystemMonitor()

    if "--monitor" in sys.argv or "-m" in sys.argv:
        # Continuous monitoring mode
        interval = 30
        if "--interval" in sys.argv:
            idx = sys.argv.index("--interval")
            if idx + 1 < len(sys.argv):
                interval = int(sys.argv[idx + 1])

        await monitor.continuous_monitor(interval)
    else:
        # Quick test mode
        await monitor.quick_test()

        console.logger.info("\n[dim]Tip: Run with --monitor for continuous monitoring[/dim]")
        console.logger.info("[dim]Example: python3 scripts/monitor_portkey_system.py --monitor --interval 60[/dim]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.logger.info("\n[yellow]Monitoring stopped by user[/yellow]")
