# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

from dataclasses import dataclass

import pandas as pd
from datashaper import VerbCallbacks

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.config.pipeline import PipelineConfig
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.update.communities import (
    _merge_and_resolve_nodes,
    _update_and_merge_communities,
    _update_and_merge_community_reports,
)
from graphrag.index.update.entities import (
    _group_and_resolve_entities,
    _run_entity_description_embedding,
    _run_entity_summarization,
)
from graphrag.index.update.relationships import _update_and_merge_relationships
from graphrag.utils.storage import _load_table_from_storage


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
    update_storage: PipelineStorage,
    config: PipelineConfig,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
) -> None:
    """Update the mergeable outputs.

    Parameters
    ----------
    dataframe_dict : dict[str, pd.DataFrame]
        The dictionary of dataframes.
    storage : PipelineStorage
        The storage used to store the dataframes.
    """
    await _concat_dataframes(
        "create_final_documents", dataframe_dict, storage, update_storage
    )

    old_entities = await _load_table_from_storage(
        "create_final_entities.parquet", storage
    )
    delta_entities = dataframe_dict["create_final_entities"]

    merged_entities_df, entity_id_mapping = _group_and_resolve_entities(
        old_entities, delta_entities
    )

    # Re-run description summarization and embeddings
    merged_entities_df = await _run_entity_summarization(
        merged_entities_df,
        config,
        cache,
        callbacks,
    )
    merged_entities_df = await _run_entity_description_embedding(
        merged_entities_df, config, cache, callbacks
    )

    # Save the updated entities back to storage
    await update_storage.set(
        "create_final_entities.parquet", merged_entities_df.to_parquet()
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

    await update_storage.set(
        "create_final_relationships.parquet", merged_relationships_df.to_parquet()
    )

    # Update and merge final text units
    old_text_units = await _load_table_from_storage(
        "create_final_text_units.parquet", storage
    )
    delta_text_units = dataframe_dict["create_final_text_units"]

    merged_text_units = _update_and_merge_text_units(
        old_text_units, delta_text_units, entity_id_mapping
    )

    await update_storage.set(
        "create_final_text_units.parquet", merged_text_units.to_parquet()
    )

    # Merge final nodes and update community ids
    old_nodes = await _load_table_from_storage("create_final_nodes.parquet", storage)
    delta_nodes = dataframe_dict["create_final_nodes"]

    merged_nodes, community_id_mapping = _merge_and_resolve_nodes(
        old_nodes, delta_nodes, merged_entities_df
    )

    await update_storage.set("create_final_nodes.parquet", merged_nodes.to_parquet())

    # Merge final communities
    old_communities = await _load_table_from_storage(
        "create_final_communities.parquet", storage
    )
    delta_communities = dataframe_dict["create_final_communities"]
    merged_communities = _update_and_merge_communities(
        old_communities, delta_communities, community_id_mapping
    )

    await update_storage.set(
        "create_final_communities.parquet", merged_communities.to_parquet()
    )

    # Merge community reports
    old_community_reports = await _load_table_from_storage(
        "create_final_community_reports.parquet", storage
    )
    delta_community_reports = dataframe_dict["create_final_community_reports"]

    merged_community_reports = _update_and_merge_community_reports(
        old_community_reports, delta_community_reports, community_id_mapping
    )

    await update_storage.set(
        "create_final_community_reports.parquet",
        merged_community_reports.to_parquet(),
    )


async def _concat_dataframes(name, dataframe_dict, storage, update_storage):
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

    await update_storage.set(f"{name}.parquet", final_df.to_parquet())


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

    # Merge the final text units
    return pd.concat([old_text_units, delta_text_units], ignore_index=True, copy=False)
