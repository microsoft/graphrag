# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Input loading module."""

import asyncio

import numpy as np
import pandas as pd

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.input.factory import create_input
from graphrag.index.operations.embed_text.strategies.openai import (
    _create_text_batches,
    _prepare_embed_texts,
)
from graphrag.index.text_splitting.text_splitting import TokenTextSplitter
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


async def _embed(
    model: EmbeddingModel, chunk: list[str], semaphore: asyncio.Semaphore
) -> np.ndarray[float, np.dtype[np.float_]]:
    async with semaphore:
        chunk_embeddings = await model.aembed_batch(chunk)
        return np.array(chunk_embeddings)


async def _embed_chunks(
    batch_size: int,
    batch_max_tokens: int,
    text_chunks: pd.DataFrame,
    embedding_llm: EmbeddingModel,
    config: LanguageModelConfig,
    splitter: TokenTextSplitter,
    logger: ProgressLogger,
    n_subset_max: int = N_SUBSET_MAX,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Convert text chunks into dense text embeddings."""
    sampled_text_chunks = text_chunks.sample(n=min(n_subset_max, len(text_chunks)))[
        "text"
    ].tolist()
    preped_text_chunks, _ = _prepare_embed_texts(sampled_text_chunks, splitter)
    semaphore: asyncio.Semaphore = asyncio.Semaphore(config.concurrent_requests)

    # Break up the input texts. The sizes here indicate how many snippets are in each input text
    sampled_batches = _create_text_batches(
        preped_text_chunks,
        batch_size,
        batch_max_tokens,
        splitter,
    )
    logger.info(
        (  # noqa: UP034
            f"embedding {len(sampled_text_chunks)} inputs "  # noqa: G004
            f"via {len(preped_text_chunks)} snippets "
            f"using {len(sampled_batches)} batches. "
            f"max_batch_size={batch_size}, max_tokens={batch_max_tokens}"
        )
    )

    # Embed each chunk of snippets
    futures = [_embed(embedding_llm, batch, semaphore) for batch in sampled_batches]
    embeddings = await asyncio.gather(*futures)
    # merge results in a single list of lists (reduce the collect dimension)
    return text_chunks, np.array([item for sublist in embeddings for item in sublist])


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
    batch_size = config.embed_text.batch_size
    batch_max_tokens = config.embed_text.batch_max_tokens
    splitter = TokenTextSplitter(
        encoding_name=embeddings_llm_settings.encoding_model,
        chunk_size=batch_max_tokens,
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
            batch_size,
            batch_max_tokens,
            splitter=splitter,
            text_chunks=chunks_df,
            embedding_llm=embedding_llm,
            config=embeddings_llm_settings,
            logger=logger,
            n_subset_max=n_subset_max,
        )
        chunks_df = _sample_chunks_from_embeddings(chunks_df, embeddings, k=k)

    # Convert the dataset to list form, so we have a list of documents
    return chunks_df["text"].tolist()
