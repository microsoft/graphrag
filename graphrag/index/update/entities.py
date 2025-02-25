# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity related operations and utils for Incremental Indexing."""

import asyncio
import itertools

import numpy as np
import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import ENTITIES_FINAL_COLUMNS
from graphrag.index.operations.summarize_descriptions.graph_intelligence_strategy import (
    run_graph_intelligence as run_entity_summarization,
)


def _group_and_resolve_entities(
    old_entities_df: pd.DataFrame, delta_entities_df: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Group and resolve entities.

    Parameters
    ----------
    old_entities_df : pd.DataFrame
        The first dataframe.
    delta_entities_df : pd.DataFrame
        The delta dataframe.

    Returns
    -------
    pd.DataFrame
        The resolved dataframe.
    dict
        The id mapping for existing entities. In the form of {df_b.id: df_a.id}.
    """
    # If a title exists in A and B, make a dictionary for {B.id : A.id}
    merged = delta_entities_df[["id", "title"]].merge(
        old_entities_df[["id", "title"]],
        on="title",
        suffixes=("_B", "_A"),
        copy=False,
    )
    id_mapping = dict(zip(merged["id_B"], merged["id_A"], strict=True))

    # Increment human readable id in b by the max of a
    initial_id = old_entities_df["human_readable_id"].max() + 1
    delta_entities_df["human_readable_id"] = np.arange(
        initial_id, initial_id + len(delta_entities_df)
    )
    # Concat A and B
    combined = pd.concat(
        [old_entities_df, delta_entities_df], ignore_index=True, copy=False
    )

    # Group by title and resolve conflicts
    aggregated = (
        combined.groupby("title")
        .agg({
            "id": "first",
            "type": "first",
            "human_readable_id": "first",
            "description": lambda x: list(x.astype(str)),  # Ensure str
            # Concatenate nd.array into a single list
            "text_unit_ids": lambda x: list(itertools.chain(*x.tolist())),
            "degree": "first",  # todo: we could probably re-compute this with the entire new graph
            "x": "first",
            "y": "first",
        })
        .reset_index()
    )

    # recompute frequency to include new text units
    aggregated["frequency"] = aggregated["text_unit_ids"].apply(len)

    # Force the result into a DataFrame
    resolved: pd.DataFrame = pd.DataFrame(aggregated)

    # Modify column order to keep consistency
    resolved = resolved.loc[:, ENTITIES_FINAL_COLUMNS]

    return resolved, id_mapping
