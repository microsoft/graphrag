# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.communities import _update_and_merge_communities

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the communities from a incremental index run."""
    logger.info("Workflow started: update_communities")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )
    
    previous_table_provider = ParquetTableProvider(previous_storage)
    delta_table_provider = ParquetTableProvider(delta_storage)
    output_table_provider = ParquetTableProvider(output_storage)

    community_id_mapping = await _update_communities(
        previous_table_provider, delta_table_provider, output_table_provider
    )

    context.state["incremental_update_community_id_mapping"] = community_id_mapping

    logger.info("Workflow completed: update_communities")
    return WorkflowFunctionOutput(result=None)


async def _update_communities(
    previous_table_provider: ParquetTableProvider,
    delta_table_provider: ParquetTableProvider,
    output_table_provider: ParquetTableProvider,
) -> dict:
    """Update the communities output."""
    old_communities = await previous_table_provider.read_dataframe("communities")
    delta_communities = await delta_table_provider.read_dataframe("communities")
    merged_communities, community_id_mapping = _update_and_merge_communities(
        old_communities, delta_communities
    )

    await output_table_provider.write_dataframe("communities", merged_communities)

    return community_id_mapping
