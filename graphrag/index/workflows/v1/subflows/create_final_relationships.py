# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

from typing import cast

from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_relationships import (
    create_final_relationships as create_final_relationships_flow,
)
from graphrag.storage.pipeline_storage import PipelineStorage


@verb(
    name="create_final_relationships",
    treats_input_tables_as_immutable=True,
)
async def create_final_relationships(
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final relationships."""
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")
    base_entity_nodes = await runtime_storage.get("base_entity_nodes")

    output = create_final_relationships_flow(base_relationship_edges, base_entity_nodes)

    return create_verb_result(cast("Table", output))
