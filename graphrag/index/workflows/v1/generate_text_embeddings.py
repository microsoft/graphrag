# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

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

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.generate_text_embeddings import (
    generate_text_embeddings,
)
from graphrag.index.utils.ds_util import get_required_input_table
from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)

workflow_name = "generate_text_embeddings"

input = {
    "source": "workflow:create_final_documents",
    "relationships": "workflow:create_final_relationships",
    "text_units": "workflow:create_final_text_units",
    "entities": "workflow:create_final_entities",
    "community_reports": "workflow:create_final_community_reports",
}


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final embeddings files.

    ## Dependencies
    * `workflow:create_final_documents`
    * `workflow:create_final_relationships`
    * `workflow:create_final_text_units`
    * `workflow:create_final_entities`
    * `workflow:create_final_community_reports`
    """
    text_embed = config.get("text_embed", {})
    embedded_fields = config.get("embedded_fields", {})
    snapshot_embeddings = config.get("snapshot_embeddings", False)
    return [
        {
            "verb": workflow_name,
            "args": {
                "text_embed": text_embed,
                "embedded_fields": embedded_fields,
                "snapshot_embeddings_enabled": snapshot_embeddings,
            },
            "input": input,
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
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
    source = cast("pd.DataFrame", input.get_input())
    final_relationships = cast(
        "pd.DataFrame", get_required_input_table(input, "relationships").table
    )
    final_text_units = cast(
        "pd.DataFrame", get_required_input_table(input, "text_units").table
    )
    final_entities = cast(
        "pd.DataFrame", get_required_input_table(input, "entities").table
    )

    final_community_reports = cast(
        "pd.DataFrame", get_required_input_table(input, "community_reports").table
    )

    await generate_text_embeddings(
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

    return create_verb_result(cast("Table", pd.DataFrame()))
