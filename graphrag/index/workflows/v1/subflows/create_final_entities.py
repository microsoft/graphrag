# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

from typing import cast

from datashaper import (
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_entities import (
    create_final_entities as create_final_entities_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage


@verb(
    name="create_final_entities",
    treats_input_tables_as_immutable=True,
)
async def create_final_entities(
    callbacks: VerbCallbacks,
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final entities."""
    entity_graph = await runtime_storage.get("base_entity_graph")

    output = create_final_entities_flow(
        entity_graph,
        callbacks,
    )

    return create_verb_result(cast(Table, output))
