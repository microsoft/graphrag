# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.create_final_documents import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    get_workflow_output,
    load_input_tables,
    load_test_table,
)


async def test_create_final_documents():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
    ])
    expected = load_test_table(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
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


async def test_create_final_documents_with_attribute_columns():
    input_tables = load_input_tables(["workflow:create_base_text_units"])
    expected = load_test_table(workflow_name)

    context = create_run_context(None, None, None)
    await context.runtime_storage.set(
        "base_text_units", input_tables["workflow:create_base_text_units"]
    )

    config = get_config_for_workflow(workflow_name)

    config["document_attribute_columns"] = ["title"]

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context=context,
    )

    # we should have dropped "title" and added "attributes"
    # our test dataframe does not have attributes, so we'll assert without it
    # and separately confirm it is in the output
    compare_outputs(
        actual, expected, columns=["id", "human_readable_id", "text", "text_unit_ids"]
    )
    assert len(actual.columns) == 5
    assert "title" not in actual.columns
    assert "attributes" in actual.columns
