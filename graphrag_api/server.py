"""FastAPI server wrapper for GraphRAG queries."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
from pathlib import Path

# Import GraphRAG's query engine
from graphrag.query.cli import main as graphrag_query
from graphrag.query.context_builder import ContextBuilder
from graphrag.query.llm_client import LLMClient

app = FastAPI(
    title="GraphRAG API",
    description="REST API for querying GraphRAG knowledge graphs",
    version="0.1.0"
)


class QueryRequest(BaseModel):
    """Request body for queries."""
    query: str
    mode: str = "local"  # local or global
    temperature: float = 0.0
    top_p: float = 1.0


class QueryResponse(BaseModel):
    """Response body for queries."""
    answer: str
    citations: List[str]
    search_mode: str
    execution_time_ms: float


class ConversationMessage(BaseModel):
    """Single message in conversation."""
    role: str  # "user" or "assistant"
    content: str
    citations: Optional[List[str]] = None


class ConversationRequest(BaseModel):
    """Request for multi-turn conversation."""
    query: str
    history: List[ConversationMessage] = []
    mode: str = "local"


# Initialize GraphRAG
def init_graphrag(data_path: str):
    """Load GraphRAG index from path."""
    # This will load the GraphRAG knowledge graph
    return ContextBuilder(data_path=Path(data_path))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "GraphRAG API"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the GraphRAG knowledge graph.
    
    Example:
        POST /query
        {
            "query": "What are the main themes?",
            "mode": "local",
            "temperature": 0.0
        }
    """
    try:
        import time
        start = time.time()
        
        # Execute query using GraphRAG
        answer = await execute_query(
            query_text=request.query,
            mode=request.mode,
            temperature=request.temperature
        )
        
        elapsed = (time.time() - start) * 1000
        
        return QueryResponse(
            answer=answer["response"],
            citations=answer.get("citations", []),
            search_mode=request.mode,
            execution_time_ms=elapsed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation")
async def conversation(request: ConversationRequest):
    """
    Multi-turn conversation endpoint.
    Maintains conversation history and context.
    """
    try:
        # Build context from conversation history
        history_context = "\n".join([
            f"{msg.role}: {msg.content}" 
            for msg in request.history
        ])
        
        # Execute query with historical context
        answer = await execute_query(
            query_text=request.query,
            mode=request.mode,
            history_context=history_context
        )
        
        return {
            "response": answer["response"],
            "citations": answer.get("citations", []),
            "conversation_id": "session_123"  # TODO: implement session tracking
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets")
async def list_datasets():
    """List available GraphRAG datasets."""
    # TODO: implement dataset discovery
    return {"datasets": []}


@app.get("/config")
async def get_config():
    """Get current GraphRAG configuration."""
    return {"config": {}}


async def execute_query(query_text: str, mode: str = "local", 
                       temperature: float = 0.0,
                       history_context: Optional[str] = None) -> dict:
    """
    Execute a GraphRAG query.
    
    This wraps the internal GraphRAG query engine.
    """
    # TODO: Implement actual GraphRAG query execution
    # For now, this is a placeholder
    return {
        "response": f"Query received: {query_text}",
        "citations": [],
        "mode": mode
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get data path from environment
    data_root = os.getenv("DATA_ROOT", "./data")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
