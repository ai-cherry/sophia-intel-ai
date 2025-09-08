#!/usr/bin/env python3
"""
Weaviate schema loader for Sophia Intel AI
Loads CodeFile, CodeSymbol, and DocFragment classes with hybrid search enabled
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import weaviate
from weaviate.exceptions import SchemaValidationException

SCHEMA_DIR = Path(__file__).parent
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")


def load_schema_file(filename: str) -> Dict[str, Any]:
    """Load a schema JSON file"""
    schema_path = SCHEMA_DIR / filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r") as f:
        return json.load(f)


def create_weaviate_client() -> weaviate.Client:
    """Create Weaviate client with error handling"""
    try:
        client = weaviate.Client(
            url=WEAVIATE_URL, timeout_config=(5, 15)  # (connect, read) timeout
        )

        # Test connection
        if not client.is_ready():
            raise ConnectionError("Weaviate is not ready")

        print(f"✅ Connected to Weaviate at {WEAVIATE_URL}")
        return client

    except Exception as e:
        print(f"❌ Failed to connect to Weaviate: {e}")
        sys.exit(1)


def class_exists(client: weaviate.Client, class_name: str) -> bool:
    """Check if a class already exists in Weaviate"""
    try:
        schema = client.schema.get()
        existing_classes = [cls["class"] for cls in schema.get("classes", [])]
        return class_name in existing_classes
    except Exception:
        return False


def create_class(
    client: weaviate.Client, class_schema: Dict[str, Any], force: bool = False
) -> bool:
    """Create a class in Weaviate with error handling"""
    class_name = class_schema["class"]

    try:
        if class_exists(client, class_name):
            if force:
                print(f"🔄 Deleting existing class: {class_name}")
                client.schema.delete_class(class_name)
            else:
                print(f"ℹ️  Class {class_name} already exists, skipping...")
                return True

        print(f"🆕 Creating class: {class_name}")
        client.schema.create_class(class_schema)

        # Verify creation
        if class_exists(client, class_name):
            print(f"✅ Successfully created class: {class_name}")
            return True
        else:
            print(f"❌ Failed to verify class creation: {class_name}")
            return False

    except SchemaValidationException as e:
        print(f"❌ Schema validation error for {class_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating class {class_name}: {e}")
        return False


def load_all_schemas(client: weaviate.Client, force: bool = False) -> bool:
    """Load all schema files"""
    schema_files = ["code_file.json", "code_symbol.json", "doc_fragment.json"]

    success_count = 0
    total_count = len(schema_files)

    print(f"🔄 Loading {total_count} schema files...")

    for schema_file in schema_files:
        try:
            schema = load_schema_file(schema_file)
            if create_class(client, schema, force=force):
                success_count += 1
            else:
                print(f"❌ Failed to create class from {schema_file}")
        except Exception as e:
            print(f"❌ Error processing {schema_file}: {e}")

    print(
        f"\n📊 Schema loading complete: {success_count}/{total_count} classes created"
    )
    return success_count == total_count


def validate_hybrid_search(client: weaviate.Client) -> bool:
    """Validate that hybrid search is working"""
    print("\n🔍 Validating hybrid search configuration...")

    try:
        # Test hybrid search on CodeFile class (should exist after loading)
        result = (
            client.query.get("CodeFile")
            .with_hybrid(query="test", alpha=0.5)
            .with_limit(1)
            .do()
        )

        print("✅ Hybrid search validation successful")
        return True

    except Exception as e:
        print(f"❌ Hybrid search validation failed: {e}")
        return False


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load Weaviate schemas for Sophia Intel AI"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force recreate existing classes"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Run validation tests after loading"
    )
    parser.add_argument(
        "--url", default=WEAVIATE_URL, help=f"Weaviate URL (default: {WEAVIATE_URL})"
    )

    args = parser.parse_args()

    # Override URL if provided
    global WEAVIATE_URL
    WEAVIATE_URL = args.url

    print("🚀 Sophia Intel AI - Weaviate Schema Loader")
    print(f"🎯 Target: {WEAVIATE_URL}")
    print(f"🔧 Force recreate: {args.force}")

    # Create client
    client = create_weaviate_client()

    # Load schemas
    success = load_all_schemas(client, force=args.force)

    # Validate if requested
    if args.validate and success:
        validate_hybrid_search(client)

    # Print final status
    if success:
        print("\n🎉 Schema loading completed successfully!")
        print("\n📋 Available classes:")
        schema = client.schema.get()
        for cls in schema.get("classes", []):
            print(f"  - {cls['class']}: {cls.get('description', 'No description')}")
    else:
        print("\n❌ Schema loading failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
