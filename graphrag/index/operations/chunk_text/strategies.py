# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing chunk strategies."""

from collections.abc import Iterable

import nltk
import tiktoken

from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.chunk_text.agentic_chunker import run_semantic_chunker
from graphrag.index.operations.chunk_text.markdown_chunker import MarkdownChunker
from graphrag.index.operations.chunk_text.typing import TextChunk
from graphrag.index.text_splitting.text_splitting import (
    Tokenizer,
    split_multiple_texts_on_tokens,
)
from graphrag.logger.progress import ProgressTicker


def run_tokens(
    input: list[str], config: ChunkingConfig, tick: ProgressTicker
) -> Iterable[TextChunk]:
    """Chunks text into chunks based on encoding tokens."""
    tokens_per_chunk = config.size
    chunk_overlap = config.overlap
    encoding_name = config.encoding_model
    enc = tiktoken.get_encoding(encoding_name)

    def encode(text: str) -> list[int]:
        if not isinstance(text, str):
            text = f"{text}"
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        return enc.decode(tokens)

    return split_multiple_texts_on_tokens(
        input,
        Tokenizer(
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=tokens_per_chunk,
            encode=encode,
            decode=decode,
        ),
        tick,
    )


def run_sentences(
    input: list[str], _config: ChunkingConfig, tick: ProgressTicker
) -> Iterable[TextChunk]:
    """Chunks text into multiple parts by sentence."""
    for doc_idx, text in enumerate(input):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            yield TextChunk(
                text_chunk=sentence,
                source_doc_indices=[doc_idx],
            )
        tick(1)

async def run_markdown(
        input: list[str],
        config: ChunkingConfig,
        tick: ProgressTicker,
        mainConfig: GraphRagConfig
) -> list[TextChunk]:
    """Chunks text into semantically coherent chunks using semantic chunker."""
    results = []
    chunker = MarkdownChunker()

    # Process each input document
    for doc_idx, text in enumerate(input):
        # Get chunks using existing semantic chunker
        chunks = await chunker.run_semantic_chunker(text, mainConfig)

        # Create TextChunk objects for each chunk
        for chunk in chunks:
            results.append(TextChunk(
                text_chunk=chunk,
                source_doc_indices=[doc_idx],
            ))
        tick(1)

    return results