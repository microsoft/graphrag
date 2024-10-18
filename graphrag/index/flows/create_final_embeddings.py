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


async def create_final_embeddings(
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

    if base_text_embed:
        log.info("Creating embeddings")
        # Embed raw_content in documents table
        if document_raw_content_embedding in embedded_fields and isinstance(
            documents_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=documents_embeddings,
                column_to_embed="raw_content",
                filename="create_final_documents_raw_content_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Documents embeddings (raw content)",
            )

        # Embed description in relationships table
        if relationship_description_embedding in embedded_fields and isinstance(
            relationships_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=relationships_embeddings,
                column_to_embed="description",
                filename="create_final_relationships_description_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Relationships embeddings (description)",
            )

        # Embed text in text_units table
        if text_unit_text_embedding in embedded_fields and isinstance(
            text_units_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=text_units_embeddings,
                column_to_embed="text",
                filename="create_final_text_units_text_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Text units embeddings (text)",
            )

        # Embed name in entities table
        if entity_name_embedding in embedded_fields and isinstance(
            entities_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=entities_embeddings,
                column_to_embed="name",
                filename="create_final_entities_name_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Entities embeddings (name)",
            )

        # Embed name+description in entities table
        if entity_description_embedding in embedded_fields and isinstance(
            entities_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=entities_embeddings,
                column_to_embed="name_description",
                filename="create_final_entities_description_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Entities embeddings (description)",
            )

        # Embed title in community reports table
        if community_title_embedding in embedded_fields and isinstance(
            community_reports_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=community_reports_embeddings,
                column_to_embed="title",
                filename="create_final_community_reports_title_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Community reports embeddings (title)",
            )

        # Embed summary in community reports table
        if community_summary_embedding in embedded_fields and isinstance(
            community_reports_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=community_reports_embeddings,
                column_to_embed="summary",
                filename="create_final_community_reports_summary_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Community reports embeddings (summary)",
            )

        # Embed full_content in community reports table
        if community_full_content_embedding in embedded_fields and isinstance(
            community_reports_embeddings, pd.DataFrame
        ):
            await run_embeddings(
                data=community_reports_embeddings,
                column_to_embed="full_content",
                filename="create_final_community_reports_full_content_embeddings",
                callbacks=callbacks,
                cache=cache,
                storage=storage,
                base_text_embed=base_text_embed,
                message="Community reports embeddings (full_content)",
            )

    return pd.DataFrame()


async def run_embeddings(
    data: pd.DataFrame,
    column_to_embed: str,
    filename: str,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    base_text_embed: dict | None = None,
    message: str | None = None,
) -> None:
    """All the steps to generate single embedding."""
    if base_text_embed:
        log.info("%s", message)
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
