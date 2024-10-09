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

    config["skip_name_embedding"] = True
    config["skip_description_embedding"] = True

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


async def test_create_final_entities_with_name_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_name_embedding"] = False
    config["skip_description_embedding"] = True
    config["entity_name_embed"]["strategy"]["type"] = "mock"

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert "name_embedding" in actual.columns
    assert len(actual.columns) == len(expected.columns)
    # the mock impl returns an array of 3 floats for each embedding
    assert len(actual["name_embedding"][:1][0]) == 3


async def test_create_final_entities_with_description_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_name_embedding"] = True
    config["skip_description_embedding"] = False
    config["entity_name_description_embed"]["strategy"]["type"] = "mock"

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert "description_embedding" in actual.columns
    assert len(actual.columns) == len(expected.columns)
    assert len(actual["description_embedding"][:1][0]) == 3


async def test_create_final_entities_with_name_and_description_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_entity_graph",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_name_embedding"] = False
    config["skip_description_embedding"] = False
    config["entity_name_description_embed"]["strategy"]["type"] = "mock"
    config["entity_name_embed"]["strategy"]["type"] = "mock"

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert "description_embedding" in actual.columns
    assert len(actual.columns) == len(expected.columns) + 1
    assert len(actual["description_embedding"][:1][0]) == 3
