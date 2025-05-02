# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.communities import _update_and_merge_community_reports
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the community reports from a incremental index run."""
    logger.info("Updating Community Reports")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )

    community_id_mapping = context.state["incremental_update_community_id_mapping"]

    merged_community_reports = await _update_community_reports(
        previous_storage, delta_storage, output_storage, community_id_mapping
    )

    context.state["incremental_update_merged_community_reports"] = (
        merged_community_reports
    )

    return WorkflowFunctionOutput(result=None)


async def _update_community_reports(
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
    community_id_mapping: dict,
) -> pd.DataFrame:
    """Update the community reports output."""
    old_community_reports = await load_table_from_storage(
        "community_reports", previous_storage
    )
    delta_community_reports = await load_table_from_storage(
        "community_reports", delta_storage
    )
    merged_community_reports = _update_and_merge_community_reports(
        old_community_reports, delta_community_reports, community_id_mapping
    )

    await write_table_to_storage(
        merged_community_reports, "community_reports", output_storage
    )

    return merged_community_reports
