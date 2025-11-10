# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import COMMUNITIES_FINAL_COLUMNS
from graphrag.index.workflows.create_communities import (
    run_workflow,
)
from graphrag.utils.storage import load_table_from_storage

from .util import (
    DEFAULT_MODEL_CONFIG,
    compare_outputs,
    create_test_context,
    load_test_table,
)


async def test_create_communities():
    expected = load_test_table("communities")

    context = await create_test_context(
        storage=[
            "entities",
            "relationships",
        ],
    )

    config = GraphRagConfig(models=DEFAULT_MODEL_CONFIG)  # type: ignore

    await run_workflow(
        config,
        context,
    )

    actual = await load_table_from_storage("communities", context.output_storage)

    columns = list(expected.columns.values)
    # don't compare period since it is created with the current date each time
    columns.remove("period")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )

    for column in COMMUNITIES_FINAL_COLUMNS:
        assert column in actual.columns
