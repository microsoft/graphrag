# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing text_embed, load_strategy and create_row_from_embedding_data methods definition."""

import logging
from enum import Enum
from typing import Any, cast

import numpy as np
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, verb

from graphrag.index.cache import PipelineCache
from graphrag.vector_stores import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreFactory,
)

from .strategies.typing import TextEmbeddingStrategy

log = logging.getLogger(__name__)

# Per Azure OpenAI Limits
# https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
DEFAULT_EMBEDDING_BATCH_SIZE = 500


class TextEmbedStrategyType(str, Enum):
    """TextEmbedStrategyType class definition."""

    openai = "openai"
    mock = "mock"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


@verb(name="text_embed")
async def text_embed(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    column: str,
    strategy: dict,
    **kwargs,
) -> TableContainer:
    """
    Embed a piece of text into a vector space. The verb outputs a new column containing a mapping between doc_id and vector.

    ## Usage
    ```yaml
    verb: text_embed
    args:
        column: text # The name of the column containing the text to embed, this can either be a column with text, or a column with a list[tuple[doc_id, str]]
        to: embedding # The name of the column to output the embedding to
        strategy: <strategy config> # See strategies section below
    ```

    ## Strategies
    The text embed verb uses a strategy to embed the text. The strategy is an object which defines the strategy to use. The following strategies are available:

    ### openai
    This strategy uses openai to embed a piece of text. In particular it uses a LLM to embed a piece of text. The strategy config is as follows:

    ```yaml
    strategy:
        type: openai
        llm: # The configuration for the LLM
            type: openai_embedding # the type of llm to use, available options are: openai_embedding, azure_openai_embedding
            api_key: !ENV ${GRAPHRAG_OPENAI_API_KEY} # The api key to use for openai
            model: !ENV ${GRAPHRAG_OPENAI_MODEL:gpt-4-turbo-preview} # The model to use for openai
            max_tokens: !ENV ${GRAPHRAG_MAX_TOKENS:6000} # The max tokens to use for openai
            organization: !ENV ${GRAPHRAG_OPENAI_ORGANIZATION} # The organization to use for openai
        vector_store: # The optional configuration for the vector store
            type: lancedb # The type of vector store to use, available options are: azure_ai_search, lancedb
            <...>
    ```
    """
    vector_store_config = strategy.get("vector_store")

    if vector_store_config:
        embedding_name = kwargs.get("embedding_name", "default")
        collection_name = _get_collection_name(vector_store_config, embedding_name)
        vector_store: BaseVectorStore = _create_vector_store(
            vector_store_config, collection_name
        )
        vector_store_workflow_config = vector_store_config.get(
            embedding_name, vector_store_config
        )
        return await _text_embed_with_vector_store(
            input,
            callbacks,
            cache,
            column,
            strategy,
            vector_store,
            vector_store_workflow_config,
            vector_store_config.get("store_in_table", False),
            kwargs.get("to", f"{column}_embedding"),
        )

    return await _text_embed_in_memory(
        input,
        callbacks,
        cache,
        column,
        strategy,
        kwargs.get("to", f"{column}_embedding"),
    )


async def _text_embed_in_memory(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    column: str,
    strategy: dict,
    to: str,
):
    output_df = cast(pd.DataFrame, input.get_input())
    strategy_type = strategy["type"]
    strategy_exec = load_strategy(strategy_type)
    strategy_args = {**strategy}
    input_table = input.get_input()

    texts: list[str] = input_table[column].to_numpy().tolist()
    result = await strategy_exec(texts, callbacks, cache, strategy_args)

    output_df[to] = result.embeddings
    return TableContainer(table=output_df)


async def _text_embed_with_vector_store(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    column: str,
    strategy: dict[str, Any],
    vector_store: BaseVectorStore,
    vector_store_config: dict,
    store_in_table: bool = False,
    to: str = "",
):
    output_df = cast(pd.DataFrame, input.get_input())
    strategy_type = strategy["type"]
    strategy_exec = load_strategy(strategy_type)
    strategy_args = {**strategy}

    # Get vector-storage configuration
    insert_batch_size: int = (
        vector_store_config.get("batch_size") or DEFAULT_EMBEDDING_BATCH_SIZE
    )
    title_column: str = vector_store_config.get("title_column", "title")
    id_column: str = vector_store_config.get("id_column", "id")
    overwrite: bool = vector_store_config.get("overwrite", True)

    if column not in output_df.columns:
        msg = f"Column {column} not found in input dataframe with columns {output_df.columns}"
        raise ValueError(msg)
    if title_column not in output_df.columns:
        msg = f"Column {title_column} not found in input dataframe with columns {output_df.columns}"
        raise ValueError(msg)
    if id_column not in output_df.columns:
        msg = f"Column {id_column} not found in input dataframe with columns {output_df.columns}"
        raise ValueError(msg)

    total_rows = 0
    for row in output_df[column]:
        if isinstance(row, list):
            total_rows += len(row)
        else:
            total_rows += 1

    i = 0
    starting_index = 0

    all_results = []

    while insert_batch_size * i < input.get_input().shape[0]:
        batch = input.get_input().iloc[
            insert_batch_size * i : insert_batch_size * (i + 1)
        ]
        texts: list[str] = batch[column].to_numpy().tolist()
        titles: list[str] = batch[title_column].to_numpy().tolist()
        ids: list[str] = batch[id_column].to_numpy().tolist()
        result = await strategy_exec(
            texts,
            callbacks,
            cache,
            strategy_args,
        )
        if store_in_table and result.embeddings:
            embeddings = [
                embedding for embedding in result.embeddings if embedding is not None
            ]
            all_results.extend(embeddings)

        vectors = result.embeddings or []
        documents: list[VectorStoreDocument] = []
        for id, text, title, vector in zip(ids, texts, titles, vectors, strict=True):
            if type(vector) is np.ndarray:
                vector = vector.tolist()
            document = VectorStoreDocument(
                id=id,
                text=text,
                vector=vector,
                attributes={"title": title},
            )
            documents.append(document)

        vector_store.load_documents(documents, overwrite and i == 0)
        starting_index += len(documents)
        i += 1

    if store_in_table:
        output_df[to] = all_results

    return TableContainer(table=output_df)


def _create_vector_store(
    vector_store_config: dict, collection_name: str
) -> BaseVectorStore:
    vector_store_type: str = str(vector_store_config.get("type"))
    if collection_name:
        vector_store_config.update({"collection_name": collection_name})

    vector_store = VectorStoreFactory.get_vector_store(
        vector_store_type, kwargs=vector_store_config
    )

    vector_store.connect(**vector_store_config)
    return vector_store


def _get_collection_name(vector_store_config: dict, embedding_name: str) -> str:
    collection_name = vector_store_config.get("collection_name")
    if not collection_name:
        collection_names = vector_store_config.get("collection_names", {})
        collection_name = collection_names.get(embedding_name, embedding_name)

    msg = f"using {vector_store_config.get('type')} collection_name {collection_name} for embedding {embedding_name}"
    log.info(msg)
    return collection_name


def load_strategy(strategy: TextEmbedStrategyType) -> TextEmbeddingStrategy:
    """Load strategy method definition."""
    match strategy:
        case TextEmbedStrategyType.openai:
            from .strategies.openai import run as run_openai

            return run_openai
        case TextEmbedStrategyType.mock:
            from .strategies.mock import run as run_mock

            return run_mock
        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
