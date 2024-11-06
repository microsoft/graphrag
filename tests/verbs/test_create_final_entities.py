# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_entities import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_final_entities():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_entity_graph", input_tables["workflow:create_base_entity_graph"]
    )

    config = get_config_for_workflow(workflow_name)

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    compare_outputs(actual, expected)
    assert len(actual.columns) == len(expected.columns)
