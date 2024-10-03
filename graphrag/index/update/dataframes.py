# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


import numpy as np
import pandas as pd

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

    merged_text_units_df = _update_and_merge_text_units(
        old_text_units, delta_text_units, entity_id_mapping
    )

    # TODO: Using _new in the meantime, to compare outputs without overwriting the original
    await storage.set(
        "create_final_text_units_new.parquet", merged_text_units_df.to_parquet()
    )

    # Update final nodes
    old_nodes = await _load_table_from_storage("create_final_nodes.parquet", storage)
    delta_nodes = dataframe_dict["create_final_nodes"]

    merged_nodes = _merge_and_update_nodes(
        old_nodes,
        delta_nodes,
        merged_relationships_df,
    )

    await storage.set("create_final_nodes_new.parquet", merged_nodes.to_parquet())


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
        .agg(
            {
                "id": "first",
                "type": "first",
                "human_readable_id": "first",
                "graph_embedding": "first",
                "description": lambda x: os.linesep.join(x.astype(str)),  # Ensure str
                # Concatenate nd.array into a single list
                "text_unit_ids": lambda x: ",".join(
                    str(i) for j in x.tolist() for i in j
                ),
                # Keep only descriptions where the original value wasn't modified
                "description_embedding": lambda x: x.iloc[0] if len(x) == 1 else np.nan,
            }
        )
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
    old_relationships: pd.DataFrame,
    delta_relationships: pd.DataFrame,
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


def _merge_and_update_nodes(
    old_nodes: pd.DataFrame,
    delta_nodes: pd.DataFrame,
    merged_relationships_df: pd.DataFrame,
    community_count_threshold: int = 2,
) -> pd.DataFrame:
    """Merge and update nodes.

    Parameters
    ----------
    old_nodes : pd.DataFrame
        The old nodes.
    delta_nodes : pd.DataFrame
        The delta nodes.
    merged_relationships_df : pd.DataFrame
        The merged relationships.
    community_count_threshold : int, optional
        The community count threshold, by default 2.
        If a node has enough relationships to a community, it will be assigned to that community.

    Returns
    -------
    pd.DataFrame
        The updated nodes.
    """
    # Increment all community ids by the max of the old nodes
    old_max_community_id = old_nodes["community"].fillna(0).astype(int).max()

    # Increment only the non-NaN values in delta_nodes["community"]
    delta_nodes["community"] = delta_nodes["community"].where(
        delta_nodes["community"].isna(),
        delta_nodes["community"].fillna(0).astype(int) + old_max_community_id + 1,
    )

    # Set index for comparison
    old_nodes_index = old_nodes.set_index(["level", "title"]).index
    delta_nodes_index = delta_nodes.set_index(["level", "title"]).index

    # Get all delta nodes that are not in the old nodes
    new_delta_nodes_df = delta_nodes[
        ~delta_nodes_index.isin(old_nodes_index)
    ].reset_index(drop=True)

    # Get all delta nodes that are in the old nodes
    existing_delta_nodes_df = delta_nodes[
        delta_nodes_index.isin(old_nodes_index)
    ].reset_index(drop=True)

    # Concat the DataFrames
    concat_nodes = pd.concat([old_nodes, existing_delta_nodes_df], ignore_index=True)
    columns_to_agg: dict[str, str | Callable] = {
        col: "first"
        for col in concat_nodes.columns
        if col not in ["description", "source_id", "level", "title"]
    }

    # Specify custom aggregation for description and source_id
    columns_to_agg.update(
        {
            "description": lambda x: os.linesep.join(x.astype(str)),
            "source_id": lambda x: ",".join(str(i) for i in x.tolist()),
        }
    )

    old_nodes = (
        concat_nodes.groupby(["level", "title"]).agg(columns_to_agg).reset_index()
    )

    new_delta_nodes_df = _assign_communities(
        new_delta_nodes_df,
        merged_relationships_df,
        old_nodes,
        community_count_threshold,
    )

    # Concatenate the old nodes with the new delta nodes
    merged_final_nodes = pd.concat(
        [old_nodes, new_delta_nodes_df], ignore_index=True, copy=False
    )

    merged_final_nodes["community"] = (
        merged_final_nodes["community"].fillna("").astype(str)
    )

    # Merge both source and target degrees
    merged_final_nodes = merged_final_nodes.merge(
        merged_relationships_df[["source", "source_degree"]],
        how="left",
        left_on="title",
        right_on="source",
    ).merge(
        merged_relationships_df[["target", "target_degree"]],
        how="left",
        left_on="title",
        right_on="target",
    )

    # Assign 'source_degree' to 'size' and 'degree'
    merged_final_nodes["size"] = merged_final_nodes["source_degree"]

    # Fill NaN values in 'size' and 'degree' with target_degree
    merged_final_nodes["size"] = merged_final_nodes["size"].fillna(
        merged_final_nodes["target_degree"]
    )
    merged_final_nodes["degree"] = merged_final_nodes["size"]

    # Drop duplicates and the auxiliary 'source', 'target, 'source_degree' and 'target_degree' columns
    return merged_final_nodes.drop(
        columns=["source", "source_degree", "target", "target_degree"]
    ).drop_duplicates()


def _assign_communities(
    new_delta_nodes_df: pd.DataFrame,
    merged_relationships_df: pd.DataFrame,
    old_nodes: pd.DataFrame,
    community_count_threshold: int = 2,
) -> pd.DataFrame:
    """Assign communities to new delta nodes based on the most common community of related nodes.

    Parameters
    ----------
    new_delta_nodes_df : pd.DataFrame
        The new delta nodes.
    merged_relationships_df : pd.DataFrame
        The merged relationships.
    old_nodes : pd.DataFrame
        The old nodes.
    community_count_threshold : int, optional
        The community count threshold, by default 2.
        If a node has enough relationships to a community, it will be assigned to that community.
    """
    # Find all relationships for the new delta nodes
    node_relationships = merged_relationships_df[
        merged_relationships_df["source"].isin(new_delta_nodes_df["title"])
        | merged_relationships_df["target"].isin(new_delta_nodes_df["title"])
    ]

    # Find old nodes that are related to these relationships
    related_communities = old_nodes[
        old_nodes["title"].isin(node_relationships["source"])
        | old_nodes["title"].isin(node_relationships["target"])
    ]

    # Merge with new_delta_nodes_df to get the level and community info
    related_communities = related_communities.merge(
        new_delta_nodes_df[["level", "title"]], on=["level", "title"], how="inner"
    )

    # Count the communities for each (level, title) pair
    community_counts = (
        related_communities.groupby(["level", "title"])["community"]
        .value_counts()
        .reset_index(name="count")
    )

    # Filter by community threshold and select the most common community for each node
    most_common_communities = community_counts[
        community_counts["count"] >= community_count_threshold
    ]
    most_common_communities = (
        most_common_communities.groupby(["level", "title"]).first().reset_index()
    )

    # Merge the most common community information back into new_delta_nodes_df
    new_delta_nodes_df = new_delta_nodes_df.merge(
        most_common_communities[["level", "title", "community"]],
        on=["level", "title"],
        how="left",
        suffixes=("", "_new"),
    )

    # Update the community in new_delta_nodes_df if a common community was found
    new_delta_nodes_df["community"] = new_delta_nodes_df["community_new"].combine_first(
        new_delta_nodes_df["community"]
    )

    # Drop the auxiliary column used for merging
    new_delta_nodes_df.drop(columns=["community_new"], inplace=True)

    return new_delta_nodes_df
