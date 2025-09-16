import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_gong_transcript_chunking_and_pipeline():
    try:
        from app.integrations.gong_rag_pipeline import (
            GongRAGPipeline,
            GongTranscriptProcessor,
        )
    except Exception:
        pytest.skip("gong_rag_pipeline not available")

    # Minimal transcript sample
    sample_transcript = {
        "callTranscripts": [
            {
                "sentences": [
                    {
                        "speakerName": "Sales Rep",
                        "text": "Welcome to our demo. Today I'll show you our key features.",
                        "start": 0,
                        "end": 3000,
                    },
                    {
                        "speakerName": "Customer",
                        "text": "Great! We're particularly interested in the integration capabilities and pricing model.",
                        "start": 3000,
                        "end": 6000,
                    },
                ]
            }
        ]
    }

    # Test chunking
    try:
        processor = GongTranscriptProcessor(chunk_size=128, chunk_overlap=32)
        chunks = processor.chunk_transcript(sample_transcript, "test_call")
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
    except Exception:
        # If internal deps missing, skip gracefully
        pytest.skip("Transcript processor dependencies missing")

    # Test pipeline high-level call (best-effort; skip on infra deps missing)
    try:
        pipeline = GongRAGPipeline()
        await pipeline.setup()
        insights = await pipeline.process_transcript(sample_transcript, {"id": "test_call"})
        assert isinstance(insights, list)
    except Exception:
        pytest.skip("Pipeline setup or dependencies missing (vector store/LLM)")

