import json

from fnllm import ChatLLM
from typing import List, Tuple
from dataclasses import dataclass
from typing import Dict, Any
from graphrag.config.load_config import load_config
from pathlib import Path
from graphrag.index.llm.load_llm import load_llm

@dataclass
class ChunkConfig:
    """Configuration for SemanticChunker."""
    max_chunk_size: int = 1000

@dataclass
class SemanticChunk:
    content: str
    context_summary: str
    importance_score: float
    dependencies: List[str]

async def run_semantic_chunker(
    text: str,
    callbacks: Any = None,
    cache: Any = None,
) -> List[str]:
    """Run the semantic chunking strategy."""
    config = load_config(Path('/Users/tgn1kor/suprslay/graphrag/tests/ragtest'), None, {})
    llm_config = config.get_language_model_config(
        config.extract_graph.model_id
    )
    llm = load_llm(
        "semantic_chunker",
        llm_config,
        callbacks=callbacks,
        cache=cache,
    )
    chunker = SemanticChunker(llm)
    return await chunker.chunk_text(text)


class SemanticChunker:
    def __init__(self, llm: ChatLLM):
        """Initialize the SemanticChunker with a ChatLLM instance."""
        self.config = ChunkConfig()
        self.llm = llm

    async def chunk_large_section(self, content: str, max_length: int) -> List[SemanticChunk]:
        """Use LLM to break down content into semantic chunks."""
        prompt = f"""
        Analyze this text content and break it into meaningful chunks of approximately {max_length} words each.
        For each chunk:
        1. Ensure it contains complete thoughts/concepts
        2. Identify key context that future chunks might need
        3. Score its importance (0-1)
        4. List any dependencies on previous content

        Text to analyze: {content}

        Return the analysis as JSON with this structure for each chunk:
        {{
            "chunks": [
                {{
                    "content": "actual chunk text",
                    "context_summary": "key context for understanding subsequent chunks",
                    "importance_score": 0.8,
                    "dependencies": ["list of concepts/context needed from previous chunks"]
                }}
            ]
        }}
        """

        response = await self.llm(
            prompt,
            name="get_chunk_indices",
            json=True
        )
        chunks_data = json.loads(response.output.content)

        return [
            SemanticChunk(
                content=chunk['content'],
                context_summary=chunk['context_summary'],
                importance_score=chunk['importance_score'],
                dependencies=chunk['dependencies']
            )
            for chunk in chunks_data['chunks']
        ]