# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Indexing-Engine to Query Read Adapters.

The parts of these functions that do type adaptation, renaming, collating, etc. should eventually go away.
Ideally this is just a straight read-through into the object model.
"""

import logging
from typing import cast

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.summarize_communities import restore_community_hierarchy
from graphrag.model.community import Community
from graphrag.model.community_report import CommunityReport
from graphrag.model.covariate import Covariate
from graphrag.model.entity import Entity
from graphrag.model.relationship import Relationship
from graphrag.model.text_unit import TextUnit
from graphrag.query.factories import get_text_embedder
from graphrag.query.input.loaders.dfs import (
    read_communities,
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
)
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.vector_stores.base import BaseVectorStore

log = logging.getLogger(__name__)


def read_indexer_text_units(final_text_units: pd.DataFrame) -> list[TextUnit]:
    """Read in the Text Units from the raw indexing outputs."""
    return read_text_units(
        df=final_text_units,
        # expects a covariate map of type -> ids
        covariates_col=None,
    )


def read_indexer_covariates(final_covariates: pd.DataFrame) -> list[Covariate]:
    """Read in the Claims from the raw indexing outputs."""
    covariate_df = final_covariates
    covariate_df["id"] = covariate_df["id"].astype(str)
    return read_covariates(
        df=covariate_df,
        short_id_col="human_readable_id",
        attributes_cols=[
            "object_id",
            "status",
            "start_date",
            "end_date",
            "description",
        ],
        text_unit_ids_col=None,
    )


def read_indexer_relationships(final_relationships: pd.DataFrame) -> list[Relationship]:
    """Read in the Relationships from the raw indexing outputs."""
    # rank is for back-compat with older indexes
    # TODO: remove for 1.0
    rank_col = (
        "combined_degree"
        if "combined_degree" in final_relationships.columns
        else "rank"
    )
    return read_relationships(
        df=final_relationships,
        short_id_col="human_readable_id",
        rank_col=rank_col,
        description_embedding_col=None,
        attributes_cols=None,
    )


def read_indexer_reports(
    final_community_reports: pd.DataFrame,
    final_nodes: pd.DataFrame,
    community_level: int | None,
    dynamic_community_selection: bool = False,
    content_embedding_col: str = "full_content_embedding",
    config: GraphRagConfig | None = None,
) -> list[CommunityReport]:
    """Read in the Community Reports from the raw indexing outputs.

    If not dynamic_community_selection, then select reports with the max community level that an entity belongs to.
    """
    reports_df = final_community_reports
    nodes_df = final_nodes

    if community_level is not None:
        nodes_df = _filter_under_community_level(nodes_df, community_level)
        reports_df = _filter_under_community_level(reports_df, community_level)

    if not dynamic_community_selection:
        # perform community level roll up
        nodes_df.loc[:, "community"] = nodes_df["community"].fillna(-1)
        nodes_df.loc[:, "community"] = nodes_df["community"].astype(int)

        nodes_df = nodes_df.groupby(["title"]).agg({"community": "max"}).reset_index()
        filtered_community_df = nodes_df["community"].drop_duplicates()

        # todo: pre 1.0 back-compat where community was a string
        reports_df.loc[:, "community"] = reports_df["community"].fillna(-1)
        reports_df.loc[:, "community"] = reports_df["community"].astype(int)

        reports_df = reports_df.merge(
            filtered_community_df, on="community", how="inner"
        )

    if config and (
        content_embedding_col not in reports_df.columns
        or reports_df.loc[:, content_embedding_col].isna().any()
    ):
        embedder = get_text_embedder(config)
        reports_df = embed_community_reports(
            reports_df, embedder, embedding_col=content_embedding_col
        )

    return read_community_reports(
        df=reports_df,
        id_col="id",
        short_id_col="community",
        summary_embedding_col=None,
        content_embedding_col=content_embedding_col,
    )


def read_indexer_report_embeddings(
    community_reports: list[CommunityReport],
    embeddings_store: BaseVectorStore,
):
    """Read in the Community Reports from the raw indexing outputs."""
    for report in community_reports:
        report.full_content_embedding = embeddings_store.search_by_id(report.id).vector


def read_indexer_entities(
    final_nodes: pd.DataFrame,
    final_entities: pd.DataFrame,
    community_level: int | None,
) -> list[Entity]:
    """Read in the Entities from the raw indexing outputs."""
    nodes_df = final_nodes
    entities_df = final_entities

    if community_level is not None:
        nodes_df = _filter_under_community_level(nodes_df, community_level)

    nodes_df = cast(pd.DataFrame, nodes_df[["id", "degree", "community"]])

    nodes_df["community"] = nodes_df["community"].fillna(-1)
    nodes_df["community"] = nodes_df["community"].astype(int)
    nodes_df["degree"] = nodes_df["degree"].astype(int)

    # group entities by id and degree and remove duplicated community IDs
    nodes_df = nodes_df.groupby(["id", "degree"]).agg({"community": set}).reset_index()
    nodes_df["community"] = nodes_df["community"].apply(lambda x: [str(i) for i in x])
    final_df = nodes_df.merge(entities_df, on="id", how="inner").drop_duplicates(
        subset=["id"]
    )

    # todo: pre 1.0 back-compat where title was name
    if "title" not in final_df.columns:
        final_df["title"] = final_df["name"]

    # read entity dataframe to knowledge model objects
    return read_entities(
        df=final_df,
        id_col="id",
        title_col="title",
        type_col="type",
        short_id_col="human_readable_id",
        description_col="description",
        community_col="community",
        rank_col="degree",
        name_embedding_col=None,
        description_embedding_col="description_embedding",
        text_unit_ids_col="text_unit_ids",
    )


def read_indexer_communities(
    final_communities: pd.DataFrame,
    final_nodes: pd.DataFrame,
    final_community_reports: pd.DataFrame,
) -> list[Community]:
    """Read in the Communities from the raw indexing outputs.

    Reconstruct the community hierarchy information and add to the sub-community field.
    """
    communities_df = final_communities
    nodes_df = final_nodes
    reports_df = final_community_reports

    # todo: pre 1.0 back-compat!
    if "community" not in communities_df.columns:
        communities_df["community"] = communities_df["id"]

    # ensure communities matches community reports
    missing_reports = communities_df[
        ~communities_df.community.isin(reports_df.community.unique())
    ].community.to_list()
    if len(missing_reports):
        log.warning("Missing reports for communities: %s", missing_reports)
        communities_df = communities_df.loc[
            communities_df.community.isin(reports_df.community.unique())
        ]
        nodes_df = nodes_df.loc[nodes_df.community.isin(reports_df.community.unique())]

    # reconstruct the community hierarchy
    # note that restore_community_hierarchy only return communities with sub communities
    community_hierarchy = restore_community_hierarchy(input=nodes_df)

    # small datasets can result in hierarchies that are only one deep, so the hierarchy will have no rows
    if not community_hierarchy.empty:
        community_hierarchy = (
            community_hierarchy.groupby(["community"])
            .agg({"sub_community": list})
            .reset_index()
            .rename(columns={"sub_community": "sub_community_ids"})
        )
        # add sub community IDs to community DataFrame
        communities_df = communities_df.merge(
            community_hierarchy, on="community", how="left"
        )
        # replace NaN sub community IDs with empty list
        communities_df.sub_community_ids = communities_df.sub_community_ids.apply(
            lambda x: x if isinstance(x, list) else []
        )

    return read_communities(
        communities_df,
        id_col="id",
        short_id_col="community",
        title_col="title",
        level_col="level",
        entities_col=None,
        relationships_col=None,
        covariates_col=None,
        sub_communities_col="sub_community_ids",
        attributes_cols=None,
    )


def embed_community_reports(
    reports_df: pd.DataFrame,
    embedder: OpenAIEmbedding,
    source_col: str = "full_content",
    embedding_col: str = "full_content_embedding",
) -> pd.DataFrame:
    """Embed a source column of the reports dataframe using the given embedder."""
    if source_col not in reports_df.columns:
        error_msg = f"Reports missing {source_col} column"
        raise ValueError(error_msg)

    if embedding_col not in reports_df.columns:
        reports_df[embedding_col] = reports_df.loc[:, source_col].apply(
            lambda x: embedder.embed(x)
        )

    return reports_df


def _filter_under_community_level(
    df: pd.DataFrame, community_level: int
) -> pd.DataFrame:
    return cast(
        pd.DataFrame,
        df[df.level <= community_level],
    )
