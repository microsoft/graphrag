# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Streaming text embedding operation."""

import logging
from typing import TYPE_CHECKING, Any

import numpy as np
from graphrag_llm.tokenizer import Tokenizer
from graphrag_storage.tables.table import Table
from graphrag_vectors import VectorStore, VectorStoreDocument

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.embed_text.run_embed_text import run_embed_text

if TYPE_CHECKING:
    from graphrag_llm.embedding import LLMEmbedding

logger = logging.getLogger(__name__)


async def embed_text(
    input_table: Table,
    callbacks: WorkflowCallbacks,
    model: "LLMEmbedding",
    tokenizer: Tokenizer,
    embed_column: str,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store: VectorStore,
    id_column: str = "id",
    output_table: Table | None = None,
) -> int:
    """Embed text from a streaming Table into a vector store."""
    vector_store.create_index()

    buffer: list[dict[str, Any]] = []
    total_rows = 0

    async for row in input_table:
        text = row.get(embed_column)
        if text is None:
            text = ""

        buffer.append({
            id_column: row[id_column],
            embed_column: text,
        })

        if len(buffer) >= batch_size:
            total_rows += await _flush_embedding_buffer(
                buffer,
                embed_column,
                id_column,
                callbacks,
                model,
                tokenizer,
                batch_size,
                batch_max_tokens,
                num_threads,
                vector_store,
                output_table,
            )
            buffer.clear()

    if buffer:
        total_rows += await _flush_embedding_buffer(
            buffer,
            embed_column,
            id_column,
            callbacks,
            model,
            tokenizer,
            batch_size,
            batch_max_tokens,
            num_threads,
            vector_store,
            output_table,
        )

    return total_rows


async def _flush_embedding_buffer(
    buffer: list[dict[str, Any]],
    embed_column: str,
    id_column: str,
    callbacks: WorkflowCallbacks,
    model: "LLMEmbedding",
    tokenizer: Tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store: VectorStore,
    output_table: Table | None,
) -> int:
    """Embed a buffer of rows and load results into the vector store."""
    texts: list[str] = [row[embed_column] for row in buffer]
    ids: list[str] = [row[id_column] for row in buffer]

    result = await run_embed_text(
        texts,
        callbacks,
        model,
        tokenizer,
        batch_size,
        batch_max_tokens,
        num_threads,
    )

    vectors = result.embeddings or []
    skipped = 0
    documents: list[VectorStoreDocument] = []
    for doc_id, doc_vector in zip(ids, vectors, strict=True):
        if doc_vector is None:
            skipped += 1
            continue
        if type(doc_vector) is np.ndarray:
            doc_vector = doc_vector.tolist()
        documents.append(
            VectorStoreDocument(
                id=doc_id,
                vector=doc_vector,
            )
        )

    vector_store.load_documents(documents)

    if skipped > 0:
        logger.warning(
            "Skipped %d rows with None embeddings out of %d",
            skipped,
            len(buffer),
        )

    if output_table is not None:
        for doc_id, doc_vector in zip(ids, vectors, strict=True):
            if doc_vector is None:
                continue
            if type(doc_vector) is np.ndarray:
                doc_vector = doc_vector.tolist()
            await output_table.write({"id": doc_id, "embedding": doc_vector})

    return len(buffer)
