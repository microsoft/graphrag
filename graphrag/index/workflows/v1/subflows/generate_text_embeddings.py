# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform the text units."""

import logging
from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    VerbResult,
    create_verb_result,
    verb,
)

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.flows.generate_text_embeddings import (
    generate_text_embeddings as generate_text_embeddings_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.utils.ds_util import get_required_input_table

log = logging.getLogger(__name__)


@verb(name="generate_text_embeddings", treats_input_tables_as_immutable=True)
async def generate_text_embeddings(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    text_embed: dict,
    embedded_fields: set[str],
    snapshot_embeddings_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to generate embeddings."""
    source = cast(pd.DataFrame, input.get_input())
    final_relationships = cast(
        pd.DataFrame, get_required_input_table(input, "relationships").table
    )
    final_text_units = cast(
        pd.DataFrame, get_required_input_table(input, "text_units").table
    )
    final_entities = cast(
        pd.DataFrame, get_required_input_table(input, "entities").table
    )

    final_community_reports = cast(
        pd.DataFrame, get_required_input_table(input, "community_reports").table
    )

    await generate_text_embeddings_flow(
        final_documents=source,
        final_relationships=final_relationships,
        final_text_units=final_text_units,
        final_entities=final_entities,
        final_community_reports=final_community_reports,
        callbacks=callbacks,
        cache=cache,
        storage=storage,
        text_embed_config=text_embed,
        embedded_fields=embedded_fields,
        snapshot_embeddings_enabled=snapshot_embeddings_enabled,
    )

    return create_verb_result(cast(Table, pd.DataFrame()))
