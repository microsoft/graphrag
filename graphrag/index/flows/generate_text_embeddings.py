# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform the text units."""

import logging

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.config.embeddings import (
    community_full_content_embedding,
    community_summary_embedding,
    community_title_embedding,
    document_raw_content_embedding,
    entity_description_embedding,
    entity_name_embedding,
    relationship_description_embedding,
    text_unit_text_embedding,
)
from graphrag.index.operations.embed_text import embed_text
from graphrag.index.operations.snapshot import snapshot
from graphrag.index.storage import PipelineStorage

log = logging.getLogger(__name__)


async def generate_text_embeddings(
    final_documents: pd.DataFrame | None,
    final_relationships: pd.DataFrame | None,
    final_text_units: pd.DataFrame | None,
    final_entities: pd.DataFrame | None,
    final_community_reports: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    text_embed_config: dict,
    embedded_fields: set[str],
    embeddings_snapshot_enabled: bool = False,
) -> None:
    """All the steps to generate all embeddings."""
    embedding_param_map = {
        document_raw_content_embedding: {
            "data": final_documents.loc[:, ["id", "raw_content"]]
            if final_documents is not None
            else None,
            "column_to_embed": "raw_content",
        },
        relationship_description_embedding: {
            "data": final_relationships.loc[:, ["id", "description"]]
            if final_relationships is not None
            else None,
            "column_to_embed": "description",
        },
        text_unit_text_embedding: {
            "data": final_text_units.loc[:, ["id", "text"]]
            if final_text_units is not None
            else None,
            "column_to_embed": "text",
        },
        entity_name_embedding: {
            "data": final_entities.loc[:, ["id", "name", "description"]]
            if final_entities is not None
            else None,
            "column_to_embed": "name",
        },
        entity_description_embedding: {
            "data": final_entities.loc[:, ["id", "name", "description"]].assign(
                name_description=lambda df: df["name"] + ":" + df["description"]
            )
            if final_entities is not None
            else None,
            "column_to_embed": "name_description",
        },
        community_title_embedding: {
            "data": final_community_reports.loc[
                :, ["id", "full_content", "summary", "title"]
            ]
            if final_community_reports is not None
            else None,
            "column_to_embed": "title",
        },
        community_summary_embedding: {
            "data": final_community_reports.loc[
                :, ["id", "full_content", "summary", "title"]
            ]
            if final_community_reports is not None
            else None,
            "column_to_embed": "summary",
        },
        community_full_content_embedding: {
            "data": final_community_reports.loc[
                :, ["id", "full_content", "summary", "title"]
            ]
            if final_community_reports is not None
            else None,
            "column_to_embed": "full_content",
        },
    }

    log.info("Creating embeddings")
    for field in embedded_fields:
        await _run_and_snapshot_embeddings(
            name=field,
            callbacks=callbacks,
            cache=cache,
            storage=storage,
            text_embed_config=text_embed_config,
            embeddings_snapshot_enabled=embeddings_snapshot_enabled,
            **embedding_param_map[field],
        )


async def _run_and_snapshot_embeddings(
    name: str,
    data: pd.DataFrame,
    column_to_embed: str,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    text_embed_config: dict,
    embeddings_snapshot_enabled: bool,
) -> None:
    """All the steps to generate single embedding."""
    if text_embed_config:
        data["embedding"] = await embed_text(
            data,
            callbacks,
            cache,
            embed_column=column_to_embed,
            embedding_name=name,
            strategy=text_embed_config["strategy"],
        )

        data = data.loc[:, ["id", "embedding"]]

        if embeddings_snapshot_enabled is True:
            await snapshot(
                data,
                name=f"embeddings.{name}",
                storage=storage,
                formats=["parquet"],
            )
