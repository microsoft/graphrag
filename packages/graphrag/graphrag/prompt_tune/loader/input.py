# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Input loading module."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from graphrag_chunking.chunker_factory import create_chunker
from graphrag_input import create_input_reader
from graphrag_llm.embedding import create_embedding
from graphrag_storage import create_storage

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.embed_text.run_embed_text import (
    run_embed_text,
)
from graphrag.index.workflows.create_base_text_units import create_base_text_units
from graphrag.prompt_tune.defaults import (
    LIMIT,
    N_SUBSET_MAX,
    K,
)
from graphrag.prompt_tune.types import DocSelectionType


def _sample_chunks_from_embeddings(
    text_chunks: pd.DataFrame,
    embeddings: np.ndarray[Any, np.dtype[np.float64]],
    k: int = K,
) -> pd.DataFrame:
    """Sample text chunks from embeddings."""
    center = np.mean(embeddings, axis=0)
    distances = np.linalg.norm(embeddings - center, axis=1)
    nearest_indices = np.argsort(distances)[:k]

    return text_chunks.iloc[nearest_indices]


async def load_docs_in_chunks(
    config: GraphRagConfig,
    select_method: DocSelectionType,
    limit: int,
    logger: logging.Logger,
    n_subset_max: int = N_SUBSET_MAX,
    k: int = K,
) -> list[str]:
    """Load docs into chunks for generating prompts."""
    embeddings_llm_settings = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )
    model = create_embedding(embeddings_llm_settings)
    tokenizer = model.tokenizer
    chunker = create_chunker(config.chunking, tokenizer.encode, tokenizer.decode)
    input_storage = create_storage(config.input_storage)
    input_reader = create_input_reader(config.input, input_storage)
    dataset = await input_reader.read_files()
    chunks_df = create_base_text_units(
        documents=pd.DataFrame(dataset),
        callbacks=NoopWorkflowCallbacks(),
        tokenizer=tokenizer,
        chunker=chunker,
    )

    # Depending on the select method, build the dataset
    if limit <= 0 or limit > len(chunks_df):
        logger.warning(f"Limit out of range, using default number of chunks: {LIMIT}")  # noqa: G004
        limit = LIMIT

    if select_method == DocSelectionType.TOP:
        chunks_df = chunks_df[:limit]
    elif select_method == DocSelectionType.RANDOM:
        chunks_df = chunks_df.sample(n=limit)
    elif select_method == DocSelectionType.AUTO:
        if k is None or k <= 0:
            msg = "k must be an integer > 0"
            raise ValueError(msg)

        """Convert text chunks into dense text embeddings."""
        sampled_text_chunks = chunks_df.sample(n=min(n_subset_max, len(chunks_df)))[
            "text"
        ].tolist()

        embedding_results = await run_embed_text(
            sampled_text_chunks,
            callbacks=NoopWorkflowCallbacks(),
            model=model,
            tokenizer=tokenizer,
            batch_size=config.embed_text.batch_size,
            batch_max_tokens=config.embed_text.batch_max_tokens,
            num_threads=config.concurrent_requests,
        )
        embeddings = np.array(embedding_results.embeddings)
        chunks_df = _sample_chunks_from_embeddings(chunks_df, embeddings, k=k)

    # Convert the dataset to list form, so we have a list of documents
    return [
        # need this to prevent the str.format() function from breaking when parsing LaTeX from markdown files
        i.replace("{", "{{").replace("}", "}}")
        for i in chunks_df["text"]
    ]
