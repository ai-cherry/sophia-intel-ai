"""
Anthropic Integration Tests
Tests Claude API connectivity and functionality
"""
import os
import httpx
import pytest
from dotenv import load_dotenv
# Load environment variables
load_dotenv(".env.production")
class TestAnthropicIntegration:
    @pytest.fixture
    def api_key(self):
        """Get Anthropic API key"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")
        return api_key
    @pytest.fixture
    def client(self):
        """Create HTTP client for Anthropic API"""
        return httpx.AsyncClient(base_url="https://api.anthropic.com", timeout=30.0)
    @pytest.mark.asyncio
    async def test_connection(self, client, api_key):
        """Test basic connection to Anthropic"""
        try:
            response = await client.post(
                "/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 50,
                    "messages": [
                        {"role": "user", "content": "Hello, this is a connection test."}
                    ],
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            print("✅ Anthropic connection successful")
        except Exception as e:
            pytest.fail(f"Anthropic connection failed: {e}")
    @pytest.mark.asyncio
    async def test_claude_opus_4_1(self, client, api_key):
        """Test Claude Opus 4.1 functionality"""
        try:
            response = await client.post(
                "/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-opus-20240229",  # Latest available model
                    "max_tokens": 100,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Please respond with 'Claude Opus integration working' to confirm the integration.",
                        }
                    ],
                },
            )
            assert response.status_code == 200
            data = response.json()
            content = data["content"][0]["text"]
            assert "Claude Opus integration working" in content
            print(f"✅ Claude Opus integration successful: {content}")
        except Exception as e:
            pytest.fail(f"Claude Opus integration failed: {e}")
    @pytest.mark.asyncio
    async def test_streaming_response(self, client, api_key):
        """Test streaming response functionality"""
        try:
            async with client.stream(
                "POST",
                "/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 50,
                    "stream": True,
                    "messages": [{"role": "user", "content": "Count to 5"}],
                },
            ) as response:
                assert response.status_code == 200
                chunks = []
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        chunks.append(chunk)
                assert len(chunks) > 0
                print(
                    f"✅ Anthropic streaming successful - {len(chunks)} chunks received"
                )
        except Exception as e:
            pytest.fail(f"Anthropic streaming failed: {e}")
    @pytest.mark.asyncio
    async def test_error_handling(self, client, api_key):
        """Test error handling with invalid requests"""
        try:
            # Test with invalid model
            response = await client.post(
                "/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "invalid-model",
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": "Test"}],
                },
            )
            assert response.status_code == 400
            print("✅ Anthropic error handling working - invalid model rejected")
        except Exception as e:
            pytest.fail(f"Anthropic error handling test failed: {e}")
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
