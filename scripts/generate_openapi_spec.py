#!/usr/bin/env python3
"""
Generate OpenAPI Specification for Foundational Knowledge API
This script generates the OpenAPI specification from FastAPI routes
and saves it to a JSON file for documentation and client generation.
"""
import json
import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
# Import the router
from app.api.routes.foundational_knowledge import router as knowledge_router
from app.api.routes.health import router as health_router
def generate_openapi_spec():
    """
    Generate OpenAPI specification for the Foundational Knowledge API.
    """
    # Create a FastAPI app with the routers
    app = FastAPI(
        title="Foundational Knowledge API",
        description="API for managing foundational business knowledge with versioning, classification, and Airtable sync",
        version="1.0.0",
        contact={
            "name": "Sophia Intel AI Team",
            "email": "support@sophia-intel.ai",
        },
        license_info={
            "name": "Proprietary",
        },
    )
    # Include routers
    app.include_router(knowledge_router, tags=["foundational-knowledge"])
    app.include_router(health_router, tags=["health"])
    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )
    # Add additional information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local development server",
        },
        {
            "url": "https://api.sophia-intel.ai",
            "description": "Production server",
        },
    ]
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token",
        },
        "apiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service authentication",
        },
        "adminKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Admin-Key",
            "description": "Admin API key for privileged operations",
        },
    }
    # Add example schemas
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    # Add custom schemas
    openapi_schema["components"]["schemas"].update(
        {
            "KnowledgeClassification": {
                "type": "string",
                "enum": [
                    "company_info",
                    "business_metrics",
                    "payment_processing",
                    "integration_config",
                    "operational",
                    "system_config",
                ],
                "description": "Classification of knowledge entities",
            },
            "KnowledgePriority": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Priority level (1=minimal, 5=critical)",
            },
            "SyncStatus": {
                "type": "string",
                "enum": ["idle", "running", "success", "failed", "partial"],
                "description": "Synchronization status",
            },
            "PayReadyContext": {
                "type": "object",
                "properties": {
                    "business_impact": {
                        "type": "string",
                        "description": "Business impact description",
                    },
                    "integration_requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Integration requirements",
                    },
                    "compliance_notes": {
                        "type": "string",
                        "description": "Compliance and regulatory notes",
                    },
                    "revenue_impact": {
                        "type": "string",
                        "description": "Revenue impact assessment",
                    },
                },
            },
        }
    )
    # Add tags descriptions
    openapi_schema["tags"] = [
        {
            "name": "foundational-knowledge",
            "description": "Operations for managing foundational business knowledge",
            "externalDocs": {
                "description": "Full documentation",
                "url": "/docs/foundational_knowledge_system.md",
            },
        },
        {
            "name": "health",
            "description": "Health check and monitoring endpoints",
        },
    ]
    return openapi_schema
def save_openapi_spec(spec: dict, output_path: str):
    """
    Save OpenAPI specification to file.
    Args:
        spec: OpenAPI specification dictionary
        output_path: Path to save the specification
    """
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"OpenAPI specification saved to: {output_path}")
def main():
    """
    Main function to generate and save OpenAPI spec.
    """
    # Generate spec
    print("Generating OpenAPI specification...")
    spec = generate_openapi_spec()
    # Create output directory if needed
    output_dir = project_root / "docs" / "api"
    output_dir.mkdir(parents=True, exist_ok=True)
    # Save as JSON
    json_path = output_dir / "foundational_knowledge_openapi.json"
    save_openapi_spec(spec, str(json_path))
    # Also save as YAML for better readability
    try:
        import yaml
        yaml_path = output_dir / "foundational_knowledge_openapi.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
        print(f"OpenAPI specification (YAML) saved to: {yaml_path}")
    except ImportError:
        print("PyYAML not installed, skipping YAML output")
    # Print summary
    print("\nAPI Summary:")
    print(f"  Title: {spec['info']['title']}")
    print(f"  Version: {spec['info']['version']}")
    print(f"  Endpoints: {len(spec['paths'])}")
    # List endpoints
    print("\nEndpoints:")
    for path, methods in spec["paths"].items():
        for method in methods.keys():
            if method in ["get", "post", "put", "delete", "patch"]:
                print(f"  {method.upper():6} {path}")
if __name__ == "__main__":
    main()
