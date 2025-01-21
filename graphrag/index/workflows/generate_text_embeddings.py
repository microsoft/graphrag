# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.embeddings import get_embedded_fields, get_embedding_settings
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.generate_text_embeddings import (
    generate_text_embeddings,
)
from graphrag.utils.storage import load_table_from_storage

workflow_name = "generate_text_embeddings"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform community reports."""
    final_documents = await load_table_from_storage(
        "create_final_documents", context.storage
    )
    final_relationships = await load_table_from_storage(
        "create_final_relationships", context.storage
    )
    final_text_units = await load_table_from_storage(
        "create_final_text_units", context.storage
    )
    final_entities = await load_table_from_storage(
        "create_final_entities", context.storage
    )
    final_community_reports = await load_table_from_storage(
        "create_final_community_reports", context.storage
    )

    embedded_fields = get_embedded_fields(config)
    text_embed = get_embedding_settings(config)

    await generate_text_embeddings(
        final_documents=final_documents,
        final_relationships=final_relationships,
        final_text_units=final_text_units,
        final_entities=final_entities,
        final_community_reports=final_community_reports,
        callbacks=callbacks,
        cache=context.cache,
        storage=context.storage,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
        snapshot_embeddings_enabled=config.snapshots.embeddings,
    )
