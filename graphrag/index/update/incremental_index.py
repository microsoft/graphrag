# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.embeddings import get_embedded_fields, get_embedding_settings
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.update.communities import (
    _update_and_merge_communities,
    _update_and_merge_community_reports,
)
from graphrag.index.update.entities import (
    _group_and_resolve_entities,
    _run_entity_summarization,
)
from graphrag.index.update.relationships import _update_and_merge_relationships
from graphrag.index.workflows.generate_text_embeddings import generate_text_embeddings
from graphrag.logger.print_progress import ProgressLogger
from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import (
    load_table_from_storage,
    storage_has_table,
    write_table_to_storage,
)


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
    final_docs = await load_table_from_storage("documents", storage)

    # Select distinct title from final docs and from dataset
    previous_docs: list[str] = final_docs["title"].unique().tolist()
    dataset_docs: list[str] = input_dataset["title"].unique().tolist()

    # Get the new documents (using loc to ensure DataFrame)
    new_docs = input_dataset.loc[~input_dataset["title"].isin(previous_docs)]

    # Get the deleted documents (again using loc to ensure DataFrame)
    deleted_docs = final_docs.loc[~final_docs["title"].isin(dataset_docs)]

    return InputDelta(new_docs, deleted_docs)


async def update_dataframe_outputs(
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
    config: GraphRagConfig,
    cache: PipelineCache,
    callbacks: WorkflowCallbacks,
    progress_logger: ProgressLogger,
) -> None:
    """Update the mergeable outputs.

    Parameters
    ----------
    previous_storage : PipelineStorage
        The storage used to store the dataframes in the original run.
    delta_storage : PipelineStorage
        The storage used to store the subset of new dataframes in the update run.
    output_storage : PipelineStorage
        The storage used to store the updated dataframes (the final incremental output).
    """
    progress_logger.info("Updating Documents")
    final_documents_df = await _concat_dataframes(
        "documents", previous_storage, delta_storage, output_storage
    )

    # Update entities and merge them
    progress_logger.info("Updating Entities")
    merged_entities_df, entity_id_mapping = await _update_entities(
        previous_storage, delta_storage, output_storage, config, cache, callbacks
    )

    # Update relationships with the entities id mapping
    progress_logger.info("Updating Relationships")
    merged_relationships_df = await _update_relationships(
        previous_storage, delta_storage, output_storage
    )

    # Update and merge final text units
    progress_logger.info("Updating Text Units")
    merged_text_units = await _update_text_units(
        previous_storage, delta_storage, output_storage, entity_id_mapping
    )

    # Merge final covariates
    if await storage_has_table(
        "covariates", previous_storage
    ) and await storage_has_table("covariates", delta_storage):
        progress_logger.info("Updating Covariates")
        await _update_covariates(previous_storage, delta_storage, output_storage)

    # Merge final communities
    progress_logger.info("Updating Communities")
    community_id_mapping = await _update_communities(
        previous_storage, delta_storage, output_storage
    )

    # Merge community reports
    progress_logger.info("Updating Community Reports")
    merged_community_reports = await _update_community_reports(
        previous_storage, delta_storage, output_storage, community_id_mapping
    )

    # Generate text embeddings
    progress_logger.info("Updating Text Embeddings")
    embedded_fields = get_embedded_fields(config)
    text_embed = get_embedding_settings(config)
    await generate_text_embeddings(
        final_documents=final_documents_df,
        final_relationships=merged_relationships_df,
        final_text_units=merged_text_units,
        final_entities=merged_entities_df,
        final_community_reports=merged_community_reports,
        callbacks=callbacks,
        cache=cache,
        storage=output_storage,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
        snapshot_embeddings_enabled=config.snapshots.embeddings,
    )


async def _update_community_reports(
    previous_storage, delta_storage, output_storage, community_id_mapping
):
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


async def _update_communities(previous_storage, delta_storage, output_storage):
    """Update the communities output."""
    old_communities = await load_table_from_storage("communities", previous_storage)
    delta_communities = await load_table_from_storage("communities", delta_storage)
    merged_communities, community_id_mapping = _update_and_merge_communities(
        old_communities, delta_communities
    )

    await write_table_to_storage(merged_communities, "communities", output_storage)

    return community_id_mapping


async def _update_covariates(previous_storage, delta_storage, output_storage):
    """Update the covariates output."""
    old_covariates = await load_table_from_storage("covariates", previous_storage)
    delta_covariates = await load_table_from_storage("covariates", delta_storage)
    merged_covariates = _merge_covariates(old_covariates, delta_covariates)

    await write_table_to_storage(merged_covariates, "covariates", output_storage)


async def _update_text_units(
    previous_storage, delta_storage, output_storage, entity_id_mapping
):
    """Update the text units output."""
    old_text_units = await load_table_from_storage("text_units", previous_storage)
    delta_text_units = await load_table_from_storage("text_units", delta_storage)
    merged_text_units = _update_and_merge_text_units(
        old_text_units, delta_text_units, entity_id_mapping
    )

    await write_table_to_storage(merged_text_units, "text_units", output_storage)

    return merged_text_units


async def _update_relationships(previous_storage, delta_storage, output_storage):
    """Update the relationships output."""
    old_relationships = await load_table_from_storage("relationships", previous_storage)
    delta_relationships = await load_table_from_storage("relationships", delta_storage)
    merged_relationships_df = _update_and_merge_relationships(
        old_relationships,
        delta_relationships,
    )

    await write_table_to_storage(
        merged_relationships_df, "relationships", output_storage
    )

    return merged_relationships_df


async def _update_entities(
    previous_storage, delta_storage, output_storage, config, cache, callbacks
):
    """Update Final Entities output."""
    old_entities = await load_table_from_storage("entities", previous_storage)
    delta_entities = await load_table_from_storage("entities", delta_storage)

    merged_entities_df, entity_id_mapping = _group_and_resolve_entities(
        old_entities, delta_entities
    )

    # Re-run description summarization
    merged_entities_df = await _run_entity_summarization(
        merged_entities_df,
        config,
        cache,
        callbacks,
    )

    # Save the updated entities back to storage
    await write_table_to_storage(merged_entities_df, "entities", output_storage)

    return merged_entities_df, entity_id_mapping


async def _concat_dataframes(name, previous_storage, delta_storage, output_storage):
    """Concatenate dataframes."""
    old_df = await load_table_from_storage(name, previous_storage)
    delta_df = await load_table_from_storage(name, delta_storage)

    # Merge the final documents
    initial_id = old_df["human_readable_id"].max() + 1
    delta_df["human_readable_id"] = np.arange(initial_id, initial_id + len(delta_df))
    final_df = pd.concat([old_df, delta_df], ignore_index=True, copy=False)

    await write_table_to_storage(final_df, name, output_storage)

    return final_df


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
