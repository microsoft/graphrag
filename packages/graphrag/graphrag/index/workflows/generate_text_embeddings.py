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

    model_config = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )

    model = create_embedding(
        model_config,
        cache=context.cache.child(config.embed_text.model_instance_name),
        cache_key_creator=cache_key_creator,
    )

    tokenizer = model.tokenizer

    # Use streaming approach
    await generate_text_embeddings_streaming(
        table_provider=context.output_table_provider,
        callbacks=context.callbacks,
        model=model,
        tokenizer=tokenizer,
        batch_size=config.embed_text.batch_size,
        batch_max_tokens=config.embed_text.batch_max_tokens,
        num_threads=config.concurrent_requests,
        vector_store_config=config.vector_store,
        embedded_fields=embedded_fields,
        write_snapshots=config.snapshots.embeddings,
    )

    # Read back for return value to maintain workflow compatibility
    output = {}
    for field in embedded_fields:
        snapshot_name = f"embeddings.{field}"
        if await context.output_table_provider.has_dataframe(snapshot_name):
            output[field] = await context.output_table_provider.read_dataframe(
                snapshot_name
            )

    logger.info("Workflow completed: generate_text_embeddings")
    return WorkflowFunctionOutput(result=output)


async def generate_text_embeddings_streaming(
    table_provider,
    callbacks,
    model: "LLMEmbedding",
    tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store_config,
    embedded_fields: list[str],
    write_snapshots: bool = False,
) -> None:
    """Generate embeddings using streaming to reduce memory pressure."""
    # Generate embeddings for each field
    if text_unit_text_embedding in embedded_fields:
        await _run_embeddings_streaming(
            table_provider=table_provider,
            table_name="text_units",
            field_name=text_unit_text_embedding,
            id_column="id",
            text_column="text",
            callbacks=callbacks,
            model=model,
            tokenizer=tokenizer,
            batch_size=batch_size,
            batch_max_tokens=batch_max_tokens,
            num_threads=num_threads,
            vector_store_config=vector_store_config,
            write_snapshots=write_snapshots,
        )
    
    if entity_description_embedding in embedded_fields:
        await _run_embeddings_streaming(
            table_provider=table_provider,
            table_name="entities",
            field_name=entity_description_embedding,
            id_column="id",
            text_column="description",
            callbacks=callbacks,
            model=model,
            tokenizer=tokenizer,
            batch_size=batch_size,
            batch_max_tokens=batch_max_tokens,
            num_threads=num_threads,
            vector_store_config=vector_store_config,
            write_snapshots=write_snapshots,
        )
    
    if community_full_content_embedding in embedded_fields:
        await _run_embeddings_streaming(
            table_provider=table_provider,
            table_name="community_reports",
            field_name=community_full_content_embedding,
            id_column="id",
            text_column="full_content",
            callbacks=callbacks,
            model=model,
            tokenizer=tokenizer,
            batch_size=batch_size,
            batch_max_tokens=batch_max_tokens,
            num_threads=num_threads,
            vector_store_config=vector_store_config,
            write_snapshots=write_snapshots,
        )


async def _run_embeddings_streaming(
    table_provider,
    table_name: str,
    field_name: str,
    id_column: str,
    text_column: str,
    callbacks,
    model,
    tokenizer,
    batch_size: int,
    batch_max_tokens: int,
    num_threads: int,
    vector_store_config,
    write_snapshots: bool,
) -> None:
    """Run embeddings on a table using streaming and batching."""
    logger.info("Generating %s embeddings for %s...", field_name, table_name)
    
    # Read table - for now, use DataFrame approach since embed_text expects DataFrame
    # TODO: Implement true streaming when embed_text supports it
    df = await table_provider.read_dataframe(table_name)
    
    if df.empty:
        logger.warning("Table %s is empty, skipping embeddings", table_name)
        return
    
    # Prepare data for embedding
    embed_data = df[[id_column, text_column]].copy()
    
    # Create vector store if configured
    vector_store = None
    if vector_store_config and field_name in vector_store_config.index_schema:
        vector_store = create_vector_store(
            vector_store_config, vector_store_config.index_schema[field_name]
        )
        vector_store.connect()
    
    # Generate embeddings
    embed_data["embedding"] = await embed_text(
        input=embed_data,
        callbacks=callbacks,
        model=model,
        tokenizer=tokenizer,
        embed_column=text_column,
        batch_size=batch_size,
        batch_max_tokens=batch_max_tokens,
        num_threads=num_threads,
        vector_store=vector_store,
    )
    
    # Write snapshot if requested
    if write_snapshots:
        result = embed_data[[id_column, "embedding"]].rename(columns={id_column: "id"})
        await table_provider.write_dataframe(f"embeddings.{field_name}", result)
    
    logger.info("Completed %s embeddings for %s", field_name, table_name)


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
