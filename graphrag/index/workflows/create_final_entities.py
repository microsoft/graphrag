# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_entities import (
    create_final_entities,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_final_entities"


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final entities."""
    base_entity_nodes = await context.runtime_storage.get("base_entity_nodes")

    output = create_final_entities(base_entity_nodes)

    await snapshot(
        output,
        name="create_final_entities",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
