# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from datashaper import NoopVerbCallbacks

from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.index.flows.create_final_nodes import (
    create_final_nodes,
)
from graphrag.index.workflows.v1.create_final_nodes import (
    workflow_name,
)

from .util import (
    compare_outputs,
    load_test_table,
)


def test_create_final_nodes():
    base_entity_nodes = load_test_table("base_entity_nodes")
    base_relationship_edges = load_test_table("base_relationship_edges")
    base_communities = load_test_table("base_communities")

    expected = load_test_table(workflow_name)

    embed_config = EmbedGraphConfig(enabled=False)
    actual = create_final_nodes(
        base_entity_nodes=base_entity_nodes,
        base_relationship_edges=base_relationship_edges,
        base_communities=base_communities,
        callbacks=NoopVerbCallbacks(),
        embed_config=embed_config,
        layout_enabled=False,
    )

    assert "id" in expected.columns
    columns = list(expected.columns.values)
    columns.remove("id")
    compare_outputs(actual, expected, columns)
    assert len(actual.columns) == len(expected.columns)
