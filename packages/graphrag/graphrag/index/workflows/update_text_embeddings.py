# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

from graphrag_llm.embedding import create_embedding

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_table_providers
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.workflows.generate_text_embeddings import generate_text_embeddings

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the text embeddings from a incremental index run."""
    logger.info("Workflow started: update_text_embeddings")
    output_table_provider, _, _ = get_update_table_providers(
        config, context.state["update_timestamp"]
    )

    merged_text_units = context.state["incremental_update_merged_text_units"]
    merged_entities_df = context.state["incremental_update_merged_entities"]
    merged_community_reports = context.state[
        "incremental_update_merged_community_reports"
    ]

    embedded_fields = config.embed_text.names

    model_config = config.get_embedding_model_config(
        config.embed_text.embedding_model_id
    )

    model = create_embedding(
        model_config,
        cache=context.cache.child("text_embedding"),
        cache_key_creator=cache_key_creator,
    )

    tokenizer = model.tokenizer

    result = await generate_text_embeddings(
        text_units=merged_text_units,
        entities=merged_entities_df,
        community_reports=merged_community_reports,
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
        for name, table in result.items():
            await output_table_provider.write_dataframe(f"embeddings.{name}", table)

    logger.info("Workflow completed: update_text_embeddings")
    return WorkflowFunctionOutput(result=None)
