#!/usr/bin/env python3
"""
Test ALL Updated API Keys Including New Ones
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Update environment with new keys
os.environ.update(
    {
        "HUGGINGFACE_API_TOKEN": "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",
        "XAI_API_KEY": "xai-4WmKCCbqXhuxL56tfrCxaqs3N84fcLVirQG0NIb0NB6ViDPnnvr3vsYOBwpPKpPMzW5UMuHqf1kv87m3",
        "OPENAI_API_KEY": "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",
        "OPENROUTER_API_KEY": "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",
        "QWEN_API_KEY": "qwen-api-key-ad6c81",
        "PERPLEXITY_API_KEY": "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",
        "MEM0_API_KEY": "m0-migu5eMnfwT41nhTgVHsCnSAifVtOf3WIFz2vmQc",
        "MILVUS_API_KEY": "d21d225d7b5f192996ff5c89e2b725eb0f969818ffa8c18393a3a92f52fbff837052ccba69993f4165bd209c4764bc9d67bcc923",
        "NEON_API_KEY": "napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby",
        "REDIS_PASSWORD": "pdM2P5F7oO269JCCtBURsrCBrSacqZmF",
        "REDIS_URL": "redis://default:pdM2P5F7oO269JCCtBURsrCBrSacqZmF@redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com:15014",
    }
)


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(title):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.ENDC}")


def test_openai():
    """Test OpenAI with updated key"""
    print(f"\n{Colors.BOLD}[OpenAI]{Colors.ENDC}")
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OpenAI OK'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✅ OpenAI: {response.choices[0].message.content}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ OpenAI: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_xai_grok():
    """Test X.AI Grok with new key"""
    print(f"\n{Colors.BOLD}[X.AI Grok]{Colors.ENDC}")
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")
        response = client.chat.completions.create(
            model="grok-beta",
            messages=[{"role": "user", "content": "Say 'Grok OK'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✅ X.AI Grok: {response.choices[0].message.content}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ X.AI Grok: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_openrouter():
    """Test OpenRouter with updated key"""
    print(f"\n{Colors.BOLD}[OpenRouter]{Colors.ENDC}")
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sophia-intel-ai.com",
            "X-Title": "Sophia Intel AI",
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Say 'OpenRouter OK'"}],
            "max_tokens": 10,
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(
                f"{Colors.GREEN}✅ OpenRouter: {result['choices'][0]['message']['content']}{Colors.ENDC}"
            )
            return True
        else:
            print(f"{Colors.RED}❌ OpenRouter: HTTP {response.status_code}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ OpenRouter: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_perplexity():
    """Test Perplexity with updated key"""
    print(f"\n{Colors.BOLD}[Perplexity]{Colors.ENDC}")
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["PERPLEXITY_API_KEY"], base_url="https://api.perplexity.ai"
        )
        response = client.chat.completions.create(
            model="llama-3.1-sonar-small-128k-chat",
            messages=[{"role": "user", "content": "Say 'Perplexity OK'"}],
            max_tokens=10,
        )
        print(f"{Colors.GREEN}✅ Perplexity: {response.choices[0].message.content}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Perplexity: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_huggingface():
    """Test HuggingFace with API token"""
    print(f"\n{Colors.BOLD}[HuggingFace]{Colors.ENDC}")
    try:
        import requests

        headers = {"Authorization": f"Bearer {os.environ['HUGGINGFACE_API_TOKEN']}"}
        data = {
            "inputs": "Say 'HuggingFace OK'",
            "parameters": {"max_new_tokens": 10, "return_full_text": False},
        }
        # Try a more reliable model
        response = requests.post(
            "https://api-inference.huggingface.co/models/gpt2",
            headers=headers,
            json=data,
            timeout=10,
        )
        if response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}✅ HuggingFace: Connected (GPT-2){Colors.ENDC}")
            return True
        else:
            print(f"{Colors.RED}❌ HuggingFace: HTTP {response.status_code}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ HuggingFace: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_mem0():
    """Test Mem0 memory system"""
    print(f"\n{Colors.BOLD}[Mem0 Memory]{Colors.ENDC}")
    try:
        # Try using requests directly since mem0 package may not be installed
        import requests

        headers = {
            "Authorization": f"Bearer {os.environ['MEM0_API_KEY']}",
            "Content-Type": "application/json",
        }
        # Test with a simple memory operation
        data = {"messages": [{"role": "user", "content": "Test memory"}], "user_id": "test_user"}
        response = requests.post(
            "https://api.mem0.ai/v1/memories", headers=headers, json=data, timeout=10
        )
        if response.status_code in [200, 201]:
            print(f"{Colors.GREEN}✅ Mem0: Connected{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Mem0: HTTP {response.status_code}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Mem0: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_redis():
    """Test Redis with updated credentials"""
    print(f"\n{Colors.BOLD}[Redis]{Colors.ENDC}")
    try:
        import redis

        # Parse the Redis URL
        r = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        # Test connection
        r.ping()
        # Set and get a test value
        r.set("test_key", "Redis OK")
        value = r.get("test_key")
        r.delete("test_key")
        print(f"{Colors.GREEN}✅ Redis: {value}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Redis: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_neon():
    """Test Neon PostgreSQL"""
    print(f"\n{Colors.BOLD}[Neon Database]{Colors.ENDC}")
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {os.environ['NEON_API_KEY']}",
            "Accept": "application/json",
        }
        # Test API connection
        response = requests.get(
            f"https://console.neon.tech/api/v2/projects/{os.environ.get('NEON_PROJECT_ID', 'rough-union-72390895')}",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ Neon: Connected{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Neon: HTTP {response.status_code}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Neon: {str(e)[:100]}{Colors.ENDC}")
        return False


def test_portkey_virtual_keys():
    """Test Portkey virtual keys with real models"""
    print_header("TESTING PORTKEY VIRTUAL KEYS")

    from portkey_ai import Portkey

    test_configs = [
        ("OpenAI", "openai-vk-190a60", "gpt-3.5-turbo"),
        ("Anthropic", "anthropic-vk-b42804", "claude-3-haiku-20240307"),
        ("DeepSeek", "deepseek-vk-24102f", "deepseek-chat"),
        ("Mistral", "mistral-vk-f92861", "mistral-small-latest"),
        ("Together", "together-ai-670469", "meta-llama/Llama-3.2-3B-Instruct-Turbo"),
        ("Perplexity", "perplexity-vk-56c172", "llama-3.1-sonar-small-128k-chat"),
        ("OpenRouter", "vkj-openrouter-cc4151", "openai/gpt-3.5-turbo"),
    ]

    results = []
    for name, vk, model in test_configs:
        print(f"\n{Colors.BOLD}[{name} via Portkey]{Colors.ENDC}")
        try:
            client = Portkey(api_key="hPxFZGd8AN269n4bznDf2/Onbi8I", virtual_key=vk)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"Say '{name} OK'"}],
                max_tokens=10,
                temperature=0,
            )
            print(f"{Colors.GREEN}✅ {name}: {response.choices[0].message.content}{Colors.ENDC}")
            results.append((name, True))
        except Exception as e:
            print(f"{Colors.RED}❌ {name}: {str(e)[:100]}{Colors.ENDC}")
            results.append((name, False))
        time.sleep(0.5)

    return results


def main():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print(" COMPREHENSIVE API KEY VALIDATION - ALL UPDATED KEYS")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    all_results = {}

    # Test Direct APIs
    print_header("TESTING DIRECT API KEYS")

    direct_results = []
    direct_results.append(("OpenAI", test_openai()))
    direct_results.append(("X.AI Grok", test_xai_grok()))
    direct_results.append(("OpenRouter", test_openrouter()))
    direct_results.append(("Perplexity", test_perplexity()))
    direct_results.append(("HuggingFace", test_huggingface()))
    direct_results.append(("Mem0", test_mem0()))
    direct_results.append(("Redis", test_redis()))
    direct_results.append(("Neon", test_neon()))

    all_results["direct"] = direct_results

    # Test Portkey Virtual Keys
    portkey_results = test_portkey_virtual_keys()
    all_results["portkey"] = portkey_results

    # Generate Report
    print_header("FINAL RESULTS SUMMARY")

    # Direct APIs
    print(f"\n{Colors.BOLD}Direct API Keys:{Colors.ENDC}")
    direct_working = sum(1 for _, status in direct_results if status)
    direct_total = len(direct_results)
    for name, status in direct_results:
        icon = f"{Colors.GREEN}✅{Colors.ENDC}" if status else f"{Colors.RED}❌{Colors.ENDC}"
        print(f"  {icon} {name}")
    print(
        f"\n  Success Rate: {direct_working}/{direct_total} ({direct_working*100//direct_total}%)"
    )

    # Portkey Virtual Keys
    print(f"\n{Colors.BOLD}Portkey Virtual Keys:{Colors.ENDC}")
    portkey_working = sum(1 for _, status in portkey_results if status)
    portkey_total = len(portkey_results)
    for name, status in portkey_results:
        icon = f"{Colors.GREEN}✅{Colors.ENDC}" if status else f"{Colors.RED}❌{Colors.ENDC}"
        print(f"  {icon} {name}")
    print(
        f"\n  Success Rate: {portkey_working}/{portkey_total} ({portkey_working*100//portkey_total if portkey_total else 0}%)"
    )

    # Overall Summary
    total_working = direct_working + portkey_working
    total_tests = direct_total + portkey_total

    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(
        f"{Colors.BOLD}OVERALL: {total_working}/{total_tests} APIs Working ({total_working*100//total_tests}%){Colors.ENDC}"
    )

    if total_working >= total_tests * 0.8:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SYSTEM READY FOR PRODUCTION{Colors.ENDC}")
    elif total_working >= total_tests * 0.6:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  SYSTEM PARTIALLY READY{Colors.ENDC}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ SYSTEM NEEDS FIXES{Colors.ENDC}")

    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")

    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "direct_apis": {name: "working" if status else "failed" for name, status in direct_results},
        "portkey_virtual_keys": {
            name: "working" if status else "failed" for name, status in portkey_results
        },
        "summary": {
            "direct_working": direct_working,
            "direct_total": direct_total,
            "portkey_working": portkey_working,
            "portkey_total": portkey_total,
            "overall_success_rate": f"{total_working}/{total_tests} ({total_working*100//total_tests}%)",
        },
    }

    with open("all_keys_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{Colors.BLUE}Report saved to: all_keys_test_report.json{Colors.ENDC}")

    return 0 if total_working >= total_tests * 0.6 else 1


if __name__ == "__main__":
    exit(main())
