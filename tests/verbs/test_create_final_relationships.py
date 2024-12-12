# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.flows.create_final_relationships import (
    create_final_relationships,
)
from graphrag.index.workflows.v1.create_final_relationships import (
    workflow_name,
)

from .util import (
    compare_outputs,
    load_test_table,
)


def test_create_final_relationships():
    edges = load_test_table("base_relationship_edges")
    expected = load_test_table(workflow_name)

    actual = create_final_relationships(edges)

    assert "id" in expected.columns
    columns = list(expected.columns.values)
    columns.remove("id")
    compare_outputs(actual, expected, columns)
    assert len(actual.columns) == len(expected.columns)
