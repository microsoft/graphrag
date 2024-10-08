# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable

from graphrag.index.storage.typing import PipelineStorage
from graphrag.utils.storage import _load_table_from_storage

mergeable_outputs = [
    "create_final_documents",
    "create_final_entities",
    "create_final_relationships",
]


@dataclass
class InputDelta:
    """Dataclass to hold the input delta.

    Attributes
    ----------
    new_inputs : pd.DataFrame
        The new inputs.
    deleted_inputs : pd.DataFrame
        The deleted inputs.
    """

    new_inputs: pd.DataFrame
    deleted_inputs: pd.DataFrame


async def get_delta_docs(
    input_dataset: pd.DataFrame, storage: PipelineStorage
) -> InputDelta:
    """Get the delta between the input dataset and the final documents.

    Parameters
    ----------
    input_dataset : pd.DataFrame
        The input dataset.
    storage : PipelineStorage
        The Pipeline storage.

    Returns
    -------
    InputDelta
        The input delta. With new inputs and deleted inputs.
    """
    final_docs = await _load_table_from_storage(
        "create_final_documents.parquet", storage
    )

    # Select distinct title from final docs and from dataset
    previous_docs: list[str] = final_docs["title"].unique().tolist()
    dataset_docs: list[str] = input_dataset["title"].unique().tolist()

    # Get the new documents (using loc to ensure DataFrame)
    new_docs = input_dataset.loc[~input_dataset["title"].isin(previous_docs)]

    # Get the deleted documents (again using loc to ensure DataFrame)
    deleted_docs = final_docs.loc[~final_docs["title"].isin(dataset_docs)]

    return InputDelta(new_docs, deleted_docs)


async def update_dataframe_outputs(
    dataframe_dict: dict[str, pd.DataFrame],
    storage: PipelineStorage,
) -> None:
    """Update the mergeable outputs.

    Parameters
    ----------
    dataframe_dict : dict[str, pd.DataFrame]
        The dictionary of dataframes.
    storage : PipelineStorage
        The storage used to store the dataframes.
    """
    await _concat_dataframes("create_base_text_units", dataframe_dict, storage)
    await _concat_dataframes("create_final_documents", dataframe_dict, storage)

    old_entities = await _load_table_from_storage(
        "create_final_entities.parquet", storage
    )
    delta_entities = dataframe_dict["create_final_entities"]

    merged_entities_df, entity_id_mapping = _group_and_resolve_entities(
        old_entities, delta_entities
    )
    # Save the updated entities back to storage
    # TODO: Using _new in the meantime, to compare outputs without overwriting the original
    await storage.set(
        "create_final_entities_new.parquet", merged_entities_df.to_parquet()
    )

    # Update relationships with the entities id mapping
    old_relationships = await _load_table_from_storage(
        "create_final_relationships.parquet", storage
    )
    delta_relationships = dataframe_dict["create_final_relationships"]
    merged_relationships_df = _update_and_merge_relationships(
        old_relationships,
        delta_relationships,
    )

    # TODO: Using _new in the meantime, to compare outputs without overwriting the original
    await storage.set(
        "create_final_relationships_new.parquet", merged_relationships_df.to_parquet()
    )

    # Update and merge final text units
    old_text_units = await _load_table_from_storage(
        "create_final_text_units.parquet", storage
    )
    delta_text_units = dataframe_dict["create_final_text_units"]

    merged_text_units = _update_and_merge_text_units(
        old_text_units, delta_text_units, entity_id_mapping
    )

    # TODO: Using _new in the meantime, to compare outputs without overwriting the original
    await storage.set(
        "create_final_text_units_new.parquet", merged_text_units.to_parquet()
    )

    # Merge final nodes and update community ids
    old_nodes = await _load_table_from_storage("create_final_nodes.parquet", storage)
    delta_nodes = dataframe_dict["create_final_nodes"]

    merged_nodes, community_id_mapping = _merge_and_resolve_nodes(
        old_nodes, delta_nodes, merged_entities_df
    )

    await storage.set("create_final_nodes_new.parquet", merged_nodes.to_parquet())

    # Merge final communities
    old_communities = await _load_table_from_storage(
        "create_final_communities.parquet", storage
    )
    delta_communities = dataframe_dict["create_final_communities"]
    merged_communities = _update_and_merge_communities(
        old_communities, delta_communities, community_id_mapping
    )

    await storage.set(
        "create_final_communities_new.parquet", merged_communities.to_parquet()
    )

    # Merge community reports
    old_community_reports = await _load_table_from_storage(
        "create_final_community_reports.parquet", storage
    )
    delta_community_reports = dataframe_dict["create_final_community_reports"]

    merged_community_reports = _update_and_merge_community_reports(
        old_community_reports, delta_community_reports, community_id_mapping
    )

    await storage.set(
        "create_final_community_reports_new.parquet",
        merged_community_reports.to_parquet(),
    )


async def _concat_dataframes(name, dataframe_dict, storage):
    """Concatenate the dataframes.

    Parameters
    ----------
    name : str
        The name of the dataframe to concatenate.
    dataframe_dict : dict[str, pd.DataFrame]
        The dictionary of dataframes from a pipeline run.
    storage : PipelineStorage
        The storage used to store the dataframes.
    """
    old_df = await _load_table_from_storage(f"{name}.parquet", storage)
    delta_df = dataframe_dict[name]

    # Merge the final documents
    final_df = pd.concat([old_df, delta_df], copy=False)

    # TODO: Using _new in the mean time, to compare outputs without overwriting the original
    await storage.set(f"{name}_new.parquet", final_df.to_parquet())


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
    # If a name exists in A and B, make a dictionary for {B.id : A.id}
    merged = delta_entities_df[["id", "name"]].merge(
        old_entities_df[["id", "name"]],
        on="name",
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

    # Group by name and resolve conflicts
    aggregated = (
        combined.groupby("name")
        .agg({
            "id": "first",
            "type": "first",
            "human_readable_id": "first",
            "graph_embedding": "first",
            "description": lambda x: os.linesep.join(x.astype(str)),  # Ensure str
            # Concatenate nd.array into a single list
            "text_unit_ids": lambda x: ",".join(str(i) for j in x.tolist() for i in j),
            # Keep only descriptions where the original value wasn't modified
            "description_embedding": lambda x: x.iloc[0] if len(x) == 1 else np.nan,
        })
        .reset_index()
    )

    # Force the result into a DataFrame
    resolved: pd.DataFrame = pd.DataFrame(aggregated)

    # Modify column order to keep consistency
    resolved = resolved.loc[
        :,
        [
            "id",
            "name",
            "description",
            "type",
            "human_readable_id",
            "graph_embedding",
            "text_unit_ids",
            "description_embedding",
        ],
    ]

    return resolved, id_mapping


def _update_and_merge_relationships(
    old_relationships: pd.DataFrame, delta_relationships: pd.DataFrame
) -> pd.DataFrame:
    """Update and merge relationships.

    Parameters
    ----------
    old_relationships : pd.DataFrame
        The old relationships.
    delta_relationships : pd.DataFrame
        The delta relationships.

    Returns
    -------
    pd.DataFrame
        The updated relationships.
    """
    # Increment the human readable id in b by the max of a
    # Ensure both columns are integers
    delta_relationships["human_readable_id"] = delta_relationships[
        "human_readable_id"
    ].astype(int)
    old_relationships["human_readable_id"] = old_relationships[
        "human_readable_id"
    ].astype(int)

    # Adjust delta_relationships IDs to be greater than any in old_relationships
    initial_id = old_relationships["human_readable_id"].max() + 1
    delta_relationships["human_readable_id"] = np.arange(
        initial_id, initial_id + len(delta_relationships)
    )

    # Merge the DataFrames without copying if possible
    final_relationships = pd.concat(
        [old_relationships, delta_relationships], ignore_index=True, copy=False
    )

    # Recalculate target and source degrees
    final_relationships["source_degree"] = final_relationships.groupby("source")[
        "target"
    ].transform("count")
    final_relationships["target_degree"] = final_relationships.groupby("target")[
        "source"
    ].transform("count")

    # Recalculate the rank of the relationships (source degree + target degree)
    final_relationships["rank"] = (
        final_relationships["source_degree"] + final_relationships["target_degree"]
    )

    return final_relationships


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
    delta_text_units["entity_ids"] = delta_text_units["entity_ids"].apply(
        lambda x: [entity_id_mapping.get(i, i) for i in x]
    )

    # Merge the final text units
    return pd.concat([old_text_units, delta_text_units], ignore_index=True, copy=False)


def _merge_and_resolve_nodes(
    old_nodes: pd.DataFrame, delta_nodes: pd.DataFrame, merged_entities_df: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Merge and resolve nodes.

    Parameters
    ----------
    old_nodes : pd.DataFrame
        The old nodes.
    delta_nodes : pd.DataFrame
        The delta nodes.

    Returns
    -------
    pd.DataFrame
        The merged nodes.
    dict
        The community id mapping.
    """
    # Increment all community ids by the max of the old nodes
    old_max_community_id = old_nodes["community"].fillna(0).astype(int).max()

    # Merge delta_nodes with merged_entities_df to get the new human_readable_id
    delta_nodes = delta_nodes.merge(
        merged_entities_df[["name", "human_readable_id"]],
        left_on="title",
        right_on="name",
        how="left",
        suffixes=("", "_new"),
    )

    # Replace existing human_readable_id with the new one from merged_entities_df
    delta_nodes["human_readable_id"] = delta_nodes.loc[
        :, "human_readable_id_new"
    ].combine_first(delta_nodes.loc[:, "human_readable_id"])

    # Drop the auxiliary column from the merge
    delta_nodes.drop(columns=["name", "human_readable_id_new"], inplace=True)

    # Increment only the non-NaN values in delta_nodes["community"]
    community_id_mapping = {
        v: v + old_max_community_id + 1
        for k, v in delta_nodes["community"].dropna().astype(int).items()
    }

    delta_nodes["community"] = delta_nodes["community"].where(
        delta_nodes["community"].isna(),
        delta_nodes["community"].fillna(0).astype(int) + old_max_community_id + 1,
    )

    # Concat the DataFrames
    concat_nodes = pd.concat([old_nodes, delta_nodes], ignore_index=True)
    columns_to_agg: dict[str, str | Callable] = {
        col: "first"
        for col in concat_nodes.columns
        if col not in ["description", "source_id", "level", "title"]
    }

    # Specify custom aggregation for description and source_id
    columns_to_agg.update({
        "description": lambda x: os.linesep.join(x.astype(str)),
        "source_id": lambda x: ",".join(str(i) for i in x.tolist()),
    })

    merged_nodes = (
        concat_nodes.groupby(["level", "title"]).agg(columns_to_agg).reset_index()
    )

    merged_nodes["community"] = old_nodes["community"].astype("Int64")

    return merged_nodes, community_id_mapping


def _update_and_merge_communities(
    old_communities: pd.DataFrame,
    delta_communities: pd.DataFrame,
    community_id_mapping: dict,
) -> pd.DataFrame:
    """Update and merge communities.

    Parameters
    ----------
    old_communities : pd.DataFrame
        The old communities.
    delta_communities : pd.DataFrame
        The delta communities.
    community_id_mapping : dict
        The community id mapping.

    Returns
    -------
    pd.DataFrame
        The updated communities.
    """
    # Check if size and period columns exist in the old_communities. If not, add them
    if "size" not in old_communities.columns:
        old_communities["size"] = None
    if "period" not in old_communities.columns:
        old_communities["period"] = None

    # Same for delta_communities
    if "size" not in delta_communities.columns:
        delta_communities["size"] = None
    if "period" not in delta_communities.columns:
        delta_communities["period"] = None

    # Look for community ids in community and replace them with the corresponding id in the mapping
    delta_communities["id"] = (
        delta_communities["id"]
        .astype("Int64")
        .apply(lambda x: community_id_mapping.get(x, x))
    )

    old_communities["id"] = old_communities["id"].astype("Int64")

    # Merge the final communities
    merged_communities = pd.concat(
        [old_communities, delta_communities], ignore_index=True, copy=False
    )

    # Rename title
    merged_communities["title"] = "Community " + merged_communities["id"].astype(str)
    return merged_communities


def _update_and_merge_community_reports(
    old_community_reports: pd.DataFrame,
    delta_community_reports: pd.DataFrame,
    community_id_mapping: dict,
) -> pd.DataFrame:
    """Update and merge community reports.

    Parameters
    ----------
    old_community_reports : pd.DataFrame
        The old community reports.
    delta_community_reports : pd.DataFrame
        The delta community reports.
    community_id_mapping : dict
        The community id mapping.

    Returns
    -------
    pd.DataFrame
        The updated community reports.
    """
    # Check if size and period columns exist in the old_community_reports. If not, add them
    if "size" not in old_community_reports.columns:
        old_community_reports["size"] = None
    if "period" not in old_community_reports.columns:
        old_community_reports["period"] = None

    # Same for delta_community_reports
    if "size" not in delta_community_reports.columns:
        delta_community_reports["size"] = None
    if "period" not in delta_community_reports.columns:
        delta_community_reports["period"] = None

    # Look for community ids in community and replace them with the corresponding id in the mapping
    delta_community_reports["community"] = (
        delta_community_reports["community"]
        .astype("Int64")
        .apply(lambda x: community_id_mapping.get(x, x))
    )

    old_community_reports["community"] = old_community_reports["community"].astype(
        "Int64"
    )

    # Merge the final community reports
    return pd.concat(
        [old_community_reports, delta_community_reports], ignore_index=True, copy=False
    )
