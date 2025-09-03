#!/usr/bin/env python3
"""Test script to verify OpenAI API key configuration."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_key():
    """Test if OpenAI API key is properly configured and working."""
    
    # Check if key exists
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✅ OPENAI_API_KEY loaded from .env file")
    print(f"   Key prefix: {api_key[:20]}...")
    print(f"   Key length: {len(api_key)} characters")
    
    # Test with OpenAI client
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Try a simple API call
        response = client.models.list()
        models = list(response)
        
        print(f"\n✅ Successfully connected to OpenAI API")
        print(f"   Available models: {len(models)}")
        print(f"   Sample models: {', '.join([m.id for m in models[:3]])}")
        
        return True
        
    except ImportError:
        print("\n⚠️  OpenAI package not installed. Install with: pip install openai")
        return False
        
    except Exception as e:
        print(f"\n❌ Failed to connect to OpenAI API: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_key()
    sys.exit(0 if success else 1)