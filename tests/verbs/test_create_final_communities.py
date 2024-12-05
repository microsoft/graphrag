# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.flows.create_final_communities import (
    create_final_communities,
)
from graphrag.index.workflows.v1.create_final_communities import (
    workflow_name,
)

from .util import (
    compare_outputs,
    load_test_table,
)


def test_create_final_communities():
    base_entity_nodes = load_test_table("base_entity_nodes")
    base_relationship_edges = load_test_table("base_relationship_edges")
    base_communities = load_test_table("base_communities")

    expected = load_test_table(workflow_name)

    actual = create_final_communities(
        base_entity_nodes=base_entity_nodes,
        base_relationship_edges=base_relationship_edges,
        base_communities=base_communities,
    )

    assert "period" in expected.columns
    assert "id" in expected.columns
    columns = list(expected.columns.values)
    columns.remove("period")
    columns.remove("id")
    compare_outputs(
        actual,
        expected,
        columns=columns,
    )
