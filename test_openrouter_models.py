#!/usr/bin/env python3
"""Test script for OpenRouter Model Mix configuration.

This script tests the performance of different OpenRouter models
for various tasks to help optimize the model mix.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai package...")
    os.system("pip install openai")
    from openai import OpenAI


class ModelTester:
    """Tests different OpenRouter models for performance comparison."""

    def __init__(self):
        """Initialize the tester with API key from GitHub Codespaces secret."""
        # Get API key from environment (set by GitHub Codespaces secret)
        self.api_key = os.environ.get("OPENROUTER_API_KEY")

        if not self.api_key:
            print("Error: OPENROUTER_API_KEY not found in environment.")
            print("Please set up your GitHub Codespaces secret as described in:")
            print("setup_codespaces_secrets.md")
            sys.exit(1)

        # Initialize OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        # Model configurations
        self.models = {
            "claude-sonnet-4": {
                "id": "anthropic/claude-sonnet-4",
                "description": "Most powerful reasoning",
            },
            "gemini-2.5-flash": {
                "id": "google/gemini-2.5-flash",
                "description": "Fast generation",
            },
            "deepseek-v3-0324": {
                "id": "deepseek/deepseek-v3-0324",
                "description": "Cost-effective",
            },
            "qwen3-coder": {
                "id": "qwen/qwen3-coder",
                "description": "Specialized for coding",
            },
        }

    def test_model(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Test a specific model with the given prompt."""
        model_id = self.models[model_name]["id"]
        start_time = time.time()

        try:
            # Call the API
            response = self.client.chat.completions.create(
                model=model_id, messages=[{"role": "user", "content": prompt}]
            )

            end_time = time.time()
            response_text = response.choices[0].message.content

            result = {
                "model": model_name,
                "description": self.models[model_name]["description"],
                "success": True,
                "response_time": end_time - start_time,
                "response_length": len(response_text),
                "response_preview": (
                    response_text[:100] + "..."
                    if len(response_text) > 100
                    else response_text
                ),
            }

            return result

        except Exception as e:
            end_time = time.time()
            return {
                "model": model_name,
                "description": self.models[model_name]["description"],
                "success": False,
                "error": str(e),
                "response_time": end_time - start_time,
            }

    def test_all_models(self, prompt: str) -> List[Dict[str, Any]]:
        """Test all models with the given prompt."""
        results = []
        for model_name in self.models:
            print(f"Testing {model_name}...")
            result = self.test_model(model_name, prompt)
            results.append(result)
        return results

    def benchmark(self, prompts: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """Run benchmarks with different prompts."""
        benchmarks = {}
        for task_name, prompt in prompts.items():
            print(f"\nRunning benchmark for task: {task_name}")
            benchmarks[task_name] = self.test_all_models(prompt)
        return benchmarks

    def print_results(self, benchmark_results: Dict[str, List[Dict[str, Any]]]) -> None:
        """Print benchmark results in a readable format."""
        print("\n==== BENCHMARK RESULTS ====\n")

        for task_name, results in benchmark_results.items():
            print(f"\n--- Task: {task_name} ---\n")

            # Sort by response time (fastest first)
            sorted_results = sorted(
                results, key=lambda x: x.get("response_time", float("inf"))
            )

            for result in sorted_results:
                model = result["model"]
                desc = result["description"]
                success = "✅" if result.get("success", False) else "❌"

                if success == "✅":
                    time_ms = int(result["response_time"] * 1000)
                    length = result["response_length"]
                    print(f"{success} {model} ({desc}): {time_ms}ms, {length} chars")
                    print(f"   Preview: {result.get('response_preview', 'N/A')}")
                else:
                    time_ms = int(result["response_time"] * 1000)
                    error = result.get("error", "Unknown error")
                    print(f"{success} {model} ({desc}): {time_ms}ms - Error: {error}")

        print("\n==== MODEL RECOMMENDATIONS ====\n")

        for task_name, results in benchmark_results.items():
            successful_results = [r for r in results if r.get("success", False)]

            if not successful_results:
                print(f"Task: {task_name} - No successful models")
                continue

            # Find fastest model
            fastest = min(
                successful_results, key=lambda x: x.get("response_time", float("inf"))
            )

            # Find most detailed response (by length)
            most_detailed = max(
                successful_results, key=lambda x: x.get("response_length", 0)
            )

            print(f"Task: {task_name}")
            print(
                f"  Fastest: {fastest['model']} ({int(fastest['response_time'] * 1000)}ms)"
            )
            print(
                f"  Most detailed: {most_detailed['model']} ({most_detailed['response_length']} chars)"
            )


def main():
    """Main function to run benchmarks."""
    parser = argparse.ArgumentParser(description="Test OpenRouter models")
    parser.add_argument("--save", help="Save results to specified JSON file")
    args = parser.parse_args()

    # Create test prompts for different tasks
    prompts = {
        "code_generation": "Write a Python function to find all prime numbers up to n using the Sieve of Eratosthenes algorithm.",
        "code_explanation": "Explain how Promise.all works in JavaScript with examples of error handling.",
        "system_architecture": "Design a microservice architecture for an e-commerce website with high availability requirements.",
        "api_design": "Create a REST API specification for a task management system with users, tasks, and projects.",
    }

    tester = ModelTester()
    results = tester.benchmark(prompts)
    tester.print_results(results)

    if args.save:
        with open(args.save, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.save}")


if __name__ == "__main__":
    main()
