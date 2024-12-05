# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.flows.create_final_entities import (
    create_final_entities,
)
from graphrag.index.workflows.v1.create_final_entities import (
    workflow_name,
)

from .util import (
    compare_outputs,
    load_test_table,
)


def test_create_final_entities():
    input = load_test_table("base_entity_nodes")
    expected = load_test_table(workflow_name)

    actual = create_final_entities(input)

    compare_outputs(actual, expected)
    assert len(actual.columns) == len(expected.columns)
