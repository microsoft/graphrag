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
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Update the text units from a incremental index run."""
    logger.info("Updating Text Units")
    output_storage, previous_storage, delta_storage = get_update_storages(
        config, context.state["update_timestamp"]
    )
    entity_id_mapping = context.state["incremental_update_entity_id_mapping"]

    merged_text_units = await _update_text_units(
        previous_storage, delta_storage, output_storage, entity_id_mapping
    )

    context.state["incremental_update_merged_text_units"] = merged_text_units

    return WorkflowFunctionOutput(result=None)


async def _update_text_units(
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
    entity_id_mapping: dict,
) -> pd.DataFrame:
    """Update the text units output."""
    old_text_units = await load_table_from_storage("text_units", previous_storage)
    delta_text_units = await load_table_from_storage("text_units", delta_storage)
    merged_text_units = _update_and_merge_text_units(
        old_text_units, delta_text_units, entity_id_mapping
    )

    await write_table_to_storage(merged_text_units, "text_units", output_storage)

    return merged_text_units


def _update_and_merge_text_units(
    old_text_units: pd.DataFrame,
    delta_text_units: pd.DataFrame,
    entity_id_mapping: dict,
) -> pd.DataFrame:
    """Update and merge text units.

    Parameters
    ----------
    old_text_units : pd.DataFrame
        The old text units.
    delta_text_units : pd.DataFrame
        The delta text units.
    entity_id_mapping : dict
        The entity id mapping.

    Returns
    -------
    pd.DataFrame
        The updated text units.
    """
    # Look for entity ids in entity_ids and replace them with the corresponding id in the mapping
    if entity_id_mapping:
        delta_text_units["entity_ids"] = delta_text_units["entity_ids"].apply(
            lambda x: [entity_id_mapping.get(i, i) for i in x] if x is not None else x
        )

    initial_id = old_text_units["human_readable_id"].max() + 1
    delta_text_units["human_readable_id"] = np.arange(
        initial_id, initial_id + len(delta_text_units)
    )
    # Merge the final text units
    return pd.concat([old_text_units, delta_text_units], ignore_index=True, copy=False)
