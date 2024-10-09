# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.create_final_relationships import (
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


async def test_create_final_relationships():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
        "workflow:create_final_nodes",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_description_embedding"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    compare_outputs(actual, expected)


async def test_create_final_relationships_with_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
        "workflow:create_final_nodes",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_description_embedding"] = False
    # default config has a detailed standard embed config
    # just override the strategy to mock so the rest of the required parameters are in place
    config["relationship_description_embed"]["strategy"]["type"] = "mock"

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert "description_embedding" in actual.columns
    assert len(actual.columns) == len(expected.columns) + 1
    # the mock impl returns an array of 3 floats for each embedding
    assert len(actual["description_embedding"][:1][0]) == 3
