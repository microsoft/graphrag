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

from graphrag.index.cache import PipelineCache
from graphrag.index.flows.create_final_embeddings import (
    create_final_embeddings as create_final_embeddings_flow,
)
from graphrag.index.storage import PipelineStorage
from graphrag.index.utils.ds_util import get_required_input_table

log = logging.getLogger(__name__)


@verb(name="create_final_embeddings", treats_input_tables_as_immutable=True)
async def create_final_embeddings(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    storage: PipelineStorage,
    embedded_fields: set[str],
    base_text_embed: dict | None = None,
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

    output = await create_final_embeddings_flow(
        final_documents=source,
        final_relationships=final_relationships,
        final_text_units=final_text_units,
        final_entities=final_entities,
        final_community_reports=final_community_reports,
        callbacks=callbacks,
        cache=cache,
        storage=storage,
        embedded_fields=embedded_fields,
        base_text_embed=base_text_embed,
    )

    return create_verb_result(cast(Table, output))
