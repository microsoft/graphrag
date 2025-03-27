# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Integration tests for CosmosDB vector store implementation."""

import sys
import json
from datetime import datetime

import pytest

from graphrag.vector_stores.base import VectorStoreDocument
from graphrag.vector_stores.cosmosdb import CosmosDBVectoreStore

# cspell:disable-next-line well-known-key
WELL_KNOWN_COSMOS_CONNECTION_STRING = "AccountEndpoint=https://127.0.0.1:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

# the cosmosdb emulator is only available on windows runners at this time
if not sys.platform.startswith("win"):
    pytest.skip(
        "encountered windows-only tests -- will skip for now", allow_module_level=True
    )

async def test_vector_store_operations():
    """Test basic vector store operations with CosmosDB."""
    vector_store = CosmosDBVectoreStore(
        collection_name="testvector",
    )
    
    try:
        vector_store.connect(
            connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
            database_name="testdb",
        )
        
        # Create test documents
        docs = [
            VectorStoreDocument(
                id="doc1",
                text="This is document 1",
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                attributes={"title": "Doc 1", "category": "test"},
            ),
            VectorStoreDocument(
                id="doc2", 
                text="This is document 2", 
                vector=[0.2, 0.3, 0.4, 0.5, 0.6],
                attributes={"title": "Doc 2", "category": "test"},
            ),
        ]
        
        # Load documents
        vector_store.load_documents(docs)
        
        # Test filtering by ID
        vector_store.filter_by_id(["doc1"])
        
        # Test search by ID
        doc = vector_store.search_by_id("doc1")
        assert doc.id == "doc1"
        assert doc.text == "This is document 1"
        assert doc.vector == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert doc.attributes["title"] == "Doc 1"
        
        # Define a simple text embedder function for testing
        def mock_embedder(text: str) -> list[float]:
            return [0.1, 0.2, 0.3, 0.4, 0.5]  # Return fixed embedding
            
        # Test vector similarity search
        vector_results = vector_store.similarity_search_by_vector([0.1, 0.2, 0.3, 0.4, 0.5], k=2)
        assert len(vector_results) > 0
        
        # Test text similarity search
        text_results = vector_store.similarity_search_by_text("test query", mock_embedder, k=2)
        assert len(text_results) > 0
    finally:
        # Clean up
        await vector_store.clear()


async def test_child():
    """Test child container functionality."""
    parent = CosmosDBVectoreStore(
        collection_name="testparent",
    )
    try:
        parent.connect(
            connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
            database_name="testchild",
        )
        
        # Test that child returns the correct type
        child = parent.child("testchild")
        assert isinstance(child, CosmosDBVectoreStore)
    finally:
        await parent.clear()


async def test_clear():
    """Test clearing the vector store."""
    vector_store = CosmosDBVectoreStore(
        collection_name="testclear",
    )
    try:
        vector_store.connect(
            connection_string=WELL_KNOWN_COSMOS_CONNECTION_STRING,
            database_name="testclear",
        )
        
        # Create a document
        doc = VectorStoreDocument(
            id="test",
            text="Test document",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            attributes={"title": "Test Doc"},
        )
        
        # Load document and verify
        vector_store.load_documents([doc])
        result = vector_store.search_by_id("test")
        assert result.id == "test"
        
        # Clear and verify document is removed
        await vector_store.clear()
        
        # After clear, container should be gone, so search_by_id would fail
        # We just verify container client is None as evidence of cleanup
        assert vector_store._container_client is None
        assert vector_store._database_client is None
    finally:
        await vector_store.clear()