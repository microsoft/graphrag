# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import TYPE_CHECKING

from graphrag_llm.embedding import create_embedding
from graphrag_storage.tables.table import RowTransformer
from graphrag_vectors import create_vector_store

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.embeddings import (
    community_full_content_embedding,
    entity_description_embedding,
    text_unit_text_embedding,
)
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.row_transformers import (
    transform_entity_row_for_embedding,
)
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

if TYPE_CHECKING:
    from graphrag_cache import Cache
    from graphrag_storage.tables.table_provider import TableProvider

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingFieldConfig:
    """Configuration for a single embedding field.

    Describes which source table and column to embed, and an
    optional row transform to apply before embedding.
    """

    name: str
    table_name: str
    embed_column: str
    row_transform: RowTransformer | None = None


EMBEDDING_FIELDS: dict[str, EmbeddingFieldConfig] = {
    text_unit_text_embedding: EmbeddingFieldConfig(
        name=text_unit_text_embedding,
        table_name="text_units",
        embed_column="text",
    ),
    entity_description_embedding: EmbeddingFieldConfig(
        name=entity_description_embedding,
        table_name="entities",
        embed_column="title_description",
        row_transform=transform_entity_row_for_embedding,
    ),
    community_full_content_embedding: EmbeddingFieldConfig(
        name=community_full_content_embedding,
        table_name="community_reports",
        embed_column="full_content",
    ),
}


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Generate text embeddings for configured fields via streaming Tables."""
    logger.info("Workflow started: generate_text_embeddings")

    await generate_text_embeddings(
        config=config,
        table_provider=context.output_table_provider,
        cache=context.cache,
        callbacks=context.callbacks,
    )

    logger.info("Workflow completed: generate_text_embeddings")
    return WorkflowFunctionOutput(result=None)


async def generate_text_embeddings(
    config: GraphRagConfig,
    table_provider: TableProvider,
    cache: Cache,
    callbacks: WorkflowCallbacks,
) -> None:
    """Generate text embeddings for all configured fields."""
    embedded_fields = config.embed_text.names
    logger.info("Embedding the following fields: %s", embedded_fields)

    model_config = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )
    model = create_embedding(
        model_config,
        cache=cache.child(config.embed_text.model_instance_name),
        cache_key_creator=cache_key_creator,
    )
    tokenizer = model.tokenizer

    for field_name in embedded_fields:
        field_config = EMBEDDING_FIELDS[field_name]

        if not await table_provider.has(field_config.table_name):
            logger.warning(
                "Embedding %s is specified but source table '%s' "
                "is not in storage. Skipping.",
                field_config.name,
                field_config.table_name,
            )
            continue

        vector_store = create_vector_store(
            config.vector_store,
            config.vector_store.index_schema[field_config.name],
        )
        vector_store.connect()

        async with AsyncExitStack() as stack:
            input_table = await stack.enter_async_context(
                table_provider.open(
                    field_config.table_name,
                    truncate=False,
                    transformer=field_config.row_transform,
                )
            )

            output_table = None
            if config.snapshots.embeddings:
                output_table = await stack.enter_async_context(
                    table_provider.open(f"embeddings.{field_config.name}")
                )

            count = await embed_text(
                input_table=input_table,
                callbacks=callbacks,
                model=model,
                tokenizer=tokenizer,
                embed_column=field_config.embed_column,
                batch_size=config.embed_text.batch_size,
                batch_max_tokens=config.embed_text.batch_max_tokens,
                num_threads=config.concurrent_requests,
                vector_store=vector_store,
                output_table=output_table,
            )

        logger.info(
            "Embedded %d rows for %s",
            count,
            field_config.name,
        )
