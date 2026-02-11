# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import numpy as np
import pandas as pd
from graphrag_storage.tables.table_provider import TableProvider

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.index.run.utils import get_update_table_providers
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the covariates from a incremental index run."""
    logger.info("Workflow started: update_covariates")
    output_table_provider, previous_table_provider, delta_table_provider = (
        get_update_table_providers(config, context.state["update_timestamp"])
    )

    if await previous_table_provider.has(
        "covariates"
    ) and await delta_table_provider.has("covariates"):
        logger.info("Updating Covariates")
        await _update_covariates(
            previous_table_provider, delta_table_provider, output_table_provider
        )

    logger.info("Workflow completed: update_covariates")
    return WorkflowFunctionOutput(result=None)


async def _update_covariates(
    previous_table_provider: TableProvider,
    delta_table_provider: TableProvider,
    output_table_provider: TableProvider,
) -> None:
    """Update the covariates output."""
    old_covariates = await DataReader(previous_table_provider).covariates()
    delta_covariates = await DataReader(delta_table_provider).covariates()
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
