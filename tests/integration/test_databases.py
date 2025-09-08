"""
Database Integration Tests
Tests Neon PostgreSQL, Upstash Redis, and Qdrant Cloud connectivity
"""

import pytest
import os
import asyncio
import asyncpg
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

class TestDatabaseIntegrations:

    @pytest.mark.asyncio
    async def test_neon_postgresql_connection(self):
        """Test Neon PostgreSQL database connection"""
        database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
        if not database_url:
            pytest.skip("NEON_DATABASE_URL not set")

        try:
            conn = await asyncpg.connect(database_url)

            # Test basic query
            result = await conn.fetchval('SELECT version()')
            assert 'PostgreSQL' in result

            # Test table creation and operations
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')

            # Insert test data
            await conn.execute(
                'INSERT INTO test_table (name) VALUES ($1)',
                'neon_integration_test'
            )

            # Query test data
            test_data = await conn.fetchrow(
                'SELECT * FROM test_table WHERE name = $1',
                'neon_integration_test'
            )
            assert test_data['name'] == 'neon_integration_test'

            # Cleanup
            await conn.execute('DROP TABLE test_table')
            await conn.close()

            print(f"✅ Neon PostgreSQL connection successful: {result}")

        except Exception as e:
            pytest.fail(f"Neon PostgreSQL connection failed: {e}")

    @pytest.mark.asyncio
    async def test_upstash_redis_connection(self):
        """Test Upstash Redis connection"""
        redis_url = os.getenv('UPSTASH_REDIS_URL') or os.getenv('REDIS_URL')
        redis_token = os.getenv('UPSTASH_REDIS_TOKEN')

        if not redis_url:
            pytest.skip("UPSTASH_REDIS_URL not set")

        try:
            # Use HTTP API for Upstash Redis
            headers = {}
            if redis_token:
                headers['Authorization'] = f'Bearer {redis_token}'

            async with httpx.AsyncClient() as client:
                # Test SET operation
                set_response = await client.post(
                    f"{redis_url}/set/test_key/upstash_integration_test",
                    headers=headers
                )
                assert set_response.status_code == 200

                # Test GET operation
                get_response = await client.get(
                    f"{redis_url}/get/test_key",
                    headers=headers
                )
                assert get_response.status_code == 200
                data = get_response.json()
                assert data['result'] == 'upstash_integration_test'

                # Test SETEX (with expiration)
                setex_response = await client.post(
                    f"{redis_url}/setex/test_expire/1/expire_test",
                    headers=headers
                )
                assert setex_response.status_code == 200

                # Wait for expiration
                await asyncio.sleep(1.1)
                expired_response = await client.get(
                    f"{redis_url}/get/test_expire",
                    headers=headers
                )
                expired_data = expired_response.json()
                assert expired_data['result'] is None

                # Test HSET operation
                hset_response = await client.post(
                    f"{redis_url}/hset/test_hash/field1/value1",
                    headers=headers
                )
                assert hset_response.status_code == 200

                # Test HGET operation
                hget_response = await client.get(
                    f"{redis_url}/hget/test_hash/field1",
                    headers=headers
                )
                assert hget_response.status_code == 200
                hash_data = hget_response.json()
                assert hash_data['result'] == 'value1'

                # Cleanup
                await client.post(f"{redis_url}/del/test_key", headers=headers)
                await client.post(f"{redis_url}/del/test_hash", headers=headers)

                print("✅ Upstash Redis connection successful")

        except Exception as e:
            pytest.fail(f"Upstash Redis connection failed: {e}")

    @pytest.mark.asyncio
    async def test_qdrant_cloud_connection(self):
        """Test Qdrant Cloud vector database connection"""
        qdrant_url = os.getenv('QDRANT_CLOUD_URL') or os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')

        if not qdrant_url:
            pytest.skip("QDRANT_CLOUD_URL not set")

        try:
            headers = {'Content-Type': 'application/json'}
            if qdrant_api_key:
                headers['api-key'] = qdrant_api_key

            async with httpx.AsyncClient() as client:
                # Test connection
                response = await client.get(f"{qdrant_url}/", headers=headers)
                assert response.status_code == 200

                # Test collections endpoint
                response = await client.get(f"{qdrant_url}/collections", headers=headers)
                assert response.status_code == 200

                # Create test collection
                collection_name = "test_integration_collection"
                create_response = await client.put(
                    f"{qdrant_url}/collections/{collection_name}",
                    headers=headers,
                    json={
                        "vectors": {
                            "size": 384,
                            "distance": "Cosine"
                        }
                    }
                )
                assert create_response.status_code in [200, 409]  # 409 if already exists

                # Test vector insertion
                test_vector = [0.1] * 384  # 384-dimensional test vector
                insert_response = await client.put(
                    f"{qdrant_url}/collections/{collection_name}/points",
                    headers=headers,
                    json={
                        "points": [
                            {
                                "id": 1,
                                "vector": test_vector,
                                "payload": {"test": "qdrant_cloud_integration"}
                            }
                        ]
                    }
                )
                assert insert_response.status_code == 200

                # Test vector search
                search_response = await client.post(
                    f"{qdrant_url}/collections/{collection_name}/points/search",
                    headers=headers,
                    json={
                        "vector": test_vector,
                        "limit": 1
                    }
                )
                assert search_response.status_code == 200
                search_data = search_response.json()
                assert len(search_data["result"]) > 0
                assert search_data["result"][0]["payload"]["test"] == "qdrant_cloud_integration"

                # Cleanup - delete test collection
                delete_response = await client.delete(
                    f"{qdrant_url}/collections/{collection_name}",
                    headers=headers
                )
                assert delete_response.status_code == 200

                print("✅ Qdrant Cloud connection successful")

        except Exception as e:
            pytest.fail(f"Qdrant Cloud connection failed: {e}")

    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Test database performance benchmarks"""
        database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
        redis_url = os.getenv('UPSTASH_REDIS_URL') or os.getenv('REDIS_URL')
        redis_token = os.getenv('UPSTASH_REDIS_TOKEN')

        if not database_url or not redis_url:
            pytest.skip("Database URLs not set")

        try:
            # Neon PostgreSQL performance test
            conn = await asyncpg.connect(database_url)

            import time
            start_time = time.time()
            for i in range(100):
                await conn.fetchval('SELECT $1', i)
            pg_time = time.time() - start_time

            await conn.close()

            # Upstash Redis performance test
            headers = {}
            if redis_token:
                headers['Authorization'] = f'Bearer {redis_token}'

            async with httpx.AsyncClient() as client:
                start_time = time.time()
                for i in range(100):
                    await client.post(f"{redis_url}/set/perf_test_{i}/{i}", headers=headers)
                    await client.get(f"{redis_url}/get/perf_test_{i}", headers=headers)
                redis_time = time.time() - start_time

                # Cleanup
                for i in range(100):
                    await client.post(f"{redis_url}/del/perf_test_{i}", headers=headers)

            print(f"✅ Database performance test completed:")
            print(f"   Neon PostgreSQL: {pg_time:.3f}s for 100 operations")
            print(f"   Upstash Redis: {redis_time:.3f}s for 100 operations")

            # Assert reasonable performance (cloud services may be slower)
            assert pg_time < 10.0, f"Neon PostgreSQL too slow: {pg_time}s"
            assert redis_time < 5.0, f"Upstash Redis too slow: {redis_time}s"

        except Exception as e:
            pytest.fail(f"Database performance test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
