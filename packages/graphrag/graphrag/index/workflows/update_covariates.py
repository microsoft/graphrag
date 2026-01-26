# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import numpy as np
import pandas as pd
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.run.utils import get_update_storages
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the covariates from a incremental index run."""
    logger.info("Workflow started: update_covariates")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )
    
    previous_table_provider = ParquetTableProvider(previous_storage)
    delta_table_provider = ParquetTableProvider(delta_storage)
    output_table_provider = ParquetTableProvider(output_storage)

    if await previous_table_provider.has_dataframe(
        "covariates"
    ) and await delta_table_provider.has_dataframe("covariates"):
        logger.info("Updating Covariates")
        await _update_covariates(previous_table_provider, delta_table_provider, output_table_provider)

    logger.info("Workflow completed: update_covariates")
    return WorkflowFunctionOutput(result=None)


async def _update_covariates(
    previous_table_provider: ParquetTableProvider,
    delta_table_provider: ParquetTableProvider,
    output_table_provider: ParquetTableProvider,
) -> None:
    """Update the covariates output."""
    old_covariates = await previous_table_provider.read_dataframe("covariates")
    delta_covariates = await delta_table_provider.read_dataframe("covariates")
    merged_covariates = _merge_covariates(old_covariates, delta_covariates)

    await output_table_provider.write_dataframe("covariates", merged_covariates)


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
