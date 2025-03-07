# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Input loading module."""

import numpy as np
import pandas as pd

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import create_input
from graphrag.index.workflows.create_base_text_units import create_base_text_units
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.protocol.base import EmbeddingModel
from graphrag.logger.base import ProgressLogger
from graphrag.prompt_tune.defaults import (
    LIMIT,
    N_SUBSET_MAX,
    K,
)
from graphrag.prompt_tune.types import DocSelectionType


async def _embed_chunks(
    text_chunks: pd.DataFrame,
    embedding_llm: EmbeddingModel,
    n_subset_max: int = N_SUBSET_MAX,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Convert text chunks into dense text embeddings."""
    sampled_text_chunks = text_chunks.sample(n=min(n_subset_max, len(text_chunks)))
    embeddings = await embedding_llm.aembed_batch(sampled_text_chunks["text"].tolist())
    return text_chunks, np.array(embeddings)


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
    chunk_size: int,
    overlap: int,
    n_subset_max: int = N_SUBSET_MAX,
    k: int = K,
) -> list[str]:
    """Load docs into chunks for generating prompts."""
    embeddings_llm_settings = config.get_language_model_config(
        config.embed_text.model_id
    )

    dataset = await create_input(config.input, logger, root)
    chunk_config = config.chunks
    chunks_df = create_base_text_units(
        documents=dataset,
        callbacks=NoopWorkflowCallbacks(),
        group_by_columns=chunk_config.group_by_columns,
        size=chunk_size,
        overlap=overlap,
        encoding_model=chunk_config.encoding_model,
        strategy=chunk_config.strategy,
        prepend_metadata=chunk_config.prepend_metadata,
        chunk_size_includes_metadata=chunk_config.chunk_size_includes_metadata,
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
        embedding_llm = ModelManager().register_embedding(
            name="prompt_tuning_embeddings",
            model_type=embeddings_llm_settings.type,
            config=embeddings_llm_settings,
            callbacks=NoopWorkflowCallbacks(),
            cache=None,
        )

        chunks_df, embeddings = await _embed_chunks(
            chunks_df, embedding_llm, n_subset_max=n_subset_max
        )
        chunks_df = _sample_chunks_from_embeddings(chunks_df, embeddings, k=k)

    # Convert the dataset to list form, so we have a list of documents
    return chunks_df["text"].tolist()
