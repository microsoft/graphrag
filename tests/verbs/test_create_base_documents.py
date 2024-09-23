# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.create_base_documents import (
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


async def test_create_base_documents():
    input_tables = load_input_tables(["workflow:create_final_text_units"])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    compare_outputs(actual, expected)


async def test_create_base_documents_with_attribute_columns():
    input_tables = load_input_tables(["workflow:create_final_text_units"])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["document_attribute_columns"] = ["title"]

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    # we should have dropped "title" and added "attributes"
    # our test dataframe does not have attributes, so we'll assert without it
    # and separately confirm it is in the output
    compare_outputs(actual, expected, columns=["id", "text_units", "raw_content"])
    assert len(actual.columns) == 4
    assert "attributes" in actual.columns
