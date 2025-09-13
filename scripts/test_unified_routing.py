#!/usr/bin/env python3
"""
Test Unified Model Routing Across All Systems
==============================================
Shows how your centralized configuration controls all three systems
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent.parent))

from config.model_manager import get_model_manager, get_system_config

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}\n")

def test_litellm_squad():
    """Show LiteLLM Squad configuration"""
    print_section("LiteLLM SQUAD CONFIGURATION")
    
    config = get_system_config("litellm_squad")
    
    print(f"Default Policy: {config['default_policy']}")
    print(f"Parallel Requests: {config['parallel_requests']}")
    print(f"Available Models: {len(config['models'])}")
    
    print("\nTop 3 Models:")
    for model in config['models'][:3]:
        print(f"  • {model['display_name']} ({model['provider']})")
        print(f"    Virtual Key: {model['virtual_key']}")
        print(f"    Context: {model['context']:,} tokens")
    
    print(f"\nPolicies Available: {len(config['policies'])}")
    for policy_name in list(config['policies'].keys())[:3]:
        print(f"  • {policy_name}")

def test_builder_app():
    """Show Builder App configuration"""
    print_section("BUILDER APP CONFIGURATION")
    
    config = get_system_config("builder_app")
    
    print("Planner Models:")
    for model in config['planner_models'][:3]:
        fallback = " (fallback)" if model.get('is_fallback') else ""
        print(f"  • {model['display_name']}{fallback}")
    
    print("\nCoder Models:")
    for model in config['coder_models'][:3]:
        fallback = " (fallback)" if model.get('is_fallback') else ""
        print(f"  • {model['display_name']}{fallback}")
    
    print("\nReviewer Models:")
    for model in config['reviewer_models'][:3]:
        fallback = " (fallback)" if model.get('is_fallback') else ""
        print(f"  • {model['display_name']}{fallback}")
    
    print(f"\nFallbacks Allowed: {config['allow_fallbacks']}")

def test_sophia_intel():
    """Show Sophia Intel configuration"""
    print_section("SOPHIA INTEL APP CONFIGURATION")
    
    config = get_system_config("sophia_intel")
    
    print(f"Default Policy: {config['default_policy']}")
    print(f"Chat Policy: {config['chat_policy']}")
    print(f"Reasoning Policy: {config['reasoning_policy']}")
    print(f"Creative Policy: {config['creative_policy']}")
    
    print(f"\nAvailable Models: {len(config['models'])}")
    print("Top Models:")
    for model in config['models'][:5]:
        print(f"  • {model['display_name']} (Priority {model['priority']})")

def test_task_routing():
    """Test dynamic task routing"""
    print_section("DYNAMIC TASK ROUTING")
    
    manager = get_model_manager()
    
    test_cases = [
        ("Write code to parse JSON", "builder_app"),
        ("Quick chat response", "sophia_intel"),
        ("Complex reasoning about philosophy", "litellm_squad"),
        ("Debug this Python function", "builder_app"),
        ("Generate creative story", "sophia_intel"),
        ("Research paper on AI ethics", "litellm_squad"),
    ]
    
    for task, system in test_cases:
        model = manager.select_model_for_task(task, system=system)
        print(f"Task: '{task}'")
        print(f"System: {system}")
        print(f"Selected: {model['display_name']} ({model['provider']})")
        print(f"Virtual Key: {model['virtual_key']}")
        print()

def show_your_control():
    """Show how you control everything"""
    print_section("YOUR CONTROL PANEL")
    
    print("✅ You control everything from: config/user_models_config.yaml")
    print("\nTo change models:")
    print("  1. Edit user_models_config.yaml")
    print("  2. Set 'enabled: true/false' for models")
    print("  3. Adjust 'priority' (1-10)")
    print("  4. Modify routing policies")
    print("\nTo adjust routing:")
    print("  • Edit 'routing_policies' section")
    print("  • Change 'system_overrides' for each system")
    print("  • Update 'task_rules' for automatic routing")
    print("\nChanges take effect immediately!")
    
    manager = get_model_manager()
    monitoring = manager.get_monitoring_config()
    
    print(f"\nYour Current Settings:")
    print(f"  • Daily Budget: ${monitoring['daily_budget']}")
    print(f"  • Cost Alert: ${monitoring['cost_alert_threshold']}")
    print(f"  • Quality First: {manager.prioritize_quality}")
    print(f"  • Performance First: {manager.prioritize_performance}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("UNIFIED MODEL ROUTING TEST")
    print("All Three Systems Using YOUR Configuration")
    print("="*60)
    
    # Test each system
    test_litellm_squad()
    test_builder_app()
    test_sophia_intel()
    test_task_routing()
    show_your_control()
    
    print("\n" + "="*60)
    print("🎯 All systems configured from your central control file!")
    print("Edit config/user_models_config.yaml to change anything")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()