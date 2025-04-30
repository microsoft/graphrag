# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import numpy as np
import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import (
    load_table_from_storage,
    storage_has_table,
    write_table_to_storage,
)

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the covariates from a incremental index run."""
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )

    if await storage_has_table(
        "covariates", previous_storage
    ) and await storage_has_table("covariates", delta_storage):
        logger.info("Updating Covariates")
        await _update_covariates(previous_storage, delta_storage, output_storage)

    return WorkflowFunctionOutput(result=None)


async def _update_covariates(
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
) -> None:
    """Update the covariates output."""
    old_covariates = await load_table_from_storage("covariates", previous_storage)
    delta_covariates = await load_table_from_storage("covariates", delta_storage)
    merged_covariates = _merge_covariates(old_covariates, delta_covariates)

    await write_table_to_storage(merged_covariates, "covariates", output_storage)


def _merge_covariates(
    old_covariates: pd.DataFrame, delta_covariates: pd.DataFrame
) -> pd.DataFrame:
    """Merge the covariates.

    Parameters
    ----------
    old_covariates : pd.DataFrame
        The old covariates.
    delta_covariates : pd.DataFrame
        The delta covariates.

    Returns
    -------
    pd.DataFrame
        The merged covariates.
    """
    # Get the max human readable id from the old covariates and update the delta covariates
    initial_id = old_covariates["human_readable_id"].max() + 1
    delta_covariates["human_readable_id"] = np.arange(
        initial_id, initial_id + len(delta_covariates)
    )

    # Concatenate the old and delta covariates
    return pd.concat([old_covariates, delta_covariates], ignore_index=True, copy=False)
