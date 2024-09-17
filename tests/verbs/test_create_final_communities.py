# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

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


async def test_create_final_text_units():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    steps = build_steps({})

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    compare_outputs(actual, expected)
