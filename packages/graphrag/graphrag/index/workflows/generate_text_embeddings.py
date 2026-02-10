# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from typing import TYPE_CHECKING

import pandas as pd
from graphrag_llm.embedding import create_embedding
from graphrag_llm.tokenizer import Tokenizer
from graphrag_vectors import (
    VectorStoreConfig,
    create_vector_store,
)

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.embeddings import (
    community_full_content_embedding,
    entity_description_embedding,
    text_unit_text_embedding,
)
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

if TYPE_CHECKING:
    from graphrag_llm.embedding import LLMEmbedding

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    logger.info("Workflow started: generate_text_embeddings")
    embedded_fields = config.embed_text.names
    logger.info("Embedding the following fields: %s", embedded_fields)
    reader = DataReader(context.output_table_provider)
    text_units = None
    entities = None
    community_reports = None
    if text_unit_text_embedding in embedded_fields:
        text_units = await reader.text_units()
    if entity_description_embedding in embedded_fields:
        entities = await reader.entities()
    if community_full_content_embedding in embedded_fields:
        community_reports = await reader.community_reports()

    model_config = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )

    model = create_embedding(
        model_config,
        cache=context.cache.child(config.embed_text.model_instance_name),
        cache_key_creator=cache_key_creator,
    )

    tokenizer = model.tokenizer

    output = await generate_text_embeddings(
        text_units=text_units,
        entities=entities,
        community_reports=community_reports,
        callbacks=context.callbacks,
        model=model,
        tokenizer=tokenizer,
        batch_size=config.embed_text.batch_size,
        batch_max_tokens=config.embed_text.batch_max_tokens,
        num_threads=config.concurrent_requests,
        vector_store_config=config.vector_store,
        embedded_fields=embedded_fields,
    )

    if config.snapshots.embeddings:
        for name, table in output.items():
            await context.output_table_provider.write_dataframe(
                f"embeddings.{name}",
                table,
            )

    logger.info("Workflow completed: generate_text_embeddings")
    return WorkflowFunctionOutput(result=output)


async def generate_text_embeddings(
    text_units: pd.DataFrame | None,
    entities: pd.DataFrame | None,
    community_reports: pd.DataFrame | None,
    callbacks: WorkflowCallbacks,
    model: "LLMEmbedding",
    tokenizer: Tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store_config: VectorStoreConfig,
    embedded_fields: list[str],
) -> dict[str, pd.DataFrame]:
    """All the steps to generate all embeddings."""
    embedding_param_map = {
        text_unit_text_embedding: {
            "data": text_units.loc[:, ["id", "text"]]
            if text_units is not None
            else None,
            "embed_column": "text",
        },
        entity_description_embedding: {
            "data": entities.loc[:, ["id", "title", "description"]].assign(
                title_description=lambda df: df["title"] + ":" + df["description"]
            )
            if entities is not None
            else None,
            "embed_column": "title_description",
        },
        community_full_content_embedding: {
            "data": community_reports.loc[:, ["id", "full_content"]]
            if community_reports is not None
            else None,
            "embed_column": "full_content",
        },
    }

    logger.info("Creating embeddings")
    outputs = {}
    for field in embedded_fields:
        if embedding_param_map[field]["data"] is None:
            msg = f"Embedding {field} is specified but data table is not in storage. This may or may not be intentional - if you expect it to me here, please check for errors earlier in the logs."
            logger.warning(msg)
        else:
            outputs[field] = await _run_embeddings(
                name=field,
                callbacks=callbacks,
                model=model,
                tokenizer=tokenizer,
                vector_store_config=vector_store_config,
                batch_size=batch_size,
                batch_max_tokens=batch_max_tokens,
                num_threads=num_threads,
                **embedding_param_map[field],
            )
    return outputs


async def _run_embeddings(
    name: str,
    data: pd.DataFrame,
    embed_column: str,
    callbacks: WorkflowCallbacks,
    model: "LLMEmbedding",
    tokenizer: Tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store_config: VectorStoreConfig,
) -> pd.DataFrame:
    """All the steps to generate single embedding."""
    vector_store = create_vector_store(
        vector_store_config, vector_store_config.index_schema[name]
    )
    vector_store.connect()

    data["embedding"] = await embed_text(
        input=data,
        callbacks=callbacks,
        model=model,
        tokenizer=tokenizer,
        embed_column=embed_column,
        batch_size=batch_size,
        batch_max_tokens=batch_max_tokens,
        num_threads=num_threads,
        vector_store=vector_store,
    )

    return data.loc[:, ["id", "embedding"]]
