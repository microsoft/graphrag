# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

import logging
from typing import cast

from datashaper import (
    Table,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_entities import (
    create_final_entities as create_final_entities_flow,
)
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "create_final_entities"
log = logging.getLogger(__name__)


def build_steps(
    config: PipelineWorkflowConfig,  # noqa: ARG001
) -> list[PipelineWorkflowStep]:
    """
    Create the final entities table.

    ## Dependencies
    * `workflow:extract_graph`
    """
    return [
        {
            "verb": "create_final_entities",
            "args": {},
            "input": {"source": "workflow:extract_graph"},
        },
    ]


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
