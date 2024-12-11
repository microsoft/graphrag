# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import cast

from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_communities import (
    create_final_communities,
)
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "create_final_communities"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final communities table.

    ## Dependencies
    * `workflow:extract_graph`
    """
    return [
        {
            "verb": workflow_name,
            "input": {"source": "workflow:extract_graph"},
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final communities."""
    base_entity_nodes = await runtime_storage.get("base_entity_nodes")
    base_relationship_edges = await runtime_storage.get("base_relationship_edges")
    base_communities = await runtime_storage.get("base_communities")
    output = create_final_communities(
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
