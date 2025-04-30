# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.communities import _update_and_merge_communities
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the communities from a incremental index run."""
    logger.info("Updating Communities")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )

    community_id_mapping = await _update_communities(
        previous_storage, delta_storage, output_storage
    )

    context.state["incremental_update_community_id_mapping"] = community_id_mapping

    return WorkflowFunctionOutput(result=None)


async def _update_communities(
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
) -> dict:
    """Update the communities output."""
    old_communities = await load_table_from_storage("communities", previous_storage)
    delta_communities = await load_table_from_storage("communities", delta_storage)
    merged_communities, community_id_mapping = _update_and_merge_communities(
        old_communities, delta_communities
    )

    await write_table_to_storage(merged_communities, "communities", output_storage)

    return community_id_mapping
