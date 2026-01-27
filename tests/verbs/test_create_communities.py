# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.data_model.schemas import COMMUNITIES_FINAL_COLUMNS
from graphrag.index.workflows.create_communities import (
    run_workflow,
)

from tests.unit.config.utils import get_default_graphrag_config

from .util import (
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

    config = get_default_graphrag_config()

    await run_workflow(
        config,
        context,
    )

    actual = await context.output_table_provider.read_dataframe("communities")

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
