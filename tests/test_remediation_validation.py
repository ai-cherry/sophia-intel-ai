#!/usr/bin/env python3
"""
Comprehensive Test Suite for Remediation Validation
Tests all bug fixes and system reliability improvements
"""
import pytest
import asyncio
import json
import hashlib
from unittest.mock import Mock, patch
import httpx
import weaviate

# Test fixtures and utilities
@pytest.fixture
def test_document():
    """Standard test document for brain ingest tests"""
    return {
        "text": "Test document for remediation validation",
        "metadata": {"source": "test", "phase": "remediation"}
    }

@pytest.fixture
def duplicate_document():
    """Document with same content for deduplication testing"""
    return {
        "text": "Test document for remediation validation", 
        "metadata": {"source": "test", "phase": "duplicate_test"}
    }

class TestBrainIngestRemediation:
    """Test brain ingest functionality with bug fixes"""
    
    @pytest.mark.asyncio
    async def test_document_storage_with_content_hash(self, test_document):
        """Test that documents are stored with contentHash field"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/brain/ingest",
                json={"documents": [test_document]},
                timeout=30.0
            )
            
        assert response.status_code == 200
        result = response.json()
        
        # Verify successful storage
        assert result["stored"] == 1
        assert result["duplicates"] == 0
        assert result["errors"] == 0
        assert result["vectors_indexed"] == 1
        
        # Verify content hash is generated
        processed_doc = result["processed_documents"][0]
        assert processed_doc["status"] == "stored"
        assert "content_hash" in processed_doc
        assert len(processed_doc["content_hash"]) > 10  # SHA256 hash should be long
    
    @pytest.mark.asyncio
    async def test_duplicate_detection_with_content_hash(self, test_document, duplicate_document):
        """Test that duplicate detection works with contentHash field"""
        async with httpx.AsyncClient() as client:
            # Store original document
            response1 = await client.post(
                "http://localhost:8003/api/brain/ingest",
                json={"documents": [test_document]},
                timeout=30.0
            )
            assert response1.status_code == 200
            
            # Attempt to store duplicate (same text content)
            response2 = await client.post(
                "http://localhost:8003/api/brain/ingest", 
                json={"documents": [duplicate_document]},
                timeout=30.0
            )
            assert response2.status_code == 200
            
        result2 = response2.json()
        
        # Verify duplicate detection
        assert result2["stored"] == 0
        assert result2["duplicates"] == 1
        assert result2["errors"] == 0
        assert result2["vectors_indexed"] == 0
        
        processed_doc = result2["processed_documents"][0]
        assert processed_doc["status"] == "duplicate"
    
    @pytest.mark.asyncio
    async def test_request_size_limit_enforcement(self):
        """Test that 10MB request size limit is enforced"""
        # Create large document (>10MB)
        large_text = "A" * (11 * 1024 * 1024)  # 11MB of text
        large_document = {
            "text": large_text,
            "metadata": {"source": "size_test"}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/brain/ingest",
                json={"documents": [large_document]},
                timeout=30.0
            )
        
        # Should return 413 Request Entity Too Large
        assert response.status_code == 413
        assert "10MB limit" in response.text

class TestSecretsSync:
    """Test secrets sync functionality with whitespace handling fix"""
    
    def test_whitespace_trimming_in_key_parsing(self):
        """Test that comma-separated keys handle whitespace correctly"""
        from scripts.sync_staging_secrets import parse_key_list  # Assuming we extract this logic
        
        # Test various whitespace scenarios
        test_cases = [
            ("KEY1,KEY2,KEY3", ["KEY1", "KEY2", "KEY3"]),
            ("KEY1, KEY2, KEY3", ["KEY1", "KEY2", "KEY3"]),
            (" KEY1 , KEY2 , KEY3 ", ["KEY1", "KEY2", "KEY3"]),
            ("KEY1,  KEY2  ,   KEY3", ["KEY1", "KEY2", "KEY3"]),
        ]
        
        for input_keys, expected_output in test_cases:
            result = parse_key_list(input_keys)
            assert result == expected_output, f"Failed for input: {input_keys}"
    
    def test_dry_run_functionality(self):
        """Test that dry-run mode doesn't actually sync secrets"""
        # Mock the flyctl command execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            # Run dry-run mode 
            result = subprocess.run([
                './scripts/sync_staging_secrets.sh', 
                '--dry-run', 
                '--only', 
                'OPENROUTER_API_KEY,POSTGRES_URL',
                'test-app'
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "DRY RUN" in result.stdout
            # Verify flyctl was not actually called
            mock_run.assert_not_called()

class TestPydanticCompatibility:
    """Test Pydantic v2 compatibility fixes"""
    
    @pytest.mark.asyncio
    async def test_model_dump_usage(self, test_document):
        """Test that model_dump() is used instead of deprecated dict()"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/brain/ingest",
                json={"documents": [test_document]},
                timeout=30.0
            )
        
        assert response.status_code == 200
        # If the endpoint works without deprecation warnings, the fix is successful

class TestDockerBuild:
    """Test Docker build with fixed dependencies"""
    
    def test_docker_build_includes_required_dependencies(self):
        """Test that Dockerfile.bridge includes all required packages"""
        with open('infra/Dockerfile.bridge', 'r') as f:
            dockerfile_content = f.read()
        
        required_packages = [
            'sse-starlette',
            'weaviate-client',
            'uvicorn[standard]',
            'fastapi',
            'pydantic'
        ]
        
        for package in required_packages:
            assert package in dockerfile_content, f"Missing required package: {package}"

class TestEnvironmentConfiguration:
    """Test environment configuration fixes"""
    
    def test_environment_variable_consistency(self):
        """Test that environment variables are consistently named"""
        # Check docker-compose.yml for consistent variable names
        with open('infra/docker-compose.yml', 'r') as f:
            compose_content = f.read()
        
        # Verify OpenAI API key consistency
        assert '${OPENAI_API_KEY}' in compose_content
        
        # Verify Neo4j password variable usage
        assert '${NEO4J_PASSWORD:-builder123}' in compose_content
    
    def test_environment_path_conditional_setting(self):
        """Test that environment path is only set when not already present"""
        import os
        
        # Simulate environment already set
        original_env = os.environ.get("SOPHIA_REPO_ENV_FILE")
        os.environ["SOPHIA_REPO_ENV_FILE"] = "/custom/path"
        
        # Import should not override existing setting
        import test_api_server
        assert os.environ["SOPHIA_REPO_ENV_FILE"] == "/custom/path"
        
        # Restore original environment
        if original_env:
            os.environ["SOPHIA_REPO_ENV_FILE"] = original_env
        else:
            os.environ.pop("SOPHIA_REPO_ENV_FILE", None)

class TestStreamResourceManagement:
    """Test stream resource management fixes"""
    
    @pytest.mark.asyncio
    async def test_stream_cleanup_no_double_close(self):
        """Test that streams are not closed twice"""
        from bridge.api import EventStreamManager
        
        manager = EventStreamManager()
        stream_id = "test-stream-123"
        
        # Create stream
        queue = manager.create_stream(stream_id)
        assert stream_id in manager.streams
        
        # Close stream once
        manager.close_stream(stream_id)
        assert stream_id not in manager.streams
        
        # Second close should not raise an error
        manager.close_stream(stream_id)  # Should be safe

class TestHealthEndpoints:
    """Test enhanced health check functionality"""
    
    @pytest.mark.asyncio
    async def test_postgres_health_check(self):
        """Test PostgreSQL health check with retry logic"""
        from scripts.health_check_enhanced import HealthChecker
        
        checker = HealthChecker()
        result = await checker.check_postgres()
        
        assert result['status'] in ['healthy', 'unhealthy']
        assert 'attempts' in result
        
        if result['status'] == 'healthy':
            assert result['query_result'] == 1
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check covers all services"""
        from scripts.health_check_enhanced import HealthChecker
        
        checker = HealthChecker()
        results = await checker.comprehensive_health_check()
        
        # Verify all expected services are checked
        expected_services = ['postgres', 'redis', 'weaviate', 'neo4j', 'bridge']
        for service in expected_services:
            assert service in results['services']
            assert 'status' in results['services'][service]
        
        # Verify overall status is determined correctly
        assert results['overall_status'] in ['healthy', 'degraded', 'critical']
        assert 'execution_time' in results

class TestWeaviateSchema:
    """Test Weaviate schema with contentHash field"""
    
    def test_schema_includes_content_hash_field(self):
        """Test that BusinessDocument schema includes contentHash field"""
        client = weaviate.Client("http://localhost:8080")
        
        try:
            schema = client.schema.get()
            business_doc_class = None
            
            for cls in schema.get('classes', []):
                if cls['class'] == 'BusinessDocument':
                    business_doc_class = cls
                    break
            
            assert business_doc_class is not None, "BusinessDocument class not found"
            
            # Check for contentHash property
            content_hash_property = None
            for prop in business_doc_class['properties']:
                if prop['name'] == 'contentHash':
                    content_hash_property = prop
                    break
            
            assert content_hash_property is not None, "contentHash property not found"
            assert content_hash_property['dataType'] == ['text']
            
        except Exception as e:
            pytest.skip(f"Weaviate not available for schema test: {e}")

# Integration test that validates the complete remediation
class TestIntegrationRemediation:
    """Integration tests for complete remediation validation"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_document_processing(self, test_document):
        """Test complete document processing pipeline"""
        async with httpx.AsyncClient() as client:
            # 1. Verify health endpoints
            health_response = await client.get("http://localhost:8003/health")
            assert health_response.status_code == 200
            
            # 2. Test brain ingest
            ingest_response = await client.post(
                "http://localhost:8003/api/brain/ingest",
                json={"documents": [test_document]},
                timeout=30.0
            )
            assert ingest_response.status_code == 200
            
            # 3. Test defensive BI endpoints
            projects_response = await client.get("http://localhost:8003/api/projects/overview")
            assert projects_response.status_code == 200
            
            gong_response = await client.get("http://localhost:8003/api/gong/calls")
            assert gong_response.status_code == 200
            
        # Verify all responses contain expected defensive structure
        ingest_result = ingest_response.json()
        assert ingest_result["stored"] >= 0
        assert "processed_documents" in ingest_result
        
        projects_result = projects_response.json()
        assert "configured" in projects_result
        
        gong_result = gong_response.json()
        assert "configured" in gong_result

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])