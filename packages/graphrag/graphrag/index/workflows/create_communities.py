# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from datetime import datetime, timezone
from typing import Any, cast
from uuid import uuid4

import numpy as np
import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.data_model.schemas import COMMUNITIES_FINAL_COLUMNS
from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform final communities."""
    logger.info("Workflow started: create_communities")
    reader = DataReader(context.output_table_provider)
    relationships = await reader.relationships()

    title_to_entity_id: dict[str, str] = {}
    async with context.output_table_provider.open("entities") as entities_table:
        async for row in entities_table:
            title_to_entity_id[row["title"]] = row["id"]

    max_cluster_size = config.cluster_graph.max_cluster_size
    use_lcc = config.cluster_graph.use_lcc
    seed = config.cluster_graph.seed

    output = create_communities(
        title_to_entity_id,
        relationships,
        max_cluster_size=max_cluster_size,
        use_lcc=use_lcc,
        seed=seed,
    )

    rows = output.to_dict("records")
    sample_size = min(5, len(rows))
    sample_rows = rows[:sample_size]

    async with context.output_table_provider.open("communities") as table:
        for row in rows:
            await table.write(cast("dict[str, Any]", row))

    logger.info("Workflow completed: create_communities")
    return WorkflowFunctionOutput(result=sample_rows)


def create_communities(
    title_to_entity_id: dict[str, str],
    relationships: pd.DataFrame,
    max_cluster_size: int,
    use_lcc: bool,
    seed: int | None = None,
) -> pd.DataFrame:
    """Build community DataFrame from clustered relationships.

    Args
    ----
        title_to_entity_id: dict[str, str]
            Mapping of entity title to entity id.
        relationships: pd.DataFrame
            Relationships DataFrame with source, target, weight,
            text_unit_ids columns.
        max_cluster_size: int
            Maximum cluster size for hierarchical Leiden.
        use_lcc: bool
            Whether to restrict to the largest connected component.
        seed: int | None
            Random seed for deterministic clustering.

    Returns
    -------
        pd.DataFrame
            Communities DataFrame with COMMUNITIES_FINAL_COLUMNS schema.
    """
    clusters = cluster_graph(
        relationships,
        max_cluster_size,
        use_lcc,
        seed=seed,
    )

    communities = pd.DataFrame(
        clusters, columns=pd.Index(["level", "community", "parent", "title"])
    ).explode("title")
    communities["community"] = communities["community"].astype(int)

    # aggregate entity ids for each community
    entity_map = communities[["community", "title"]].copy()
    entity_map["entity_id"] = entity_map["title"].map(title_to_entity_id)
    entity_ids = (
        entity_map
        .dropna(subset=["entity_id"])
        .groupby("community")
        .agg(entity_ids=("entity_id", list))
        .reset_index()
    )

    # aggregate relationship ids per community, limited to
    # intra-community edges (source and target in the same community).
    # Process one hierarchy level at a time to keep intermediate
    # DataFrames small, then concat the grouped results once at the end.
    level_results = []
    for level in communities["level"].unique():
        level_comms = communities[communities["level"] == level]
        with_source = relationships.merge(
            level_comms, left_on="source", right_on="title", how="inner"
        )
        with_both = with_source.merge(
            level_comms, left_on="target", right_on="title", how="inner"
        )
        intra = with_both[with_both["community_x"] == with_both["community_y"]]
        if intra.empty:
            continue
        grouped = (
            intra
            .explode("text_unit_ids")
            .groupby(["community_x", "parent_x"])
            .agg(
                relationship_ids=("id", list),
                text_unit_ids=("text_unit_ids", list),
            )
            .reset_index()
        )
        grouped["level"] = level
        level_results.append(grouped)

    all_grouped = pd.concat(level_results, ignore_index=True).rename(
        columns={
            "community_x": "community",
            "parent_x": "parent",
        }
    )

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
