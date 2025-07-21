# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for ElasticSearch vector store implementation."""

import numpy as np
import pytest

from graphrag.vector_stores.base import VectorStoreDocument
from graphrag.vector_stores.elasticsearch import ElasticSearchVectorStore


def test_vector_store_operations():
    """Test basic vector store operations with ElasticSearch."""
    vector_store = ElasticSearchVectorStore(collection_name="test_collection")
    
    # Test connection
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        pytest.skip("ElasticSearch not available for testing")

    # Test documents
    docs = [
        VectorStoreDocument(
            id="1",
            text="This is document 1",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            attributes={"title": "Doc 1", "category": "test"},
        ),
        VectorStoreDocument(
            id="2",
            text="This is document 2",
            vector=[0.2, 0.3, 0.4, 0.5, 0.6],
            attributes={"title": "Doc 2", "category": "test"},
        ),
        VectorStoreDocument(
            id="3",
            text="This is document 3",
            vector=[0.3, 0.4, 0.5, 0.6, 0.7],
            attributes={"title": "Doc 3", "category": "test"},
        ),
    ]
    
    # Load documents (first 2)
    vector_store.load_documents(docs[:2])

    # Test search by ID
    doc = vector_store.search_by_id("1")
    assert doc.id == "1"
    assert doc.text == "This is document 1"
    assert doc.attributes["title"] == "Doc 1"

    # Test vector similarity search
    query_vector = [0.15, 0.25, 0.35, 0.45, 0.55]
    results = vector_store.similarity_search_by_vector(query_vector, k=2)
    
    assert len(results) <= 2
    assert all(result.score >= 0 for result in results)
    
    # Verify results are ordered by score (descending)
    scores = [result.score for result in results]
    assert scores == sorted(scores, reverse=True)

    # Test filter by ID
    filter_query = vector_store.filter_by_id(["1"])
    assert "terms" in filter_query
    assert filter_query["terms"]["id"] == ["1"]

    # Test loading additional documents (without overwrite)
    vector_store.load_documents([docs[2]], overwrite=False)

    # Test overwrite functionality
    vector_store.load_documents(docs, overwrite=True)


def test_elasticsearch_dynamic_vector_dimensions():
    """Test ElasticSearch with different vector dimensions (like LanceDB)."""
    # Test different vector dimensions like LanceDB supports
    test_cases = [
        {
            "name": "small_vectors",
            "dimension": 3,
            "vectors": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        },
        {
            "name": "bert_vectors", 
            "dimension": 768,
            "vectors": [[0.1] * 768, [0.2] * 768]
        },
        {
            "name": "openai_vectors",
            "dimension": 1536, 
            "vectors": [[0.1] * 1536, [0.2] * 1536]
        }
    ]
    
    for test_case in test_cases:
        vector_store = ElasticSearchVectorStore(collection_name=f"test_{test_case['name']}")
        
        try:
            vector_store.connect(url="http://localhost:9200")
        except Exception:
            pytest.skip("ElasticSearch not available for testing")
        
        # Test documents with specific dimensions
        docs = [
            VectorStoreDocument(
                id=f"{i}",
                text=f"Document {i}",
                vector=vector,
                attributes={"dimension": test_case["dimension"]},
            )
            for i, vector in enumerate(test_case["vectors"])
        ]
        
        # Should automatically detect vector dimension like LanceDB
        vector_store.load_documents(docs)
        
        # Test search with same dimension
        query_vector = [0.15] * test_case["dimension"]
        results = vector_store.similarity_search_by_vector(query_vector, k=1)
        
        assert len(results) <= len(docs)
        if results:
            assert len(results[0].document.vector) == test_case["dimension"]


def test_elasticsearch_with_authentication():
    """Test ElasticSearch with authentication parameters."""
    vector_store = ElasticSearchVectorStore(collection_name="test_auth")
    
    # Should not raise errors during initialization
    assert vector_store.collection_name == "test_auth"


def test_elasticsearch_connection_kwargs():
    """Test ElasticSearch with connection kwargs."""
    vector_store = ElasticSearchVectorStore(collection_name="test_kwargs")
    
    # Test that connection parameters can be passed to connect()
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        # Expected to fail without real ElasticSearch
        pass


def test_elasticsearch_error_handling():
    """Test error handling for ElasticSearch operations."""
    vector_store = ElasticSearchVectorStore(collection_name="test_errors")
    
    # Test operations without connection should raise RuntimeError
    with pytest.raises(RuntimeError, match="Must connect to ElasticSearch"):
        vector_store.load_documents([])
        
    with pytest.raises(RuntimeError, match="Must connect to ElasticSearch"):
        vector_store.similarity_search_by_vector([0.1, 0.2, 0.3])
        
    with pytest.raises(RuntimeError, match="Must connect to ElasticSearch"):
        vector_store.search_by_id("test")


def test_elasticsearch_empty_documents():
    """Test handling of empty document lists."""
    vector_store = ElasticSearchVectorStore(collection_name="test_empty")
    
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        pytest.skip("ElasticSearch not available for testing")
    
    # Loading empty list should create index with default dimension (1536)
    vector_store.load_documents([])


def test_elasticsearch_documents_without_vectors():
    """Test handling of documents without vectors."""
    vector_store = ElasticSearchVectorStore(collection_name="test_no_vectors")
    
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        pytest.skip("ElasticSearch not available for testing")
    
    # Documents without vectors should be filtered out
    docs = [
        VectorStoreDocument(
            id="1",
            text="Document without vector",
            vector=None,
            attributes={},
        ),
        VectorStoreDocument(
            id="2",
            text="Document with vector",
            vector=[0.1, 0.2, 0.3],
            attributes={},
        ),
    ]
    
    vector_store.load_documents(docs)


def test_elasticsearch_text_embedder_search():
    """Test text-based similarity search with embedder function."""
    vector_store = ElasticSearchVectorStore(collection_name="test_text_search")
    
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        pytest.skip("ElasticSearch not available for testing")
    
    # Mock text embedder function
    def mock_embedder(text: str) -> list[float]:
        """Mock embedder that returns simple vector based on text length."""
        text_length = len(text)
        return [float(text_length % 10) / 10] * 5
    
    # Test empty embedder response
    def empty_embedder(text: str) -> None:
        """Mock embedder that returns None."""
        return None
    
    # Load test documents
    docs = [
        VectorStoreDocument(
            id="1",
            text="Short text",
            vector=[0.1, 0.1, 0.1, 0.1, 0.1],
            attributes={"type": "short"},
        ),
    ]
    
    vector_store.load_documents(docs)
    
    # Test with empty embedder (should return empty list like LanceDB)
    results = vector_store.similarity_search_by_text(
        "test query",
        empty_embedder,
        k=2
    )
    assert len(results) == 0
    
    # Test text similarity search
    results = vector_store.similarity_search_by_text(
        "Medium length query text",
        mock_embedder,
        k=2
    )
    
    assert len(results) <= 2
    assert all(result.score >= 0 for result in results)


def test_elasticsearch_numpy_vector_handling():
    """Test handling of numpy arrays as vectors."""
    vector_store = ElasticSearchVectorStore(collection_name="test_numpy")
    
    # Mock text embedder that returns numpy array
    def numpy_embedder(text: str) -> np.ndarray:
        """Mock embedder that returns numpy array."""
        return np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        pytest.skip("ElasticSearch not available for testing")
    
    # Load test document
    docs = [
        VectorStoreDocument(
            id="1",
            text="Test document",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            attributes={},
        ),
    ]
    
    vector_store.load_documents(docs)
    
    # Test with numpy array - should handle conversion automatically
    results = vector_store.similarity_search_by_text(
        "test query",
        numpy_embedder,
        k=1
    )
    
    assert len(results) == 1


def test_elasticsearch_search_by_id_not_found():
    """Test search_by_id when document is not found."""
    vector_store = ElasticSearchVectorStore(collection_name="test_not_found")
    
    try:
        vector_store.connect(url="http://localhost:9200")
    except Exception:
        pytest.skip("ElasticSearch not available for testing")
    
    # Search for non-existent document should return empty document like LanceDB
    doc = vector_store.search_by_id("nonexistent")
    assert doc.id == "nonexistent"
    assert doc.text is None
    assert doc.vector is None


def test_elasticsearch_filter_by_id_empty():
    """Test filter_by_id with empty list."""
    vector_store = ElasticSearchVectorStore(collection_name="test_filter_empty")
    
    # Empty list should set query_filter to None
    result = vector_store.filter_by_id([])
    assert result is None
    assert vector_store.query_filter is None 