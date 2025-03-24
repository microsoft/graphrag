# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Input loading module."""

import numpy as np
import pandas as pd

from graphrag.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import create_input
from graphrag.index.operations.embed_text.strategies.openai import (
    run as run_embed_text,
)
from graphrag.index.workflows.create_base_text_units import create_base_text_units
from graphrag.logger.base import ProgressLogger
from graphrag.prompt_tune.defaults import (
    LIMIT,
    N_SUBSET_MAX,
    K,
)
from graphrag.prompt_tune.types import DocSelectionType


def _sample_chunks_from_embeddings(
    text_chunks: pd.DataFrame,
    embeddings: np.ndarray[float, np.dtype[np.float_]],
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

        """Convert text chunks into dense text embeddings."""
        sampled_text_chunks = chunks_df.sample(n=min(n_subset_max, len(chunks_df)))[
            "text"
        ].tolist()

        embedding_results = await run_embed_text(
            sampled_text_chunks,
            callbacks=NoopWorkflowCallbacks(),
            cache=NoopPipelineCache(),
            args={
                "llm": embeddings_llm_settings.model_dump(),
                "num_threads": embeddings_llm_settings.concurrent_requests,
                "batch_size": config.embed_text.batch_size,
                "batch_max_tokens": config.embed_text.batch_max_tokens,
            },
        )
        embeddings = np.array(embedding_results.embeddings)
        chunks_df = _sample_chunks_from_embeddings(chunks_df, embeddings, k=k)

    # Convert the dataset to list form, so we have a list of documents
    return [
        # need this to prevent the str.format() function from breaking when parsing LaTeX from markdown files
        i.replace("{", "{{").replace("}", "}}")
        for i in chunks_df["text"]
    ]
