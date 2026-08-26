"""Tests for GraphRAG API."""
import pytest
from fastapi.testclient import TestClient
from graphrag_api.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_local(client):
    """Test local query."""
    response = client.post("/query", json={
        "query": "What happened?",
        "mode": "local"
    })
    assert response.status_code == 200
    assert "answer" in response.json()


def test_query_global(client):
    """Test global query."""
    response = client.post("/query", json={
        "query": "What are the main themes?",
        "mode": "global"
    })
    assert response.status_code == 200


def test_conversation(client):
    """Test multi-turn conversation."""
    response = client.post("/conversation", json={
        "query": "Tell me about X",
        "history": [
            {
                "role": "user",
                "content": "What is GraphRAG?"
            },
            {
                "role": "assistant", 
                "content": "GraphRAG is a graph-based RAG system"
            }
        ]
    })
    assert response.status_code == 200
