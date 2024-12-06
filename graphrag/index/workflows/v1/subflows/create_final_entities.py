# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

from typing import cast

from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_entities import (
    create_final_entities as create_final_entities_flow,
)
from graphrag.storage.pipeline_storage import PipelineStorage


@verb(
    name="create_final_entities",
    treats_input_tables_as_immutable=True,
)
async def create_final_entities(
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final entities."""
    base_entity_nodes = await runtime_storage.get("base_entity_nodes")

    output = create_final_entities_flow(base_entity_nodes)

    return create_verb_result(cast("Table", output))
