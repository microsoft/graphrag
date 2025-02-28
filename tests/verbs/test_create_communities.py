# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config.create_graphrag_config import create_graphrag_config
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

    config = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})

    await run_workflow(
        config,
        context,
    )

    actual = await load_table_from_storage("communities", context.storage)

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
