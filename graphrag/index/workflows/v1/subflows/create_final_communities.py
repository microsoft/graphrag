# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final communities."""

from typing import cast

from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.flows.create_final_communities import (
    create_final_communities as create_final_communities_flow,
)
from graphrag.storage.pipeline_storage import PipelineStorage


@verb(name="create_final_communities", treats_input_tables_as_immutable=True)
async def create_final_communities(
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final communities."""
    base_entity_nodes = await runtime_storage.get("base_entity_nodes")
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")
    base_communities = await runtime_storage.get("base_communities")
    output = create_final_communities_flow(
        base_entity_nodes,
        base_relationship_edges,
        base_communities,
    )

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
