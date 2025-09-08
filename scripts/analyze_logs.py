#!/usr/bin/env python3
"""
Log Analyzer Background Script
SOLO DEVELOPER USE ONLY - NOT FOR DISTRIBUTION

Analyzes logs for errors, performance issues, and usage patterns.
Generates summaries and metrics for the dashboard.
"""

import argparse
import datetime
import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logs/analyze_logs.log",
    filemode="a",
)
logger = logging.getLogger("analyze_logs")

# Constants
LOG_FILES = {
    "mcp": "logs/mcp_server.log",
    "update_models": "logs/update_models.log",
    "memory_prune": "logs/memory_prune.log",
    "system_monitor": "logs/system_monitor.log",
}
ERROR_PATTERNS = [r"ERROR", r"Error:", r"Exception", r"Failed", r"Traceback", r"ConnectionError"]
PERFORMANCE_PATTERNS = [
    r"latency=(\d+)",
    r"took (\d+)ms",
    r"(\d+)ms to process",
    r"response time: (\d+)",
]
API_CALL_PATTERN = r"POST /api/([a-zA-Z_]+)"
TOKEN_USAGE_PATTERN = r"used (\d+) tokens"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB, truncate logs larger than this


def analyze_log_file(log_path: str) -> Dict[str, Any]:
    """
    Analyze a single log file for errors, performance, and usage patterns
    """
    if not os.path.exists(log_path):
        return {
            "status": "error",
            "message": f"Log file not found: {log_path}",
            "errors": 0,
            "api_calls": {},
            "performance": {},
        }

    try:
        # Check if log file is too large
        file_size = os.path.getsize(log_path)
        if file_size > MAX_LOG_SIZE:
            logger.warning(
                f"Log file {log_path} is too large ({file_size} bytes), analyzing only the last {MAX_LOG_SIZE} bytes"
            )

            with open(log_path, "rb") as f:
                f.seek(-min(file_size, MAX_LOG_SIZE), 2)
                log_content = f.read().decode("utf-8", errors="ignore")
        else:
            with open(log_path, encoding="utf-8", errors="ignore") as f:
                log_content = f.read()

        # Initialize counters
        error_count = 0
        api_calls = defaultdict(int)
        latencies = defaultdict(list)
        token_usages = defaultdict(list)

        # Process line by line
        lines = log_content.split("\n")
        for line in lines:
            # Check for errors
            if any(re.search(pattern, line) for pattern in ERROR_PATTERNS):
                error_count += 1

            # Check for API calls
            api_match = re.search(API_CALL_PATTERN, line)
            if api_match:
                api_endpoint = api_match.group(1)
                api_calls[api_endpoint] += 1

                # Try to extract latency for this API call
                for pattern in PERFORMANCE_PATTERNS:
                    latency_match = re.search(pattern, line)
                    if latency_match:
                        latencies[api_endpoint].append(int(latency_match.group(1)))
                        break

            # Check for token usage
            token_match = re.search(TOKEN_USAGE_PATTERN, line)
            if token_match:
                # Try to determine which model was used
                model = "unknown"
                model_patterns = [r"model=([a-zA-Z0-9-/]+)", r"using ([a-zA-Z0-9-/]+) model"]
                for pattern in model_patterns:
                    model_match = re.search(pattern, line)
                    if model_match:
                        model = model_match.group(1)
                        break

                tokens = int(token_match.group(1))
                token_usages[model].append(tokens)

        # Calculate performance metrics
        performance = {}
        for endpoint, latency_values in latencies.items():
            if latency_values:
                performance[endpoint] = {
                    "avg_latency_ms": sum(latency_values) / len(latency_values),
                    "max_latency_ms": max(latency_values),
                    "min_latency_ms": min(latency_values),
                    "p95_latency_ms": (
                        sorted(latency_values)[int(len(latency_values) * 0.95)]
                        if len(latency_values) >= 20
                        else None
                    ),
                }

        # Calculate token usage metrics
        token_metrics = {}
        for model, token_values in token_usages.items():
            if token_values:
                token_metrics[model] = {
                    "total_tokens": sum(token_values),
                    "avg_tokens": sum(token_values) / len(token_values),
                    "max_tokens": max(token_values),
                    "calls": len(token_values),
                }

        return {
            "status": "success",
            "errors": error_count,
            "api_calls": dict(api_calls),
            "performance": performance,
            "token_usage": token_metrics,
            "lines_processed": len(lines),
        }
    except Exception as e:
        logger.error(f"Error analyzing log file {log_path}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "errors": 0,
            "api_calls": {},
            "performance": {},
        }


def analyze_all_logs() -> Dict[str, Any]:
    """
    Analyze all log files and combine results
    """
    results = {}
    total_errors = 0

    for log_name, log_path in LOG_FILES.items():
        if os.path.exists(log_path):
            logger.info(f"Analyzing log file: {log_path}")
            log_results = analyze_log_file(log_path)
            results[log_name] = log_results
            total_errors += log_results.get("errors", 0)
        else:
            logger.warning(f"Log file not found: {log_path}")
            results[log_name] = {"status": "error", "message": "Log file not found"}

    # Combine API call data if multiple logs have it
    combined_api_calls = defaultdict(int)
    combined_token_usage = {}

    for log_results in results.values():
        for endpoint, count in log_results.get("api_calls", {}).items():
            combined_api_calls[endpoint] += count

        for model, metrics in log_results.get("token_usage", {}).items():
            if model not in combined_token_usage:
                combined_token_usage[model] = metrics.copy()
            else:
                combined_token_usage[model]["total_tokens"] += metrics.get("total_tokens", 0)
                combined_token_usage[model]["calls"] += metrics.get("calls", 0)
                combined_token_usage[model]["avg_tokens"] = (
                    combined_token_usage[model]["total_tokens"]
                    / combined_token_usage[model]["calls"]
                )
                combined_token_usage[model]["max_tokens"] = max(
                    combined_token_usage[model]["max_tokens"], metrics.get("max_tokens", 0)
                )

    # Calculate cost estimates if we have token usage data
    cost_estimates = {}
    model_costs = {
        "claude-sonnet": 8.0,  # $ per million tokens
        "qwen3-coder": 5.0,
        "deepseek": 0.0,
        "codellama": 0.0,
        "unknown": 6.5,  # average cost
    }

    for model, metrics in combined_token_usage.items():
        # Try to match model name to our known costs
        cost_key = next((k for k in model_costs if k in model.lower()), "unknown")
        cost_per_million = model_costs[cost_key]

        total_tokens = metrics.get("total_tokens", 0)
        cost = (total_tokens / 1000000) * cost_per_million

        cost_estimates[model] = {
            "cost_per_million": cost_per_million,
            "total_tokens": total_tokens,
            "estimated_cost": cost,
        }

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_errors": total_errors,
        "logs": results,
        "combined_api_calls": dict(combined_api_calls),
        "combined_token_usage": combined_token_usage,
        "cost_estimates": cost_estimates,
    }


def generate_summary(analysis: Dict[str, Any]) -> str:
    """
    Generate a text summary of the log analysis
    """
    total_errors = analysis.get("total_errors", 0)
    combined_api_calls = analysis.get("combined_api_calls", {})
    total_api_calls = sum(combined_api_calls.values())
    token_usage = analysis.get("combined_token_usage", {})
    total_tokens = sum(metrics.get("total_tokens", 0) for metrics in token_usage.values())
    cost_estimates = analysis.get("cost_estimates", {})
    total_cost = sum(estimate.get("estimated_cost", 0) for estimate in cost_estimates.values())

    # Find the most used API endpoint
    most_used_endpoint = max(combined_api_calls.items(), key=lambda x: x[1], default=("none", 0))

    summary = f"""
Log Analysis Summary ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})
--------------------------------------------------------------------------------
Total API Calls:    {total_api_calls}
Total Errors:       {total_errors}
Error Rate:         {(total_errors / total_api_calls * 100) if total_api_calls > 0 else 0:.2f}%
Most Used API:      {most_used_endpoint[0]} ({most_used_endpoint[1]} calls)
Total Tokens Used:  {total_tokens:,}
Estimated Cost:     ${total_cost:.4f}

Top API Endpoints:
"""

    # Add top 5 API endpoints
    sorted_endpoints = sorted(combined_api_calls.items(), key=lambda x: x[1], reverse=True)[:5]
    for endpoint, count in sorted_endpoints:
        percentage = (count / total_api_calls * 100) if total_api_calls > 0 else 0
        summary += f"  - {endpoint}: {count} calls ({percentage:.1f}%)\n"

    summary += "\nToken Usage by Model:\n"

    # Add token usage by model
    for model, metrics in token_usage.items():
        total = metrics.get("total_tokens", 0)
        avg = metrics.get("avg_tokens", 0)
        calls = metrics.get("calls", 0)
        summary += f"  - {model}: {total:,} total tokens across {calls} calls (avg: {avg:.1f})\n"

    if cost_estimates:
        summary += "\nCost Estimates:\n"
        for model, estimate in cost_estimates.items():
            cost = estimate.get("estimated_cost", 0)
            if cost > 0:
                summary += f"  - {model}: ${cost:.4f}\n"

    return summary


def save_analysis(analysis: Dict[str, Any], summary: str):
    """
    Save analysis results and summary to files
    """
    analysis_dir = Path("analysis")
    analysis_dir.mkdir(exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save JSON analysis
    with open(analysis_dir / f"log_analysis_{timestamp}.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Save latest analysis for dashboard
    with open(analysis_dir / "latest_log_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Save text summary
    with open(analysis_dir / f"log_summary_{timestamp}.txt", "w") as f:
        f.write(summary)

    # Save latest summary for dashboard
    with open(analysis_dir / "latest_log_summary.txt", "w") as f:
        f.write(summary)

    logger.info(f"Saved analysis results to {analysis_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze logs for errors, performance, and usage patterns"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save analysis results to file"
    )
    args = parser.parse_args()

    logger.info("Starting log analysis")

    # Run analysis
    analysis = analyze_all_logs()

    # Generate summary
    summary = generate_summary(analysis)

    # Print summary to console
    print(summary)

    # Save analysis unless disabled
    if not args.no_save:
        save_analysis(analysis, summary)

    logger.info("Log analysis completed")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    main()
