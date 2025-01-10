# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Input loading module."""

import numpy as np
import pandas as pd
from fnllm import ChatLLM

import graphrag.config.defaults as defs
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import create_input
from graphrag.index.llm.load_llm import load_llm_embeddings
from graphrag.index.operations.chunk_text.chunk_text import chunk_text
from graphrag.logger.base import ProgressLogger
from graphrag.prompt_tune.defaults import (
    MIN_CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
    N_SUBSET_MAX,
    K,
)
from graphrag.prompt_tune.types import DocSelectionType


async def _embed_chunks(
    text_chunks: pd.DataFrame,
    embedding_llm: ChatLLM,
    n_subset_max: int = N_SUBSET_MAX,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Convert text chunks into dense text embeddings."""
    sampled_text_chunks = text_chunks.sample(n=min(n_subset_max, len(text_chunks)))
    embeddings = await embedding_llm(sampled_text_chunks["chunks"].tolist())
    return text_chunks, np.array(embeddings.output.embeddings)


def _sample_chunks_from_embeddings(
    text_chunks: pd.DataFrame,
    embeddings,
    k: int = K,
) -> pd.DataFrame:
    """Sample text chunks from embeddings."""
    center = np.mean(embeddings, axis=0)
    distances = np.linalg.norm(embeddings - center, axis=1)
    nearest_indices = np.argsort(distances)[:k]

    return text_chunks.iloc[nearest_indices]


async def load_docs_in_chunks(
    root: str,
    config: GraphRagConfig,
    select_method: DocSelectionType,
    limit: int,
    logger: ProgressLogger,
    chunk_size: int = MIN_CHUNK_SIZE,
    n_subset_max: int = N_SUBSET_MAX,
    k: int = K,
) -> list[str]:
    """Load docs into chunks for generating prompts."""
    embeddings_llm_settings = config.get_language_model_config(
        config.embeddings.model_id
    )

    dataset = await create_input(config.input, logger, root)

    # covert to text units
    chunk_config = config.chunks

    # Use smaller chunks, to avoid huge prompts
    dataset["chunks"] = chunk_text(
        dataset,
        column="text",
        size=chunk_size,
        overlap=MIN_CHUNK_OVERLAP,
        encoding_model=defs.ENCODING_MODEL,
        strategy=chunk_config.strategy,
        callbacks=NoopWorkflowCallbacks(),
    )

    # Select chunks into a new df and explode it
    chunks_df = pd.DataFrame(dataset["chunks"].explode())  # type: ignore

    # Depending on the select method, build the dataset
    if limit <= 0 or limit > len(chunks_df):
        limit = len(chunks_df)

    if select_method == DocSelectionType.TOP:
        chunks_df = chunks_df[:limit]
    elif select_method == DocSelectionType.RANDOM:
        chunks_df = chunks_df.sample(n=limit)
    elif select_method == DocSelectionType.AUTO:
        if k is None or k <= 0:
            msg = "k must be an integer > 0"
            raise ValueError(msg)
        embedding_llm = load_llm_embeddings(
            name="prompt_tuning_embeddings",
            llm_config=embeddings_llm_settings,
            callbacks=NoopWorkflowCallbacks(),
            cache=None,
        )

        chunks_df, embeddings = await _embed_chunks(
            chunks_df, embedding_llm, n_subset_max=n_subset_max
        )
        chunks_df = _sample_chunks_from_embeddings(chunks_df, embeddings, k=k)

    # Convert the dataset to list form, so we have a list of documents
    return chunks_df["chunks"].tolist()
