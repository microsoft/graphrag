# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.flows.compute_communities import (
    compute_communities,
)
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.compute_communities import (
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    load_test_table,
)


async def test_compute_communities():
    edges = load_test_table("base_relationship_edges")
    expected = load_test_table("base_communities")

    context = create_run_context(None, None, None)
    config = get_config_for_workflow(workflow_name)
    clustering_strategy = config["cluster_graph"]["strategy"]

    actual = await compute_communities(
        edges, storage=context.storage, clustering_strategy=clustering_strategy
    )

    columns = list(expected.columns.values)
    compare_outputs(actual, expected, columns)
    assert len(actual.columns) == len(expected.columns)


async def test_compute_communities_with_snapshots():
    edges = load_test_table("base_relationship_edges")

    context = create_run_context(None, None, None)
    config = get_config_for_workflow(workflow_name)
    clustering_strategy = config["cluster_graph"]["strategy"]

    await compute_communities(
        edges,
        storage=context.storage,
        clustering_strategy=clustering_strategy,
        snapshot_transient_enabled=True,
    )

    assert context.storage.keys() == [
        "base_communities.parquet",
    ], "Community snapshot keys differ"
