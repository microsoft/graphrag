# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.extract_graph_nlp import (
    extract_graph_nlp,
)
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "extract_graph_nlp"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: WorkflowCallbacks,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    text_units = await load_table_from_storage("text_units", context.storage)

    entities, relationships = await extract_graph_nlp(
        text_units,
        context.cache,
        extraction_config=config.extract_graph_nlp,
    )

    await write_table_to_storage(entities, "entities", context.storage)
    await write_table_to_storage(relationships, "relationships", context.storage)

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        },
        config=None,
    )
