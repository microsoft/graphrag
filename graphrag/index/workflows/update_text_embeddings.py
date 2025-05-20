# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

from graphrag.config.get_embedding_settings import get_embedding_settings
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.workflows.generate_text_embeddings import generate_text_embeddings
from graphrag.utils.storage import write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the text embeddings from a incremental index run."""
    logger.info("Updating Text Embeddings")
    output_storage, _, _ = get_update_storages(
        config, context.state["update_timestamp"]
    )

    final_documents_df = context.state["incremental_update_final_documents"]
    merged_relationships_df = context.state["incremental_update_merged_relationships"]
    merged_text_units = context.state["incremental_update_merged_text_units"]
    merged_entities_df = context.state["incremental_update_merged_entities"]
    merged_community_reports = context.state[
        "incremental_update_merged_community_reports"
    ]

    embedded_fields = config.embed_text.names
    text_embed = get_embedding_settings(config)
    result = await generate_text_embeddings(
        documents=final_documents_df,
        relationships=merged_relationships_df,
        text_units=merged_text_units,
        entities=merged_entities_df,
        community_reports=merged_community_reports,
        callbacks=context.callbacks,
        cache=context.cache,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
    )
    if config.snapshots.embeddings:
        for name, table in result.items():
            await write_table_to_storage(
                table,
                f"embeddings.{name}",
                output_storage,
            )

    return WorkflowFunctionOutput(result=None)
