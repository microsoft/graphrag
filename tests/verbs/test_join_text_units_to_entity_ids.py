# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.join_text_units_to_entity_ids import build_steps
from .util import load_input_tables, load_expected, get_workflow_output

async def test_join_text_units_to_entity_ids():
    
    input_tables = load_input_tables([
        'workflow:create_final_entities',
    ])
    expected = load_expected('join_text_units_to_entity_ids')

    actual = await get_workflow_output(input_tables, {
        "steps": build_steps(None),
    })

    try:
        assert actual.shape == expected.shape
    except AssertionError:
        print("Expected:")
        print(expected.head())
        print("Actual:")
        print(actual.head())
        raise AssertionError