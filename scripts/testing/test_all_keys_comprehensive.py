#!/usr/bin/env python3
"""
COMPREHENSIVE API KEY TESTING SCRIPT
Tests ALL Portkey virtual keys and direct API keys
Ensures everything is accessible to orchestrators and agents
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.ENDC}")


def test_portkey_virtual_keys():
    """Test ALL Portkey virtual keys with correct configuration"""
    print_header("TESTING ALL PORTKEY VIRTUAL KEYS")

    from portkey_ai import Portkey

    # Exact virtual keys from Portkey dashboard
    virtual_keys = {
        "OPENAI-VK": {
            "key": "openai-vk-190a60",
            "model": "gpt-3.5-turbo",
            "test_prompt": "Say 'OpenAI connected' in 3 words",
        },
        "ANTHROPIC-VK": {
            "key": "anthropic-vk-b42804",
            "model": "claude-3-haiku-20240307",
            "test_prompt": "Say 'Anthropic connected' in 3 words",
        },
        "DEEPSEEK-VK": {
            "key": "deepseek-vk-24102f",
            "model": "deepseek-chat",
            "test_prompt": "Say 'DeepSeek connected' in 3 words",
        },
        "OPENROUTER-VK": {
            "key": "vkj-openrouter-cc4151",
            "model": "auto",
            "test_prompt": "Say 'OpenRouter connected' in 3 words",
        },
        "PERPLEXITY-VK": {
            "key": "perplexity-vk-56c172",
            "model": "llama-3.1-sonar-small-128k-online",
            "test_prompt": "Say 'Perplexity connected' in 3 words",
        },
        "GROQ-VK": {
            "key": "groq-vk-6b9b52",
            "model": "llama3-8b-8192",
            "test_prompt": "Say 'Groq connected' in 3 words",
        },
        "MISTRAL-VK": {
            "key": "mistral-vk-f92861",
            "model": "mistral-small-latest",
            "test_prompt": "Say 'Mistral connected' in 3 words",
        },
        "XAI-VK": {
            "key": "xai-vk-e65d0f",
            "model": "grok-beta",
            "test_prompt": "Say 'XAI connected' in 3 words",
        },
        "TOGETHER-VK": {
            "key": "together-ai-670469",
            "model": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
            "test_prompt": "Say 'Together connected' in 3 words",
        },
        "COHERE-VK": {
            "key": "cohere-vk-496fa9",
            "model": "command-r",
            "test_prompt": "Say 'Cohere connected' in 3 words",
        },
        "GEMINI-VK": {
            "key": "gemini-vk-3d6108",
            "model": "gemini-1.5-flash",
            "test_prompt": "Say 'Gemini connected' in 3 words",
        },
        "HUGGINGFACE-VK": {
            "key": "huggingface-vk-28240e",
            "model": "microsoft/Phi-3-mini-4k-instruct",
            "test_prompt": "Say 'HuggingFace connected' in 3 words",
        },
    }

    # Vector DB virtual keys (these don't support chat completions)
    vector_keys = {"QDRANT-VK": "qdrant-vk-d2b62a", "MILVUS-VK": "milvus-vk-34fa02"}

    portkey_api_key = os.getenv("PORTKEY_API_KEY")
    if not portkey_api_key:
        raise RuntimeError("PORTKEY_API_KEY is required to run this test.")
    results = {}

    print(f"\n{Colors.BOLD}Testing LLM Virtual Keys:{Colors.ENDC}")

    for name, config in virtual_keys.items():
        print(f"\n{name}: ", end="")
        try:
            client = Portkey(api_key=portkey_api_key, virtual_key=config["key"])

            response = client.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": config["test_prompt"]}],
                max_tokens=20,
                temperature=0,
            )

            if response and response.choices:
                result = response.choices[0].message.content
                print(f"{Colors.GREEN}✓ SUCCESS{Colors.ENDC} - Response: {result[:50]}")
                results[name] = {"status": "success", "response": result[:100]}
            else:
                print(f"{Colors.RED}✗ FAILED{Colors.ENDC} - No response")
                results[name] = {"status": "failed", "error": "No response"}

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"{Colors.RED}✗ FAILED{Colors.ENDC} - {error_msg}")
            results[name] = {"status": "failed", "error": error_msg}

        time.sleep(0.5)  # Rate limiting

    print(f"\n{Colors.BOLD}Vector DB Virtual Keys (for reference):{Colors.ENDC}")
    for name, key in vector_keys.items():
        print(f"{name}: {key}")
        results[name] = {"status": "configured", "key": key}

    return results


def test_direct_api_keys():
    """Test all direct API keys"""
    print_header("TESTING DIRECT API KEYS")

    results = {}

    # Test OpenAI directly
    print(f"\n{Colors.BOLD}Testing Direct OpenAI:{Colors.ENDC}")
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv(
                "OPENAI_API_KEY",
                "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",
            )
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Direct OpenAI works'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✓ OpenAI Direct API works{Colors.ENDC}")
        results["openai_direct"] = "success"
    except Exception as e:
        print(f"{Colors.RED}✗ OpenAI Direct API failed: {str(e)[:100]}{Colors.ENDC}")
        results["openai_direct"] = f"failed: {str(e)[:100]}"

    # Test Anthropic directly
    print(f"\n{Colors.BOLD}Testing Direct Anthropic:{Colors.ENDC}")
    try:
        from anthropic import Anthropic

        client = Anthropic(
            api_key=os.getenv(
                "ANTHROPIC_API_KEY",
                "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",
            )
        )
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Say 'Direct Anthropic works'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✓ Anthropic Direct API works{Colors.ENDC}")
        results["anthropic_direct"] = "success"
    except Exception as e:
        print(f"{Colors.RED}✗ Anthropic Direct API failed: {str(e)[:100]}{Colors.ENDC}")
        results["anthropic_direct"] = f"failed: {str(e)[:100]}"

    # Test OpenRouter directly
    print(f"\n{Colors.BOLD}Testing Direct OpenRouter:{Colors.ENDC}")
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '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')}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Say 'OpenRouter works'"}],
            "max_tokens": 10,
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ OpenRouter Direct API works{Colors.ENDC}")
            results["openrouter_direct"] = "success"
        else:
            print(
                f"{Colors.RED}✗ OpenRouter Direct API failed: {response.status_code}{Colors.ENDC}"
            )
            results["openrouter_direct"] = f"failed: {response.status_code}"
    except Exception as e:
        print(
            f"{Colors.RED}✗ OpenRouter Direct API failed: {str(e)[:100]}{Colors.ENDC}"
        )
        results["openrouter_direct"] = f"failed: {str(e)[:100]}"

    # Test Together AI directly
    print(f"\n{Colors.BOLD}Testing Direct Together AI:{Colors.ENDC}")
    try:
        from together import Together

        client = Together(
            api_key=os.getenv(
                "TOGETHER_AI_API_KEY",
                "tgp_v1_HE_uluFh-fELZDmEP9xKZXuSBT4a8EHd6s9CmSe5WWo",
            )
        )
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
            messages=[{"role": "user", "content": "Say 'Together AI works'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✓ Together AI Direct API works{Colors.ENDC}")
        results["together_direct"] = "success"
    except Exception as e:
        print(
            f"{Colors.RED}✗ Together AI Direct API failed: {str(e)[:100]}{Colors.ENDC}"
        )
        results["together_direct"] = f"failed: {str(e)[:100]}"

    # Test HuggingFace directly
    print(f"\n{Colors.BOLD}Testing Direct HuggingFace:{Colors.ENDC}")
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN', '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')}"
        }
        data = {
            "inputs": "Say 'HuggingFace works'",
            "parameters": {"max_new_tokens": 10},
        }
        response = requests.post(
            "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct",
            headers=headers,
            json=data,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ HuggingFace Direct API works{Colors.ENDC}")
            results["huggingface_direct"] = "success"
        else:
            print(
                f"{Colors.RED}✗ HuggingFace Direct API failed: {response.status_code}{Colors.ENDC}"
            )
            results["huggingface_direct"] = f"failed: {response.status_code}"
    except Exception as e:
        print(
            f"{Colors.RED}✗ HuggingFace Direct API failed: {str(e)[:100]}{Colors.ENDC}"
        )
        results["huggingface_direct"] = f"failed: {str(e)[:100]}"

    # Test Groq directly
    print(f"\n{Colors.BOLD}Testing Direct Groq:{Colors.ENDC}")
    try:
        from groq import Groq

        client = Groq(
            api_key=os.getenv(
                "GROQ_API_KEY",
                "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",
            )
        )
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "Say 'Groq works'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✓ Groq Direct API works{Colors.ENDC}")
        results["groq_direct"] = "success"
    except Exception as e:
        print(f"{Colors.RED}✗ Groq Direct API failed: {str(e)[:100]}{Colors.ENDC}")
        results["groq_direct"] = f"failed: {str(e)[:100]}"

    # Test Mistral directly
    print(f"\n{Colors.BOLD}Testing Direct Mistral:{Colors.ENDC}")
    try:
        from mistralai.client import MistralClient
        from mistralai.models.chat_completion import ChatMessage

        client = MistralClient(
            api_key=os.getenv("MISTRAL_API_KEY", "jCGVZEeBzppPH0pPVL0vxRCPnZuWL90i")
        )
        response = client.chat(
            model="mistral-small-latest",
            messages=[ChatMessage(role="user", content="Say 'Mistral works'")],
        )
        print(f"{Colors.GREEN}✓ Mistral Direct API works{Colors.ENDC}")
        results["mistral_direct"] = "success"
    except Exception as e:
        print(f"{Colors.RED}✗ Mistral Direct API failed: {str(e)[:100]}{Colors.ENDC}")
        results["mistral_direct"] = f"failed: {str(e)[:100]}"

    # Test DeepSeek directly
    print(f"\n{Colors.BOLD}Testing Direct DeepSeek:{Colors.ENDC}")
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv(
                "DEEPSEEK_API_KEY", "sk-c8a5f1725d7b4f96b29a3d041848cb74"
            ),
            base_url="https://api.deepseek.com/v1",
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Say 'DeepSeek works'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✓ DeepSeek Direct API works{Colors.ENDC}")
        results["deepseek_direct"] = "success"
    except Exception as e:
        print(f"{Colors.RED}✗ DeepSeek Direct API failed: {str(e)[:100]}{Colors.ENDC}")
        results["deepseek_direct"] = f"failed: {str(e)[:100]}"

    # Test Perplexity directly
    print(f"\n{Colors.BOLD}Testing Direct Perplexity:{Colors.ENDC}")
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv(
                "PERPLEXITY_API_KEY",
                "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",
            ),
            base_url="https://api.perplexity.ai",
        )
        response = client.chat.completions.create(
            model="llama-3.1-sonar-small-128k-online",
            messages=[{"role": "user", "content": "Say 'Perplexity works'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✓ Perplexity Direct API works{Colors.ENDC}")
        results["perplexity_direct"] = "success"
    except Exception as e:
        print(
            f"{Colors.RED}✗ Perplexity Direct API failed: {str(e)[:100]}{Colors.ENDC}"
        )
        results["perplexity_direct"] = f"failed: {str(e)[:100]}"

    # Test Gemini directly
    print(f"\n{Colors.BOLD}Testing Direct Gemini:{Colors.ENDC}")
    try:
        import google.generativeai as genai

        genai.configure(
            api_key=os.getenv(
                "GEMINI_API_KEY", "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
            )
        )
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'Gemini works'")
        print(f"{Colors.GREEN}✓ Gemini Direct API works{Colors.ENDC}")
        results["gemini_direct"] = "success"
    except Exception as e:
        print(f"{Colors.RED}✗ Gemini Direct API failed: {str(e)[:100]}{Colors.ENDC}")
        results["gemini_direct"] = f"failed: {str(e)[:100]}"

    # Test Llama API
    print(f"\n{Colors.BOLD}Testing Llama API:{Colors.ENDC}")
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {os.getenv('LLAMA_API_KEY', 'llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj')}"
        }
        data = {
            "messages": [{"role": "user", "content": "Say 'Llama works'"}],
            "stream": False,
        }
        response = requests.post(
            "https://api.llama-api.com/chat/completions",
            headers=headers,
            json=data,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Llama API works{Colors.ENDC}")
            results["llama_api"] = "success"
        else:
            print(
                f"{Colors.RED}✗ Llama API failed: {response.status_code}{Colors.ENDC}"
            )
            results["llama_api"] = f"failed: {response.status_code}"
    except Exception as e:
        print(f"{Colors.RED}✗ Llama API failed: {str(e)[:100]}{Colors.ENDC}")
        results["llama_api"] = f"failed: {str(e)[:100]}"

    return results


def test_orchestrator_access():
    """Test that orchestrators can access the keys"""
    print_header("TESTING ORCHESTRATOR ACCESS TO KEYS")

    results = {}

    # Test Artemis orchestrator access
    print(f"\n{Colors.BOLD}Testing Artemis Orchestrator:{Colors.ENDC}")
    try:
        from app.artemis.unified_factory import artemis_unified_factory

        # Check if factory can access Portkey configuration
        agent = artemis_unified_factory.create_agent(
            role="code_reviewer", personality="tactical_precise"
        )

        if agent and agent.virtual_key:
            print(f"{Colors.GREEN}✓ Artemis can access Portkey keys{Colors.ENDC}")
            print(f"  Agent created with virtual key: {agent.virtual_key[:20]}...")
            results["artemis_access"] = "success"
        else:
            print(f"{Colors.RED}✗ Artemis cannot access keys{Colors.ENDC}")
            results["artemis_access"] = "failed"

    except Exception as e:
        print(f"{Colors.RED}✗ Artemis orchestrator error: {str(e)[:100]}{Colors.ENDC}")
        results["artemis_access"] = f"error: {str(e)[:100]}"

    # Test Sophia orchestrator access (if exists)
    print(f"\n{Colors.BOLD}Testing Sophia Orchestrator:{Colors.ENDC}")
    try:
        from app.sophia.sophia_orchestrator import SophiaOrchestrator

        orchestrator = SophiaOrchestrator()
        print(f"{Colors.GREEN}✓ Sophia orchestrator accessible{Colors.ENDC}")
        results["sophia_access"] = "success"
    except ImportError:
        print(f"{Colors.YELLOW}⚠ Sophia orchestrator not found{Colors.ENDC}")
        results["sophia_access"] = "not_found"
    except Exception as e:
        print(f"{Colors.RED}✗ Sophia orchestrator error: {str(e)[:100]}{Colors.ENDC}")
        results["sophia_access"] = f"error: {str(e)[:100]}"

    # Test Portkey manager access
    print(f"\n{Colors.BOLD}Testing Portkey Manager:{Colors.ENDC}")
    try:
        from app.core.portkey_config import portkey_manager

        status = portkey_manager.get_provider_status()
        configured_count = sum(1 for p in status.values() if p["configured"])
        print(
            f"{Colors.GREEN}✓ Portkey manager configured with {configured_count} providers{Colors.ENDC}"
        )
        results["portkey_manager"] = f"{configured_count} providers"
    except Exception as e:
        print(f"{Colors.RED}✗ Portkey manager error: {str(e)[:100]}{Colors.ENDC}")
        results["portkey_manager"] = f"error: {str(e)[:100]}"

    return results


def save_comprehensive_report(all_results: Dict[str, Any]):
    """Save comprehensive test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": all_results,
        "summary": {
            "portkey_virtual_keys": {
                "total": len(
                    [k for k in all_results.get("portkey_keys", {}) if "-VK" in k]
                ),
                "successful": len(
                    [
                        v
                        for k, v in all_results.get("portkey_keys", {}).items()
                        if "-VK" in k and v.get("status") == "success"
                    ]
                ),
            },
            "direct_api_keys": {
                "total": len(all_results.get("direct_keys", {})),
                "successful": len(
                    [
                        v
                        for v in all_results.get("direct_keys", {}).values()
                        if v == "success"
                    ]
                ),
            },
            "orchestrator_access": all_results.get("orchestrator_access", {}),
        },
    }

    # Save to JSON
    report_file = (
        f"comprehensive_key_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    # Save to markdown for easy reading
    md_file = f"KEY_TEST_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(md_file, "w") as f:
        f.write("# Comprehensive API Key Test Results\n\n")
        f.write(f"**Timestamp:** {report['timestamp']}\n\n")

        f.write("## Portkey Virtual Keys\n\n")
        f.write("| Key Name | Status | Response/Error |\n")
        f.write("|----------|--------|---------------|\n")
        for key, result in all_results.get("portkey_keys", {}).items():
            status = "✅" if result.get("status") == "success" else "❌"
            msg = result.get("response", result.get("error", ""))[:50]
            f.write(f"| {key} | {status} | {msg} |\n")

        f.write("\n## Direct API Keys\n\n")
        f.write("| Service | Status |\n")
        f.write("|---------|--------|\n")
        for service, status in all_results.get("direct_keys", {}).items():
            icon = "✅" if status == "success" else "❌"
            f.write(f"| {service} | {icon} {status} |\n")

        f.write("\n## Orchestrator Access\n\n")
        for item, status in all_results.get("orchestrator_access", {}).items():
            f.write(f"- **{item}:** {status}\n")

    print(f"\n{Colors.BOLD}Reports saved:{Colors.ENDC}")
    print(f"  JSON: {report_file}")
    print(f"  Markdown: {md_file}")

    return report


def main():
    """Main test execution"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print(" COMPREHENSIVE API KEY VALIDATION SUITE")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    all_results = {}

    # Test 1: Portkey Virtual Keys
    print("\n[1/3] Testing Portkey Virtual Keys...")
    all_results["portkey_keys"] = test_portkey_virtual_keys()

    # Test 2: Direct API Keys
    print("\n[2/3] Testing Direct API Keys...")
    all_results["direct_keys"] = test_direct_api_keys()

    # Test 3: Orchestrator Access
    print("\n[3/3] Testing Orchestrator Access...")
    all_results["orchestrator_access"] = test_orchestrator_access()

    # Generate Report
    report = save_comprehensive_report(all_results)

    # Print Summary
    print_header("FINAL SUMMARY")

    portkey_success = len(
        [
            v
            for k, v in all_results["portkey_keys"].items()
            if "-VK" in k and v.get("status") == "success"
        ]
    )
    portkey_total = len([k for k in all_results["portkey_keys"] if "-VK" in k])

    direct_success = len(
        [v for v in all_results["direct_keys"].values() if v == "success"]
    )
    direct_total = len(all_results["direct_keys"])

    print(
        f"\n{Colors.BOLD}Portkey Virtual Keys:{Colors.ENDC} {portkey_success}/{portkey_total} working"
    )
    print(
        f"{Colors.BOLD}Direct API Keys:{Colors.ENDC} {direct_success}/{direct_total} working"
    )
    print(
        f"{Colors.BOLD}Orchestrator Access:{Colors.ENDC} {all_results['orchestrator_access'].get('artemis_access', 'unknown')}"
    )

    total_success = portkey_success + direct_success
    total_tests = portkey_total + direct_total
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0

    print(
        f"\n{Colors.BOLD}Overall Success Rate: {success_rate:.1f}% ({total_success}/{total_tests}){Colors.ENDC}"
    )

    if success_rate >= 80:
        print(f"{Colors.GREEN}✅ API KEY VALIDATION PASSED{Colors.ENDC}")
        return 0
    elif success_rate >= 60:
        print(f"{Colors.YELLOW}⚠️  API KEY VALIDATION PARTIALLY PASSED{Colors.ENDC}")
        return 1
    else:
        print(f"{Colors.RED}❌ API KEY VALIDATION FAILED{Colors.ENDC}")
        return 2


if __name__ == "__main__":
    exit(main())
