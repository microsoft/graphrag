# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_communities import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_final_communities():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_entity_graph", input_tables["workflow:create_base_entity_graph"]
    )

    steps = build_steps({})

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    # ignore the period and id columns, because they recalculated every time
    assert "period" in expected.columns
    assert "id" in expected.columns
    columns = list(expected.columns.values)
    columns.remove("period")
    columns.remove("id")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )
