"""Advanced test script for local vector store."""

import asyncio
import os
import random
import shutil
import time
from pathlib import Path

from graphrag.data_model.types import TextEmbedder
from graphrag.vector_stores.base import VectorStoreDocument
from graphrag.vector_stores.factory import VectorStoreType, get_vector_store


class MockEmbedder(TextEmbedder):
    """Mock text embedder for testing."""

    def __call__(self, text: str) -> list[float]:
        """Generate a mock embedding."""
        # Simple mock embedding based on hash of the text
        import hashlib
        
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash bytes to normalized floats
        vec = [float(b) / 255.0 for b in hash_bytes]
        # Pad or truncate to 10 dimensions
        return vec[:10] if len(vec) >= 10 else vec + [0.0] * (10 - len(vec))


def generate_test_docs(count: int) -> list[VectorStoreDocument]:
    """Generate test documents with random content."""
    categories = ["ml", "ai", "nlp", "cv", "rl"]
    topics = ["machine learning", "neural networks", "deep learning", 
              "computer vision", "natural language processing", 
              "reinforcement learning", "transformers", "attention"]
    
    docs = []
    for i in range(count):
        category = random.choice(categories)
        topic1 = random.choice(topics)
        topic2 = random.choice(topics)
        
        text = f"Document {i+1}: This is a test document about {topic1} and {topic2}."
        
        # Create a deterministic but varied vector
        vec = [
            (i % 10) / 10.0,
            ((i + 1) % 10) / 10.0,
            ((i + 2) % 10) / 10.0,
            ((i + 3) % 10) / 10.0,
            ((i + 4) % 10) / 10.0,
            ((i + 5) % 10) / 10.0,
            ((i + 6) % 10) / 10.0,
            ((i + 7) % 10) / 10.0,
            ((i + 8) % 10) / 10.0,
            ((i + 9) % 10) / 10.0,
        ]
        
        doc = VectorStoreDocument(
            id=f"doc_{i+1}",
            text=text,
            vector=vec,
            attributes={"category": category, "length": len(text)}
        )
        docs.append(doc)
    
    return docs


async def test_basic_functionality():
    """Test basic functionality."""
    print("\n--- Testing Basic Functionality ---")
    
    # Create store
    store = get_vector_store(
        store_type=VectorStoreType.Local,
        collection_name="test_basic",
        db_uri="./data/vector_store"
    )
    
    # Generate and load documents
    docs = generate_test_docs(5)
    store.load_documents(docs)
    
    # Test search by ID
    doc = store.search_by_id("doc_1")
    print(f"Document by ID: {doc.text}")
    
    # Test similarity search
    embedder = MockEmbedder()
    query = "machine learning"
    results = store.similarity_search_by_text(query, embedder, k=2)
    
    print("\nSearch Results:")
    for result in results:
        print(f"\nDocument: {result.document.text}")
        print(f"Score: {result.score}")
        print(f"Attributes: {result.document.attributes}")


async def test_large_dataset():
    """Test with a larger dataset."""
    print("\n--- Testing Large Dataset ---")
    
    # Create store with chunking and compression
    store = get_vector_store(
        store_type=VectorStoreType.Local,
        collection_name="test_large",
        db_uri="./data/vector_store",
        max_chunk_size=50,
        compression_enabled=True
    )
    
    # Generate and load documents in chunks
    doc_count = 200
    print(f"Generating {doc_count} documents...")
    docs = generate_test_docs(doc_count)
    
    print("Loading documents...")
    start_time = time.time()
    store.load_documents_in_chunks(docs, chunk_size=50)
    load_time = time.time() - start_time
    print(f"Documents loaded in {load_time:.2f} seconds")
    
    # Test search
    embedder = MockEmbedder()
    query = "neural networks"
    
    print("Searching...")
    start_time = time.time()
    results = store.similarity_search_by_text(query, embedder, k=5)
    search_time = time.time() - start_time
    print(f"Search completed in {search_time:.2f} seconds")
    
    print(f"\nTop result: {results[0].document.text}")
    print(f"Score: {results[0].score}")
    
    # Get stats
    stats = store.get_stats()
    print("\nStore Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")


async def test_filter_by_attributes():
    """Test filtering by attributes."""
    print("\n--- Testing Filter by Attributes ---")
    
    # Create store
    store = get_vector_store(
        store_type=VectorStoreType.Local,
        collection_name="test_filters",
        db_uri="./data/vector_store"
    )
    
    # Generate and load documents
    docs = generate_test_docs(100)
    store.load_documents(docs)
    
    # Filter by category
    embedder = MockEmbedder()
    query = "machine learning"
    
    print("\nWithout filter:")
    results = store.similarity_search_by_text(query, embedder, k=3)
    for result in results:
        print(f"Document: {result.document.text}")
        print(f"Category: {result.document.attributes['category']}")
    
    print("\nWith 'ml' category filter:")
    store.filter_by_attributes({"category": "ml"})
    results = store.similarity_search_by_text(query, embedder, k=3)
    for result in results:
        print(f"Document: {result.document.text}")
        print(f"Category: {result.document.attributes['category']}")


async def test_export_import():
    """Test export and import functionality."""
    print("\n--- Testing Export and Import ---")
    
    # Create source store
    source_store = get_vector_store(
        store_type=VectorStoreType.Local,
        collection_name="test_export",
        db_uri="./data/vector_store"
    )
    
    # Generate and load documents
    docs = generate_test_docs(20)
    source_store.load_documents(docs)
    
    # Export data
    export_path = source_store.export_data("./data/vector_store/export_test.json")
    print(f"Data exported to {export_path}")
    
    # Create target store
    target_store = get_vector_store(
        store_type=VectorStoreType.Local,
        collection_name="test_import",
        db_uri="./data/vector_store"
    )
    
    # Import data
    doc_count = target_store.import_data(export_path)
    print(f"Imported {doc_count} documents")
    
    # Verify imported data
    print(f"Target store document count: {target_store.get_document_count()}")
    doc = target_store.search_by_id("doc_1")
    print(f"Sample document: {doc.text}")


async def main():
    """Run all tests."""
    # Create necessary directories
    test_dir = Path("data/vector_store")
    
    # Clear previous test data
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Run tests
    await test_basic_functionality()
    await test_large_dataset()
    await test_filter_by_attributes()
    await test_export_import()
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 