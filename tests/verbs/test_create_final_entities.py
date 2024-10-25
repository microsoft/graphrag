# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

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

    config = get_config_for_workflow(workflow_name)

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    # ignore the description_embedding column, which is included in the expected output due to default config
    compare_outputs(
        actual,
        expected,
        columns=[
            "id",
            "name",
            "type",
            "description",
            "human_readable_id",
            "graph_embedding",
            "text_unit_ids",
        ],
    )
    assert len(actual.columns) == len(expected.columns) - 1
