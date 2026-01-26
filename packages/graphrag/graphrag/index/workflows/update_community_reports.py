# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.communities import _update_and_merge_community_reports

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the community reports from a incremental index run."""
    logger.info("Workflow started: update_community_reports")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )
    
    previous_table_provider = ParquetTableProvider(previous_storage)
    delta_table_provider = ParquetTableProvider(delta_storage)
    output_table_provider = ParquetTableProvider(output_storage)

    community_id_mapping = context.state["incremental_update_community_id_mapping"]

    merged_community_reports = await _update_community_reports(
        previous_table_provider, delta_table_provider, output_table_provider, community_id_mapping
    )

    context.state["incremental_update_merged_community_reports"] = (
        merged_community_reports
    )

    logger.info("Workflow completed: update_community_reports")
    return WorkflowFunctionOutput(result=None)


async def _update_community_reports(
    previous_table_provider: ParquetTableProvider,
    delta_table_provider: ParquetTableProvider,
    output_table_provider: ParquetTableProvider,
    community_id_mapping: dict,
) -> pd.DataFrame:
    """Update the community reports output."""
    old_community_reports = await previous_table_provider.read_dataframe(
        "community_reports"
    )
    delta_community_reports = await delta_table_provider.read_dataframe(
        "community_reports"
    )
    merged_community_reports = _update_and_merge_community_reports(
        old_community_reports, delta_community_reports, community_id_mapping
    )

    await output_table_provider.write_dataframe(
        "community_reports", merged_community_reports
    )

    return merged_community_reports
