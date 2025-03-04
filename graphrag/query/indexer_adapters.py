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
from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.data_model.covariate import Covariate
from graphrag.data_model.entity import Entity
from graphrag.data_model.relationship import Relationship
from graphrag.data_model.text_unit import TextUnit
from graphrag.language_model.manager import ModelManager
from graphrag.language_model.protocol.base import EmbeddingModel
from graphrag.query.input.loaders.dfs import (
    read_communities,
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
)
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
    return read_relationships(
        df=final_relationships,
        short_id_col="human_readable_id",
        rank_col="combined_degree",
        description_embedding_col=None,
        attributes_cols=None,
    )


def read_indexer_reports(
    final_community_reports: pd.DataFrame,
    final_communities: pd.DataFrame,
    community_level: int | None,
    dynamic_community_selection: bool = False,
    content_embedding_col: str = "full_content_embedding",
    config: GraphRagConfig | None = None,
) -> list[CommunityReport]:
    """Read in the Community Reports from the raw indexing outputs.

    If not dynamic_community_selection, then select reports with the max community level that an entity belongs to.
    """
    reports_df = final_community_reports
    nodes_df = final_communities.explode("entity_ids")

    if community_level is not None:
        nodes_df = _filter_under_community_level(nodes_df, community_level)
        reports_df = _filter_under_community_level(reports_df, community_level)

    if not dynamic_community_selection:
        # perform community level roll up
        nodes_df.loc[:, "community"] = nodes_df["community"].fillna(-1)
        nodes_df.loc[:, "community"] = nodes_df["community"].astype(int)

        nodes_df = nodes_df.groupby(["title"]).agg({"community": "max"}).reset_index()
        filtered_community_df = nodes_df["community"].drop_duplicates()

        reports_df = reports_df.merge(
            filtered_community_df, on="community", how="inner"
        )

    if config and (
        content_embedding_col not in reports_df.columns
        or reports_df.loc[:, content_embedding_col].isna().any()
    ):
        # TODO: Find a way to retrieve the right embedding model id.
        embedding_model_settings = config.get_language_model_config(
            "default_embedding_model"
        )
        embedder = ModelManager().get_or_create_embedding_model(
            name="default_embedding",
            model_type=embedding_model_settings.type,
            config=embedding_model_settings,
        )
        reports_df = embed_community_reports(
            reports_df, embedder, embedding_col=content_embedding_col
        )

    return read_community_reports(
        df=reports_df,
        id_col="id",
        short_id_col="community",
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
    entities: pd.DataFrame,
    communities: pd.DataFrame,
    community_level: int | None,
) -> list[Entity]:
    """Read in the Entities from the raw indexing outputs."""
    community_join = communities.explode("entity_ids").loc[
        :, ["community", "level", "entity_ids"]
    ]
    nodes_df = entities.merge(
        community_join, left_on="id", right_on="entity_ids", how="left"
    )

    if community_level is not None:
        nodes_df = _filter_under_community_level(nodes_df, community_level)

    nodes_df = nodes_df.loc[:, ["id", "community"]]
    nodes_df["community"] = nodes_df["community"].fillna(-1)
    # group entities by id and degree and remove duplicated community IDs
    nodes_df = nodes_df.groupby(["id"]).agg({"community": set}).reset_index()
    nodes_df["community"] = nodes_df["community"].apply(
        lambda x: [str(int(i)) for i in x]
    )
    final_df = nodes_df.merge(entities, on="id", how="inner").drop_duplicates(
        subset=["id"]
    )
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
    final_community_reports: pd.DataFrame,
) -> list[Community]:
    """Read in the Communities from the raw indexing outputs.

    Reconstruct the community hierarchy information and add to the sub-community field.
    """
    communities_df = final_communities
    nodes_df = communities_df.explode("entity_ids")
    reports_df = final_community_reports

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

    return read_communities(
        communities_df,
        id_col="id",
        short_id_col="community",
        title_col="title",
        level_col="level",
        entities_col=None,
        relationships_col=None,
        covariates_col=None,
        parent_col="parent",
        children_col="children",
        attributes_cols=None,
    )


def embed_community_reports(
    reports_df: pd.DataFrame,
    embedder: EmbeddingModel,
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
        "pd.DataFrame",
        df[df.level <= community_level],
    )
