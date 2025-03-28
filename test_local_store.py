"""Test script for local vector store."""

import asyncio
from pathlib import Path

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.types import TextEmbedder
from graphrag.vector_stores.base import VectorStoreDocument
from graphrag.vector_stores.factory import VectorStoreType, get_vector_store


class MockEmbedder(TextEmbedder):
    """Mock text embedder for testing."""

    def __call__(self, text: str) -> list[float]:
        """Generate a mock embedding."""
        # Simple mock embedding: convert text to ASCII values and normalize
        return [ord(c) / 255.0 for c in text[:10]]  # Use first 10 chars


async def main():
    """Test the local vector store."""
    # Create necessary directories
    Path("data/vector_store").mkdir(parents=True, exist_ok=True)
    Path("input").mkdir(exist_ok=True)
    Path("cache").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    # Initialize vector store
    store = get_vector_store(
        store_type=VectorStoreType.Local,
        collection_name="test_collection",
        db_uri="./data/vector_store",
    )

    # Create test documents
    test_docs = [
        VectorStoreDocument(
            id="doc1",
            text="This is a test document about machine learning",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            attributes={"category": "ml"},
        ),
        VectorStoreDocument(
            id="doc2",
            text="This is another document about artificial intelligence",
            vector=[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1],
            attributes={"category": "ai"},
        ),
    ]

    # Load documents
    store.load_documents(test_docs)

    # Test similarity search
    embedder = MockEmbedder()
    query = "machine learning"
    results = store.similarity_search_by_text(query, embedder, k=2)

    print("\nSearch Results:")
    for result in results:
        print(f"\nDocument: {result.document.text}")
        print(f"Score: {result.score}")
        print(f"Attributes: {result.document.attributes}")

    # Test search by ID
    doc = store.search_by_id("doc1")
    print(f"\nDocument by ID: {doc.text}")


if __name__ == "__main__":
    asyncio.run(main()) 