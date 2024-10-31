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
    embedded_fields: set[str],
    full_content_text_embed: dict | None = None,
    summary_text_embed: dict | None = None,
    title_text_embed: dict | None = None,
    raw_content_text_embed: dict | None = None,
    name_text_embed: dict | None = None,
    name_description_text_embed: dict | None = None,
    description_text_embed: dict | None = None,
    text_text_embed: dict | None = None,
) -> None:
    """All the steps to generate all embeddings."""
    entities_embeddings = (
        final_entities.loc[:, ["id", "name", "description"]]
        if final_entities is not None
        else None
    )
    if entities_embeddings is not None:
        entities_embeddings["name_description"] = (
            entities_embeddings["name"] + ":" + entities_embeddings["description"]
        )

    embedding_param_map = {
        document_raw_content_embedding: {
            "data": final_documents.loc[:, ["id", "raw_content"]]
            if final_documents is not None
            else None,
            "column_to_embed": "raw_content",
            "filename": "create_final_documents_raw_content_embeddings",
            "base_text_embed": raw_content_text_embed,
        },
        relationship_description_embedding: {
            "data": final_relationships.loc[:, ["id", "description"]]
            if final_relationships is not None
            else None,
            "column_to_embed": "description",
            "filename": "create_final_relationships_description_embeddings",
            "base_text_embed": description_text_embed,
        },
        text_unit_text_embedding: {
            "data": final_text_units.loc[:, ["id", "text"]]
            if final_text_units is not None
            else None,
            "column_to_embed": "text",
            "filename": "create_final_text_units_text_embeddings",
            "base_text_embed": text_text_embed,
        },
        entity_name_embedding: {
            "data": entities_embeddings,
            "column_to_embed": "name",
            "filename": "create_final_entities_name_embeddings",
            "base_text_embed": name_text_embed,
        },
        entity_description_embedding: {
            "data": entities_embeddings,
            "column_to_embed": "name_description",
            "filename": "create_final_entities_description_embeddings",
            "base_text_embed": name_description_text_embed,
        },
        community_title_embedding: {
            "data": final_community_reports.loc[
                :, ["id", "full_content", "summary", "title"]
            ]
            if final_community_reports is not None
            else None,
            "column_to_embed": "title",
            "filename": "create_final_community_reports_title_embeddings",
            "base_text_embed": title_text_embed,
        },
        community_summary_embedding: {
            "data": final_community_reports.loc[
                :, ["id", "full_content", "summary", "title"]
            ]
            if final_community_reports is not None
            else None,
            "column_to_embed": "summary",
            "filename": "create_final_community_reports_summary_embeddings",
            "base_text_embed": summary_text_embed,
        },
        community_full_content_embedding: {
            "data": final_community_reports.loc[
                :, ["id", "full_content", "summary", "title"]
            ]
            if final_community_reports is not None
            else None,
            "column_to_embed": "full_content",
            "filename": "create_final_community_reports_full_content_embeddings",
            "base_text_embed": full_content_text_embed,
        },
    }

    log.info("Creating embeddings")
    for field in embedded_fields:
        await _run_and_snapshot_embeddings(
            callbacks=callbacks,
            cache=cache,
            storage=storage,
            **embedding_param_map[field],
        )


async def _run_and_snapshot_embeddings(
    data: pd.DataFrame,
    column_to_embed: str,
    filename: str,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    base_text_embed: dict | None = None,
) -> None:
    """All the steps to generate single embedding."""
    if base_text_embed:
        data["embedding"] = await embed_text(
            data,
            callbacks,
            cache,
            column=column_to_embed,
            strategy=base_text_embed["strategy"],
        )

        data = data.loc[:, ["id", "embedding"]]

        if base_text_embed["strategy"]["vector_store"]["snapshot"] is True:
            await snapshot(
                data,
                name=filename,
                storage=storage,
                formats=["parquet"],
            )
