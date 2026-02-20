# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_table_providers
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.workflows.generate_text_embeddings import (
    generate_text_embeddings,
)

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update text embeddings for an incremental index run."""
    logger.info("Workflow started: update_text_embeddings")

    output_table_provider, _, _ = get_update_table_providers(
        config, context.state["update_timestamp"]
    )

    await generate_text_embeddings(
        config=config,
        table_provider=output_table_provider,
        cache=context.cache,
        callbacks=context.callbacks,
    )

    logger.info("Workflow completed: update_text_embeddings")
    return WorkflowFunctionOutput(result=None)
