# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

import numpy as np
import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import COMMUNITIES_FINAL_COLUMNS
from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform final communities."""
    entities = await load_table_from_storage("entities", context.storage)
    relationships = await load_table_from_storage("relationships", context.storage)

    max_cluster_size = config.cluster_graph.max_cluster_size
    use_lcc = config.cluster_graph.use_lcc
    seed = config.cluster_graph.seed

    output = create_communities(
        entities,
        relationships,
        max_cluster_size=max_cluster_size,
        use_lcc=use_lcc,
        seed=seed,
    )

    await write_table_to_storage(output, "communities", context.storage)

    return WorkflowFunctionOutput(result=output)


def create_communities(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    max_cluster_size: int,
    use_lcc: bool,
    seed: int | None = None,
) -> pd.DataFrame:
    """All the steps to transform final communities."""
    graph = create_graph(relationships, edge_attr=["weight"])

    clusters = cluster_graph(
        graph,
        max_cluster_size,
        use_lcc,
        seed=seed,
    )

    communities = pd.DataFrame(
        clusters, columns=pd.Index(["level", "community", "parent", "title"])
    ).explode("title")
    communities["community"] = communities["community"].astype(int)

    # aggregate entity ids for each community
    entity_ids = communities.merge(entities, on="title", how="inner")
    entity_ids = (
        entity_ids.groupby("community").agg(entity_ids=("id", list)).reset_index()
    )

    # aggregate relationships ids for each community
    # these are limited to only those where the source and target are in the same community
    max_level = communities["level"].max()
    all_grouped = pd.DataFrame(
        columns=["community", "level", "relationship_ids", "text_unit_ids"]  # type: ignore
    )
    for level in range(max_level + 1):
        communities_at_level = communities.loc[communities["level"] == level]
        sources = relationships.merge(
            communities_at_level, left_on="source", right_on="title", how="inner"
        )
        targets = sources.merge(
            communities_at_level, left_on="target", right_on="title", how="inner"
        )
        matched = targets.loc[targets["community_x"] == targets["community_y"]]
        text_units = matched.explode("text_unit_ids")
        grouped = (
            text_units.groupby(["community_x", "level_x", "parent_x"])
            .agg(relationship_ids=("id", list), text_unit_ids=("text_unit_ids", list))
            .reset_index()
        )
        grouped.rename(
            columns={
                "community_x": "community",
                "level_x": "level",
                "parent_x": "parent",
            },
            inplace=True,
        )
        all_grouped = pd.concat([
            all_grouped,
            grouped.loc[
                :, ["community", "level", "parent", "relationship_ids", "text_unit_ids"]
            ],
        ])

    # deduplicate the lists
    all_grouped["relationship_ids"] = all_grouped["relationship_ids"].apply(
        lambda x: sorted(set(x))
    )
    all_grouped["text_unit_ids"] = all_grouped["text_unit_ids"].apply(
        lambda x: sorted(set(x))
    )

    # join it all up and add some new fields
    final_communities = all_grouped.merge(entity_ids, on="community", how="inner")
    final_communities["id"] = [str(uuid4()) for _ in range(len(final_communities))]
    final_communities["human_readable_id"] = final_communities["community"]
    final_communities["title"] = "Community " + final_communities["community"].astype(
        str
    )
    final_communities["parent"] = final_communities["parent"].astype(int)
    # collect the children so we have a tree going both ways
    parent_grouped = cast(
        "pd.DataFrame",
        final_communities.groupby("parent").agg(children=("community", "unique")),
    )
    final_communities = final_communities.merge(
        parent_grouped,
        left_on="community",
        right_on="parent",
        how="left",
    )
    # replace NaN children with empty list
    final_communities["children"] = final_communities["children"].apply(
        lambda x: x if isinstance(x, np.ndarray) else []  # type: ignore
    )
    # add fields for incremental update tracking
    final_communities["period"] = datetime.now(timezone.utc).date().isoformat()
    final_communities["size"] = final_communities.loc[:, "entity_ids"].apply(len)

    return final_communities.loc[
        :,
        COMMUNITIES_FINAL_COLUMNS,
    ]
