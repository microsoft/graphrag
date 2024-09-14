# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.join_text_units_to_relationship_ids import build_steps
from .util import load_input_tables, load_expected, get_workflow_output, compare_outputs

async def test_join_text_units_to_relationship_ids():

    input_tables = load_input_tables([
        'workflow:create_final_relationships',
    ])
    expected = load_expected('join_text_units_to_relationship_ids')

    actual = await get_workflow_output(input_tables, {
        "steps": build_steps(None),
    })

    compare_outputs(actual, expected)