from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the embedding service with a sentence-transformer model.
        """
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of texts.
        """
        return self.model.encode(texts, convert_to_tensor=False).tolist()

# Example usage
if __name__ == "__main__":
    embedding_service = EmbeddingService()
    
    sample_texts = [
        "This is the first document.",
        "This document is the second document.",
        "And this is the third one.",
        "Is this the first document?",
    ]
    
    embeddings = embedding_service.generate_embeddings(sample_texts)
    
    print(f"Generated {len(embeddings)} embeddings.")
    print("Sample embedding (first 5 dimensions):")
    print(embeddings[0][:5])