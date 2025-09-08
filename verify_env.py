#!/usr/bin/env python3
import os
import sys

required = [
    "AIMLAPI_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "WEAVIATE_API_KEY",
    "QDRANT_API_KEY",
    "NEO4J_URI",
    "PORTKEY_API_KEY",
    "AGNO_API_KEY",
]

missing = [var for var in required if not os.getenv(var)]

if missing:
    print(f"❌ Missing environment variables: {', '.join(missing)}")
    sys.exit(1)
else:
    print("✅ All environment variables configured")

