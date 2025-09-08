"""
OpenAI Integration Tests
Tests OpenAI API connectivity and functionality
"""

import asyncio
import os

import pytest
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv(".env.production")


class TestOpenAIIntegration:
    @pytest.fixture
    def client(self):
        """Create OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        return AsyncOpenAI(api_key=api_key)

    @pytest.mark.asyncio
    async def test_connection(self, client):
        """Test basic connection to OpenAI"""
        try:
            models = await client.models.list()
            assert len(models.data) > 0
            print(
                f"✅ OpenAI connection successful - {len(models.data)} models available"
            )
        except Exception as e:
            pytest.fail(f"OpenAI connection failed: {e}")

    @pytest.mark.asyncio
    async def test_chat_completion(self, client):
        """Test chat completion functionality"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, this is a test. Please respond with 'OpenAI integration working'.",
                    }
                ],
                max_tokens=50,
                temperature=0.1,
            )

            assert response.choices[0].message.content
            assert "OpenAI integration working" in response.choices[0].message.content
            print(
                f"✅ OpenAI chat completion successful: {response.choices[0].message.content}"
            )

        except Exception as e:
            pytest.fail(f"OpenAI chat completion failed: {e}")

    @pytest.mark.asyncio
    async def test_embeddings(self, client):
        """Test embeddings functionality"""
        try:
            response = await client.embeddings.create(
                model="text-embedding-ada-002", input="This is a test embedding"
            )

            assert len(response.data) > 0
            assert len(response.data[0].embedding) > 0
            print(
                f"✅ OpenAI embeddings successful - {len(response.data[0].embedding)} dimensions"
            )

        except Exception as e:
            pytest.fail(f"OpenAI embeddings failed: {e}")

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test rate limiting handling"""
        try:
            # Make multiple rapid requests to test rate limiting
            tasks = []
            for i in range(5):
                task = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": f"Test {i}"}],
                    max_tokens=10,
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check that at least some requests succeeded
            successful_responses = [
                r for r in responses if not isinstance(r, Exception)
            ]
            assert len(successful_responses) > 0
            print(
                f"✅ Rate limiting test passed - {len(successful_responses)}/5 requests successful"
            )

        except Exception as e:
            pytest.fail(f"Rate limiting test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
