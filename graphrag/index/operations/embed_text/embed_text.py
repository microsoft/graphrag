# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing embed_text, load_strategy and create_row_from_embedding_data methods definition."""

import logging

import numpy as np
import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.embeddings import create_index_name
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.index.operations.embed_text.run_embed_text import run_embed_text
from graphrag.vector_stores.base import BaseVectorStore, VectorStoreDocument
from graphrag.vector_stores.factory import VectorStoreFactory

logger = logging.getLogger(__name__)


async def embed_text(
    input: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    embed_column: str,
    embedding_name: str,
    batch_size: int,
    batch_max_tokens: int,
    vector_store_config: dict,
    id_column: str = "id",
    title_column: str | None = None,
):
    """Embed a piece of text into a vector space. The operation outputs a new column containing a mapping between doc_id and vector."""
    if vector_store_config:
        index_name = _get_index_name(vector_store_config, embedding_name)
        vector_store: BaseVectorStore = _create_vector_store(
            vector_store_config, index_name, embedding_name
        )
        vector_store_workflow_config = vector_store_config.get(
            embedding_name, vector_store_config
        )
        return await _text_embed_with_vector_store(
            input=input,
            callbacks=callbacks,
            cache=cache,
            model_config=model_config,
            embed_column=embed_column,
            vector_store=vector_store,
            vector_store_config=vector_store_workflow_config,
            batch_size=batch_size,
            batch_max_tokens=batch_max_tokens,
            id_column=id_column,
            title_column=title_column,
        )

    return await _text_embed_in_memory(
        input=input,
        callbacks=callbacks,
        cache=cache,
        model_config=model_config,
        embed_column=embed_column,
        batch_size=batch_size,
        batch_max_tokens=batch_max_tokens,
    )


async def _text_embed_in_memory(
    input: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    embed_column: str,
    batch_size: int,
    batch_max_tokens: int,
):
    texts: list[str] = input[embed_column].tolist()
    result = await run_embed_text(
        texts, callbacks, cache, model_config, batch_size, batch_max_tokens
    )

    return result.embeddings


async def _text_embed_with_vector_store(
    input: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    embed_column: str,
    vector_store: BaseVectorStore,
    vector_store_config: dict,
    batch_size: int,
    batch_max_tokens: int,
    id_column: str,
    title_column: str | None = None,
):
    # Get vector-storage configuration

    overwrite: bool = vector_store_config.get("overwrite", True)

    if embed_column not in input.columns:
        msg = f"Column {embed_column} not found in input dataframe with columns {input.columns}"
        raise ValueError(msg)
    title = title_column or embed_column
    if title not in input.columns:
        msg = (
            f"Column {title} not found in input dataframe with columns {input.columns}"
        )
        raise ValueError(msg)
    if id_column not in input.columns:
        msg = f"Column {id_column} not found in input dataframe with columns {input.columns}"
        raise ValueError(msg)

    total_rows = 0
    for row in input[embed_column]:
        if isinstance(row, list):
            total_rows += len(row)
        else:
            total_rows += 1

    i = 0
    starting_index = 0

    all_results = []

    num_total_batches = (input.shape[0] + batch_size - 1) // batch_size
    while batch_size * i < input.shape[0]:
        logger.info(
            "uploading text embeddings batch %d/%d of size %d to vector store",
            i + 1,
            num_total_batches,
            batch_size,
        )
        batch = input.iloc[batch_size * i : batch_size * (i + 1)]
        texts: list[str] = batch[embed_column].tolist()
        titles: list[str] = batch[title].tolist()
        ids: list[str] = batch[id_column].tolist()
        result = await run_embed_text(
            texts, callbacks, cache, model_config, batch_size, batch_max_tokens
        )
        if result.embeddings:
            embeddings = [
                embedding for embedding in result.embeddings if embedding is not None
            ]
            all_results.extend(embeddings)

        vectors = result.embeddings or []
        documents: list[VectorStoreDocument] = []
        for doc_id, doc_text, doc_title, doc_vector in zip(
            ids, texts, titles, vectors, strict=True
        ):
            if type(doc_vector) is np.ndarray:
                doc_vector = doc_vector.tolist()
            document = VectorStoreDocument(
                id=doc_id,
                text=doc_text,
                vector=doc_vector,
                attributes={"title": doc_title},
            )
            documents.append(document)

        vector_store.load_documents(documents, overwrite and i == 0)
        starting_index += len(documents)
        i += 1

    return all_results


def _create_vector_store(
    vector_store_config: dict, index_name: str, embedding_name: str | None = None
) -> BaseVectorStore:
    vector_store_type: str = str(vector_store_config.get("type"))

    embeddings_schema: dict[str, VectorStoreSchemaConfig] = vector_store_config.get(
        "embeddings_schema", {}
    )
    single_embedding_config: VectorStoreSchemaConfig = VectorStoreSchemaConfig()

    if (
        embeddings_schema is not None
        and embedding_name is not None
        and embedding_name in embeddings_schema
    ):
        raw_config = embeddings_schema[embedding_name]
        if isinstance(raw_config, dict):
            single_embedding_config = VectorStoreSchemaConfig(**raw_config)
        else:
            single_embedding_config = raw_config

    if single_embedding_config.index_name is None:
        single_embedding_config.index_name = index_name

    vector_store = VectorStoreFactory().create_vector_store(
        vector_store_schema_config=single_embedding_config,
        vector_store_type=vector_store_type,
        **vector_store_config,
    )

    vector_store.connect(**vector_store_config)
    return vector_store


def _get_index_name(vector_store_config: dict, embedding_name: str) -> str:
    container_name = vector_store_config.get("container_name", "default")
    index_name = create_index_name(container_name, embedding_name)

    msg = f"using vector store {vector_store_config.get('type')} with container_name {container_name} for embedding {embedding_name}: {index_name}"
    logger.info(msg)
    return index_name
