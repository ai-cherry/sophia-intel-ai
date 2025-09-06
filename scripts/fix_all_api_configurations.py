#!/usr/bin/env python3
"""
Fix All API Configurations Based on Best Practices
Implements the solutions from the research document
"""

import json
import os
import sys
import time
from datetime import datetime

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Update environment with correct configurations
os.environ.update(
    {
        "PERPLEXITY_API_KEY": "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",
        "XAI_API_KEY": "xai-4WmKCCbqXhuxL56tfrCxaqs3N84fcLVirQG0NIb0NB6ViDPnnvr3vsYOBwpPKpPMzW5UMuHqf1kv87m3",
        "HUGGINGFACE_API_TOKEN": "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",
        "MEM0_API_KEY": "m0-migu5eMnfwT41nhTgVHsCnSAifVtOf3WIFz2vmQc",
        "QDRANT_API_KEY": "ccabdaed-b564-4157-8846-b8f227c7f29b|hRnj-WYa5pxZlPuu2S2LmrX2LziBOdChyLP5Hq578N-HIi16EZIshA",
        "WEAVIATE_API_KEY": "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf",
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


def fix_perplexity():
    """Fix Perplexity API with correct model names"""
    print_header("FIXING PERPLEXITY API")

    from openai import OpenAI

    client = OpenAI(api_key=os.environ["PERPLEXITY_API_KEY"], base_url="https://api.perplexity.ai")

    # ✅ CORRECT Model Names (2025) based on research
    valid_models = [
        "sonar-pro",  # Most capable
        "sonar",  # Standard
        "sonar-reasoning",  # Enhanced reasoning
    ]

    print("Testing with corrected model names...")
    for model in valid_models:
        try:
            print(f"\nTrying model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'Perplexity works'"}],
                max_tokens=10,
            )
            print(
                f"{Colors.GREEN}✅ {model} WORKS: {response.choices[0].message.content}{Colors.ENDC}"
            )
            return True
        except Exception as e:
            error = str(e)[:100]
            if "rate limit" in error.lower():
                print(f"{Colors.YELLOW}⚠️  {model}: Rate limited{Colors.ENDC}")
            else:
                print(f"{Colors.RED}❌ {model}: {error}{Colors.ENDC}")

    return False


def fix_xai_grok():
    """Fix X.AI Grok with correct model names"""
    print_header("FIXING X.AI GROK")

    from openai import OpenAI

    client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")

    # ✅ CORRECT Model Names (2025) based on research
    valid_models = [
        "grok-2",  # Latest flagship model
        "grok-2-mini",  # Smaller version
        "grok-vision-2",  # Vision capabilities
    ]

    print("Testing with corrected model names...")
    for model in valid_models:
        try:
            print(f"\nTrying model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'Grok works'"}],
                max_tokens=10,
                extra_body={
                    "search_enabled": False,  # Disable search for simple test
                },
            )
            print(
                f"{Colors.GREEN}✅ {model} WORKS: {response.choices[0].message.content}{Colors.ENDC}"
            )
            return True
        except Exception as e:
            error = str(e)[:100]
            print(f"{Colors.RED}❌ {model}: {error}{Colors.ENDC}")

    return False


def fix_huggingface():
    """Fix HuggingFace with valid model identifiers"""
    print_header("FIXING HUGGINGFACE")

    # ✅ CORRECT Model Identifiers based on research
    valid_models = [
        "microsoft/DialoGPT-medium",  # Recommended conversational
        "microsoft/DialoGPT-small",  # Lighter version
        "google/flan-t5-base",  # Text generation
        "distilbert/distilgpt2",  # Fast GPT2 variant
    ]

    headers = {"Authorization": f"Bearer {os.environ['HUGGINGFACE_API_TOKEN']}"}

    print("Testing with correct model identifiers...")
    for model in valid_models:
        try:
            print(f"\nTrying model: {model}")
            api_url = f"https://api-inference.huggingface.co/models/{model}"

            # Different payload based on model type
            if "DialoGPT" in model:
                payload = {
                    "inputs": "Hello, how are you?",
                    "parameters": {"max_new_tokens": 20, "return_full_text": False},
                }
            else:
                payload = {
                    "inputs": "Say 'HuggingFace works'",
                    "parameters": {"max_new_tokens": 10},
                }

            response = requests.post(api_url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"{Colors.GREEN}✅ {model} WORKS: {str(result)[:100]}{Colors.ENDC}")
                return True
            elif response.status_code == 503:
                print(f"{Colors.YELLOW}⚠️  {model}: Model loading, retry needed{Colors.ENDC}")
                time.sleep(3)
                # Retry once
                response = requests.post(api_url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"{Colors.GREEN}✅ {model} WORKS after retry{Colors.ENDC}")
                    return True
            else:
                print(f"{Colors.RED}❌ {model}: HTTP {response.status_code}{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.RED}❌ {model}: {str(e)[:100]}{Colors.ENDC}")

    return False


def fix_mem0():
    """Fix Mem0 with different authentication formats"""
    print_header("FIXING MEM0")

    api_key = os.environ["MEM0_API_KEY"]

    # Try different authentication formats based on research
    auth_formats = [
        ("Token", f"Token {api_key}"),
        ("Bearer", f"Bearer {api_key}"),
        ("Direct", api_key),
        ("Basic", f"Basic {api_key}"),
    ]

    print("Testing different authentication formats...")
    for format_name, auth_header in auth_formats:
        try:
            print(f"\nTrying format: {format_name}")
            headers = {"Authorization": auth_header, "Content-Type": "application/json"}

            # Try to get memories (should work even if empty)
            response = requests.get(
                "https://api.mem0.ai/v1/memories",
                headers=headers,
                params={"user_id": "test"},
                timeout=10,
            )

            if response.status_code == 200:
                print(f"{Colors.GREEN}✅ {format_name} format WORKS{Colors.ENDC}")
                return True
            elif response.status_code == 401:
                print(f"{Colors.YELLOW}⚠️  {format_name}: Still unauthorized{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}⚠️  {format_name}: HTTP {response.status_code}{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.RED}❌ {format_name}: {str(e)[:100]}{Colors.ENDC}")

    # If all fail, key might be expired
    print(f"\n{Colors.RED}❌ All authentication formats failed - key might be expired{Colors.ENDC}")
    print("Visit https://app.mem0.ai to generate a new API key")
    return False


def fix_qdrant():
    """Fix Qdrant by handling composite key format"""
    print_header("FIXING QDRANT")

    raw_key = os.environ["QDRANT_API_KEY"]

    # Handle composite key format based on research
    if "|" in raw_key:
        print("Detected composite key format (contains '|')")
        key_parts = raw_key.split("|")
        print(f"Key has {len(key_parts)} parts")

        # Try each part
        for i, key_part in enumerate(key_parts):
            try:
                print(f"\nTrying part {i+1}: {key_part[:20]}...")

                from qdrant_client import QdrantClient

                client = QdrantClient(
                    url="https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io",
                    api_key=key_part,
                    timeout=10,
                )

                # Try to get collections
                collections = client.get_collections()
                print(f"{Colors.GREEN}✅ Part {i+1} WORKS! Collections: {collections}{Colors.ENDC}")

                # Save the working part
                print(f"\n{Colors.GREEN}Use this key part: {key_part[:20]}...{Colors.ENDC}")
                return True

            except Exception as e:
                error = str(e)[:100]
                if "403" in error or "forbidden" in error.lower():
                    print(f"{Colors.RED}❌ Part {i+1}: Forbidden{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}❌ Part {i+1}: {error}{Colors.ENDC}")
    else:
        print("Single key format, testing as-is...")
        # Test single key format
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(
                url="https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io",
                api_key=raw_key,
                timeout=10,
            )
            collections = client.get_collections()
            print(f"{Colors.GREEN}✅ Key WORKS! Collections: {collections}{Colors.ENDC}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Key failed: {str(e)[:100]}{Colors.ENDC}")

    return False


def fix_weaviate():
    """Fix Weaviate protobuf version conflict"""
    print_header("FIXING WEAVIATE")

    print("Checking protobuf version...")
    try:
        import google.protobuf

        current_version = google.protobuf.__version__
        print(f"Current protobuf version: {current_version}")

        # Check if version is compatible
        major, minor = map(int, current_version.split(".")[:2])
        if major == 4 and 21 <= minor <= 25:
            print(f"{Colors.GREEN}✅ Protobuf version is compatible{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}⚠️  Protobuf version might cause issues{Colors.ENDC}")
            print("Run: pip install --upgrade protobuf==4.25.0")

    except ImportError:
        print(f"{Colors.RED}❌ Protobuf not installed{Colors.ENDC}")
        print("Run: pip install protobuf==4.25.0")
        return False

    # Try to import and test Weaviate
    try:
        import weaviate
        from weaviate.auth import AuthApiKey

        client = weaviate.Client(
            url="https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
            auth_client_secret=AuthApiKey(api_key=os.environ["WEAVIATE_API_KEY"]),
        )

        # Test connection
        schema = client.schema.get()
        print(f"{Colors.GREEN}✅ Weaviate connection WORKS!{Colors.ENDC}")
        return True

    except ImportError as e:
        if "runtime_version" in str(e):
            print(f"{Colors.RED}❌ Protobuf version conflict detected{Colors.ENDC}")
            print("Fix: pip install --upgrade protobuf==4.25.0 --force-reinstall")
        else:
            print(f"{Colors.RED}❌ Weaviate import error: {str(e)[:100]}{Colors.ENDC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Weaviate connection failed: {str(e)[:100]}{Colors.ENDC}")
        return False


def save_fixed_configuration():
    """Save the fixed configuration"""
    print_header("SAVING FIXED CONFIGURATION")

    fixed_config = {
        "perplexity": {
            "models": ["sonar-pro", "sonar", "sonar-reasoning"],
            "base_url": "https://api.perplexity.ai",
        },
        "xai": {"models": ["grok-2", "grok-2-mini"], "base_url": "https://api.x.ai/v1"},
        "huggingface": {
            "models": ["microsoft/DialoGPT-medium", "google/flan-t5-base"],
            "base_url": "https://api-inference.huggingface.co",
        },
        "mem0": {
            "auth_format": "Try Token, Bearer, or Direct",
            "note": "Key might be expired - regenerate at https://app.mem0.ai",
        },
        "qdrant": {
            "note": "Use first part of key before '|' character",
            "example": "key.split('|')[0]",
        },
        "weaviate": {
            "fix": "pip install --upgrade protobuf==4.25.0",
            "note": "Requires protobuf 4.x for compatibility",
        },
    }

    with open("fixed_api_configurations.json", "w") as f:
        json.dump(fixed_config, f, indent=2)

    print(f"{Colors.GREEN}✅ Configuration saved to fixed_api_configurations.json{Colors.ENDC}")
    return fixed_config


def main():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print(" FIXING ALL API CONFIGURATIONS")
    print(" Based on Best Practices Research")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    results = {}

    # Fix each service
    results["perplexity"] = fix_perplexity()
    results["xai_grok"] = fix_xai_grok()
    results["huggingface"] = fix_huggingface()
    results["mem0"] = fix_mem0()
    results["qdrant"] = fix_qdrant()
    results["weaviate"] = fix_weaviate()

    # Save configuration
    config = save_fixed_configuration()

    # Summary
    print_header("FINAL RESULTS")

    working = sum(1 for v in results.values() if v)
    total = len(results)

    for service, status in results.items():
        icon = f"{Colors.GREEN}✅{Colors.ENDC}" if status else f"{Colors.RED}❌{Colors.ENDC}"
        print(f"{icon} {service.upper()}: {'FIXED' if status else 'NEEDS ATTENTION'}")

    print(f"\n{Colors.BOLD}Success Rate: {working}/{total} ({working*100//total}%){Colors.ENDC}")

    if working == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL APIS FIXED AND WORKING!{Colors.ENDC}")
    else:
        print(
            f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some APIs still need manual intervention{Colors.ENDC}"
        )
        print("\nNext steps:")
        if not results["mem0"]:
            print("- Regenerate Mem0 API key at https://app.mem0.ai")
        if not results["xai_grok"]:
            print("- Verify X.AI account has API access")
        if not results["weaviate"]:
            print("- Run: pip install --upgrade protobuf==4.25.0")

    return 0 if working >= 4 else 1


if __name__ == "__main__":
    exit(main())
