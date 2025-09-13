#!/usr/bin/env python3
"""Test new API keys and evaluate their potential use in the project."""

import os
import sys
import requests
import json
from pathlib import Path

# Load environment variables
env_file = Path("/Users/lynnmusil/sophia-intel-ai/.env.master")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')

def test_apify():
    """Test Apify API - Web scraping and automation."""
    print("\n🕷️ Testing Apify API (Web Scraping)...")
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        print("❌ APIFY_API_TOKEN not found")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://api.apify.com/v2/acts",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Apify API: Connected successfully")
            data = response.json()
            print(f"   Found {data.get('total', 0)} actors available")
            print("   USE CASE: Could scrape competitor sites, gather market data")
            return True
        else:
            print(f"❌ Apify API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Apify API: {e}")
        return False

def test_arize():
    """Test Arize API - ML monitoring and observability."""
    print("\n📊 Testing Arize API (ML Monitoring)...")
    api_key = os.getenv("ARIZE_API_KEY")
    space_id = os.getenv("ARIZE_SPACE_ID")
    
    if not api_key or not space_id:
        print("❌ ARIZE_API_KEY or ARIZE_SPACE_ID not found")
        return False
    
    try:
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        # Arize uses GraphQL endpoint
        response = requests.post(
            "https://api.arize.com/graphql",
            headers=headers,
            json={"query": "{ spaces { edges { node { id name } } } }"},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Arize API: Connected successfully")
            print(f"   Space ID: {space_id}")
            print("   USE CASE: Monitor AI model performance, track predictions")
            return True
        else:
            print(f"❌ Arize API: HTTP {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Arize API: {e}")
        return False

def test_asana():
    """Test Asana API - Project management."""
    print("\n📋 Testing Asana API (Project Management)...")
    token = os.getenv("ASANA_API_TOKEN")
    if not token:
        print("❌ ASANA_API_TOKEN not found")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://app.asana.com/api/1.0/users/me",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Asana API: Connected successfully")
            data = response.json()
            user = data.get('data', {})
            print(f"   User: {user.get('name', 'Unknown')} ({user.get('email', '')})")
            print("   USE CASE: Already integrated for project tracking")
            return True
        else:
            print(f"❌ Asana API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Asana API: {e}")
        return False

def test_assembly():
    """Test AssemblyAI API - Speech-to-text."""
    print("\n🎤 Testing AssemblyAI API (Speech-to-Text)...")
    api_key = os.getenv("ASSEMBLY_API_KEY")
    if not api_key:
        print("❌ ASSEMBLY_API_KEY not found")
        return False
    
    try:
        headers = {"Authorization": api_key}
        response = requests.get(
            "https://api.assemblyai.com/v2/transcript",
            headers=headers,
            timeout=5
        )
        # AssemblyAI returns 200 with empty list if no transcripts
        if response.status_code == 200:
            print("✅ AssemblyAI API: Connected successfully")
            data = response.json()
            print(f"   Transcripts: {len(data.get('transcripts', []))}")
            print("   USE CASE: Transcribe Gong calls, voice memos, meetings")
            return True
        else:
            print(f"❌ AssemblyAI API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AssemblyAI API: {e}")
        return False

def evaluate_integration():
    """Evaluate which services would benefit the project."""
    print("\n" + "="*60)
    print("🎯 INTEGRATION RECOMMENDATIONS")
    print("="*60)
    
    print("\n✅ ALREADY INTEGRATED:")
    print("• Asana - Project management (app/connectors/asana.py)")
    print("• AssemblyAI - Listed but needs voice features")
    
    print("\n🚀 HIGH VALUE ADDITIONS:")
    print("• Arize - Monitor AI model performance across all agents")
    print("  - Track Sophia's prediction accuracy")
    print("  - Monitor token usage and costs")
    print("  - Detect model drift and anomalies")
    
    print("\n🔄 MODERATE VALUE:")
    print("• Apify - Web scraping for competitive intelligence")
    print("  - Could gather market data automatically")
    print("  - Scrape competitor pricing/features")
    
    print("\n⚠️ LOW PRIORITY (at this stage):")
    print("• AssemblyAI - Unless adding voice features soon")
    
    print("\n📝 RECOMMENDATION:")
    print("Focus on Arize for AI observability - critical for production")
    print("Keep others in .env.master for future use")

def main():
    print("🔑 Testing New API Keys")
    print("="*60)
    
    results = {
        "Apify": test_apify(),
        "Arize": test_arize(),
        "Asana": test_asana(),
        "AssemblyAI": test_assembly()
    }
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    for service, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {service}: {'Connected' if status else 'Failed'}")
    
    evaluate_integration()
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n✨ {success_count}/{len(results)} services connected successfully")
    
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())