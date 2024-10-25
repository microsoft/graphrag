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
    final_documents: pd.DataFrame,
    final_relationships: pd.DataFrame,
    final_text_units: pd.DataFrame,
    final_entities: pd.DataFrame,
    final_community_reports: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    embedded_fields: set[str],
    base_text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to generate all embeddings."""
    documents_embeddings = final_documents.loc[:, ["id", "raw_content"]]
    relationships_embeddings = final_relationships.loc[:, ["id", "description"]]
    text_units_embeddings = final_text_units.loc[:, ["id", "text"]]

    entities_embeddings = final_entities.loc[:, ["id", "name", "description"]]
    entities_embeddings["name_description"] = (
        entities_embeddings["name"] + ":" + entities_embeddings["description"]
    )

    community_reports_embeddings = final_community_reports.loc[
        :, ["id", "full_content", "summary", "title"]
    ]

    embedding_param_map = {
        document_raw_content_embedding: {
            "data": documents_embeddings,
            "column_to_embed":"raw_content",
            "filename": "create_final_documents_raw_content_embeddings",
        },
        relationship_description_embedding:{
            "data": relationships_embeddings,
            "column_to_embed":"description",
            "filename": "create_final_relationships_description_embeddings",
        },
        text_unit_text_embedding:{
            "data": text_units_embeddings,
            "column_to_embed":"text",
            "filename": "create_final_text_units_text_embeddings",
        },
        entity_name_embedding:{
            "data": entities_embeddings,
            "column_to_embed":"name",
            "filename": "create_final_entities_name_embeddings",
        },
        entity_description_embedding:{
            "data": entities_embeddings,
            "column_to_embed":"name_description",
            "filename": "create_final_entities_description_embeddings",
        },
        community_title_embedding:{
            "data": community_reports_embeddings,
            "column_to_embed":"title",
            "filename": "create_final_community_reports_title_embeddings",
        },
        community_summary_embedding:{
            "data": community_reports_embeddings,
            "column_to_embed":"summary",
            "filename": "create_final_community_reports_summary_embeddings",
        },
        community_full_content_embedding:{
            "data": community_reports_embeddings,
            "column_to_embed":"full_content",
            "filename": "create_final_community_reports_full_content_embeddings",
        },
    
    }

    if base_text_embed:
        log.info("Creating embeddings")
        for field in embedded_fields:
            await _run_and_snapshot_embeddings(
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                **embedding_param_map[field]
            )

    return pd.DataFrame()


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

    await snapshot(
        data,
        name=filename,
        storage=storage,
        formats=["parquet"],
    )
