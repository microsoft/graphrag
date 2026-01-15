# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'TextEmbeddingResult' model and run_embed_text method definition."""

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from graphrag_chunking.token_chunker import split_text_on_tokens
from graphrag_llm.tokenizer import Tokenizer

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.utils.is_null import is_null
from graphrag.logger.progress import ProgressTicker, progress_ticker

if TYPE_CHECKING:
    from graphrag_llm.embedding import LLMEmbedding

logger = logging.getLogger(__name__)


@dataclass
class TextEmbeddingResult:
    """Text embedding result class definition."""

    embeddings: list[list[float] | None] | None


async def run_embed_text(
    input: list[str],
    callbacks: WorkflowCallbacks,
    model: "LLMEmbedding",
    tokenizer: Tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
) -> TextEmbeddingResult:
    """Run the Claim extraction chain."""
    if is_null(input):
        return TextEmbeddingResult(embeddings=None)

    semaphore: asyncio.Semaphore = asyncio.Semaphore(num_threads)

    # Break up the input texts. The sizes here indicate how many snippets are in each input text
    texts, input_sizes = _prepare_embed_texts(input, tokenizer, batch_max_tokens)
    text_batches = _create_text_batches(
        texts,
        tokenizer,
        batch_size,
        batch_max_tokens,
    )
    logger.info(
        "embedding %d inputs via %d snippets using %d batches. max_batch_size=%d, batch_max_tokens=%d",
        len(input),
        len(texts),
        len(text_batches),
        batch_size,
        batch_max_tokens,
    )
    ticker = progress_ticker(
        callbacks.progress,
        len(text_batches),
        description="generate embeddings progress: ",
    )

    # Embed each chunk of snippets
    embeddings = await _execute(model, text_batches, ticker, semaphore)
    embeddings = _reconstitute_embeddings(embeddings, input_sizes)

    return TextEmbeddingResult(embeddings=embeddings)


async def _execute(
    model: "LLMEmbedding",
    chunks: list[list[str]],
    tick: ProgressTicker,
    semaphore: asyncio.Semaphore,
) -> list[list[float]]:
    async def embed(chunk: list[str]):
        async with semaphore:
            embeddings_response = await model.embedding_async(input=chunk)
            result = np.array(embeddings_response.embeddings)
            tick(1)
        return result

    futures = [embed(chunk) for chunk in chunks]
    results = await asyncio.gather(*futures)
    # merge results in a single list of lists (reduce the collect dimension)
    return [item for sublist in results for item in sublist]


def _create_text_batches(
    texts: list[str],
    tokenizer: Tokenizer,
    max_batch_size: int,
    max_batch_tokens: int,
) -> list[list[str]]:
    """Create batches of texts to embed."""
    # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
    # According to this embeddings reference, Azure limits us to 16 concurrent embeddings and 8191 tokens per request
    result = []
    current_batch = []
    current_batch_tokens = 0

    for text in texts:
        token_count = tokenizer.num_tokens(text)
        if (
            len(current_batch) >= max_batch_size
            or current_batch_tokens + token_count > max_batch_tokens
        ):
            result.append(current_batch)
            current_batch = []
            current_batch_tokens = 0

        current_batch.append(text)
        current_batch_tokens += token_count

    if len(current_batch) > 0:
        result.append(current_batch)

    return result


def _prepare_embed_texts(
    input: list[str],
    tokenizer: Tokenizer,
    batch_max_tokens: int = 8191,
    chunk_overlap: int = 100,
) -> tuple[list[str], list[int]]:
    sizes: list[int] = []
    snippets: list[str] = []

    for text in input:
        split_texts = split_text_on_tokens(
            text,
            chunk_size=batch_max_tokens,
            chunk_overlap=chunk_overlap,
            encode=tokenizer.encode,
            decode=tokenizer.decode,
        )
        split_texts = [text for text in split_texts if len(text) > 0]
        sizes.append(len(split_texts))
        snippets.extend(split_texts)

    return snippets, sizes


def _reconstitute_embeddings(
    raw_embeddings: list[list[float]], sizes: list[int]
) -> list[list[float] | None]:
    """Reconstitute the embeddings into the original input texts."""
    embeddings: list[list[float] | None] = []
    cursor = 0
    for size in sizes:
        if size == 0:
            embeddings.append(None)
        elif size == 1:
            embedding = raw_embeddings[cursor]
            embeddings.append(embedding)
            cursor += 1
        else:
            chunk = raw_embeddings[cursor : cursor + size]
            average = np.average(chunk, axis=0)
            normalized = average / np.linalg.norm(average)
            embeddings.append(normalized.tolist())
            cursor += size
    return embeddings
