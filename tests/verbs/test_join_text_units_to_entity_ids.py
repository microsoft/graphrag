# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.config import create_graphrag_config
from graphrag.index.workflows.v1.join_text_units_to_entity_ids import build_steps

from .util import compare_outputs, get_workflow_output, load_expected, load_input_tables


async def test_join_text_units_to_entity_ids():
    input_tables = load_input_tables([
        "workflow:create_final_entities",
    ])
    expected = load_expected("join_text_units_to_entity_ids")

    config = create_graphrag_config()

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": build_steps(config),
        },
    )

    compare_outputs(actual, expected)
