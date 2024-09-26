# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.create_final_documents import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
    remove_disabled_steps,
)


async def test_create_final_documents():
    input_tables = load_input_tables([
        "workflow:create_base_documents",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_raw_content_embedding"] = True

    steps = remove_disabled_steps(build_steps(config))

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    compare_outputs(actual, expected)


async def test_create_final_documents_with_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_documents",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["skip_raw_content_embedding"] = False
    # default config has a detailed standard embed config
    # just override the strategy to mock so the rest of the required parameters are in place
    config["document_raw_content_embed"]["strategy"]["type"] = "mock"

    steps = remove_disabled_steps(build_steps(config))

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert "raw_content_embedding" in actual.columns
    assert len(actual.columns) == len(expected.columns) + 1
    # the mock impl returns an array of 3 floats for each embedding
    assert len(actual["raw_content_embedding"][:1][0]) == 3
