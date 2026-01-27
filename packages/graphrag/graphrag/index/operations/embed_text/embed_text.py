# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embed_text method definition."""

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from graphrag_llm.tokenizer import Tokenizer
from graphrag_vectors import VectorStore, VectorStoreDocument

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.embed_text.run_embed_text import run_embed_text

if TYPE_CHECKING:
    from graphrag_llm.embedding import LLMEmbedding

logger = logging.getLogger(__name__)


async def embed_text(
    input: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: "LLMEmbedding",
    tokenizer: Tokenizer,
    embed_column: str,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store: VectorStore,
    id_column: str = "id",
):
    """Embed a piece of text into a vector space. The operation outputs a new column containing a mapping between doc_id and vector."""
    if embed_column not in input.columns:
        msg = f"Column {embed_column} not found in input dataframe with columns {input.columns}"
        raise ValueError(msg)
    if id_column not in input.columns:
        msg = f"Column {id_column} not found in input dataframe with columns {input.columns}"
        raise ValueError(msg)

    vector_store.create_index()

    index = 0

    all_results = []

    num_total_batches = (input.shape[0] + batch_size - 1) // batch_size
    while batch_size * index < input.shape[0]:
        logger.info(
            "uploading text embeddings batch %d/%d of size %d to vector store",
            index + 1,
            num_total_batches,
            batch_size,
        )
        batch = input.iloc[batch_size * index : batch_size * (index + 1)]
        texts: list[str] = batch[embed_column].tolist()
        ids: list[str] = batch[id_column].tolist()
        result = await run_embed_text(
            texts,
            callbacks,
            model,
            tokenizer,
            batch_size,
            batch_max_tokens,
            num_threads,
        )
        if result.embeddings:
            embeddings = [
                embedding for embedding in result.embeddings if embedding is not None
            ]
            all_results.extend(embeddings)

        vectors = result.embeddings or []
        documents: list[VectorStoreDocument] = []
        for doc_id, doc_vector in zip(ids, vectors, strict=True):
            if type(doc_vector) is np.ndarray:
                doc_vector = doc_vector.tolist()
            document = VectorStoreDocument(
                id=doc_id,
                vector=doc_vector,
            )
            documents.append(document)

        vector_store.load_documents(documents)
        index += 1

    return all_results
