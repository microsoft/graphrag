# Copyright (c) 2024 Microsoft Corporation. All rights reserved.
"""Indexing-Engine to Query Read Adapters. These should eventually go away, users should use the read_x functions instead."""

from typing import cast

import pandas as pd

from graphrag.model import CommunityReport, Covariate, Entity, Relationship, TextUnit
from graphrag.query.input.loaders.dfs import (
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
)
from graphrag.query.input.retrieval.relationships import (
    calculate_relationship_combined_rank,
)


def read_raw_covariates(final_covariates: pd.DataFrame) -> list[Covariate]:
    """Read in the Claims from the raw indexing outputs."""
    covariate_df = final_covariates
    covariate_df["human_readable_id"] = covariate_df["human_readable_id"].astype(str)
    try:
        covariate_df = cast(
            pd.DataFrame,
            covariate_df[
                [
                    "id",
                    "human_readable_id",
                    "type",
                    "subject_id",
                    "subject_type",
                    "object_id",
                    "status",
                    "start_date",
                    "end_date",
                    "description",
                ]
            ],
        )

    except:  # noqa: E722
        columns = [
            "id",
            "human_readable_id",
            "type",
            "subject_id",
            "object_id",
            "status",
            "start_date",
            "end_date",
            "description",
        ]
        covariate_df = pd.DataFrame({column: [] for column in columns})

    return read_covariates(
        df=covariate_df,
        id_col="id",
        short_id_col="human_readable_id",
        subject_col="subject_id",
        subject_type_col=None,
        covariate_type_col="type",
        attributes_cols=[
            "object_id",
            "status",
            "start_date",
            "end_date",
            "description",
        ],
        text_unit_ids_col=None,
        document_ids_col=None,
    )


def read_raw_reports(
    final_community_reports: pd.DataFrame,
    final_nodes: pd.DataFrame,
    community_level: int | None,
) -> list[CommunityReport]:
    """Read in the Community Reports from the raw indexing outputs."""
    report_df = final_community_reports
    entity_df = final_nodes

    if community_level is not None:
        entity_df = cast(
            pd.DataFrame,
            entity_df[
                (entity_df.type == "entity")
                & (entity_df.level <= f"level_{community_level}")
            ],
        )
    entity_df["community"] = entity_df["community"].fillna(-1)
    entity_df["community"] = entity_df["community"].astype(int)
    entity_df = entity_df.groupby(["title"]).agg({"community": "max"}).reset_index()
    entity_df["community"] = entity_df["community"].astype(str)
    filtered_community_df = entity_df["community"].drop_duplicates()

    if community_level is not None:
        report_df = cast(
            pd.DataFrame,
            report_df[report_df.level <= community_level],
        )

    report_df["rank"] = report_df["rank"].fillna(-1)
    report_df["rank"] = report_df["rank"].astype(int)
    report_df = report_df.merge(filtered_community_df, on="community", how="inner")

    return read_community_reports(
        df=report_df,
        id_col="community",
        short_id_col="community",
        community_col="community",
        title_col="title",
        summary_col="summary",
        content_col="full_content",
        rank_col="rank",
        summary_embedding_col=None,
        content_embedding_col=None,
    )


def read_raw_text_units(final_text_units: pd.DataFrame) -> list[TextUnit]:
    """Read in the Text Units from the raw indexing outputs."""
    return read_text_units(
        df=final_text_units,
        id_col="id",
        short_id_col=None,
        text_col="text",
        embedding_col="text_embedding",
        entities_col=None,
        relationships_col=None,
        covariates_col=None,
    )


def read_raw_entities(
    final_nodes: pd.DataFrame,
    final_entities: pd.DataFrame,
    community_level: int | None = None,
) -> list[Entity]:
    """Read in the Entities from the raw indexing outputs."""
    entity_df = final_nodes
    entity_embedding_df = final_entities

    if community_level is not None:
        entity_df = cast(
            pd.DataFrame,
            entity_df[
                (entity_df.type == "entity")
                & (entity_df.level <= f"level_{community_level}")
            ],
        )
    entity_df = cast(pd.DataFrame, entity_df[["title", "degree", "community"]]).rename(
        columns={"title": "name", "degree": "rank"}
    )

    entity_df["community"] = entity_df["community"].fillna(-1)
    entity_df["community"] = entity_df["community"].astype(int)
    entity_df["rank"] = entity_df["rank"].astype(int)

    # for duplicate entities, keep the one with the highest community level
    entity_df = (
        entity_df.groupby(["name", "rank"]).agg({"community": "max"}).reset_index()
    )
    entity_df["community"] = entity_df["community"].apply(lambda x: [str(x)])

    entity_embedding_df = cast(
        pd.DataFrame,
        entity_embedding_df[
            [
                "id",
                "human_readable_id",
                "name",
                "type",
                "description",
                "description_embedding",
                "text_unit_ids",
            ]
        ],
    )

    entity_df = entity_df.merge(
        entity_embedding_df, on="name", how="inner"
    ).drop_duplicates(subset=["name"])

    # read entity dataframe to knowledge model objects
    return read_entities(
        df=entity_df,
        id_col="id",
        title_col="name",
        type_col="type",
        short_id_col="human_readable_id",
        description_col="description",
        community_col="community",
        rank_col="rank",
        name_embedding_col=None,
        description_embedding_col="description_embedding",
        graph_embedding_col=None,
        text_unit_ids_col="text_unit_ids",
        document_ids_col=None,
    )


def read_raw_relationships(
    final_relationships: pd.DataFrame, entities: list[Entity]
) -> list[Relationship]:
    """Read in the Relationships from the raw indexing outputs."""
    relationship_df = final_relationships
    relationship_df["id"] = relationship_df["id"].astype(str)
    relationship_df["human_readable_id"] = relationship_df["human_readable_id"].astype(
        str
    )
    relationship_df["weight"] = relationship_df["weight"].astype(float)
    relationship_df["text_unit_ids"] = relationship_df["text_unit_ids"].apply(
        lambda x: x.split(",")
    )
    relationship_df = cast(
        pd.DataFrame,
        relationship_df[
            [
                "id",
                "human_readable_id",
                "source",
                "target",
                "description",
                "weight",
                "text_unit_ids",
            ]
        ],
    )
    relationships = read_relationships(
        df=relationship_df,
        id_col="id",
        short_id_col="human_readable_id",
        source_col="source",
        target_col="target",
        description_col="description",
        weight_col="weight",
        description_embedding_col=None,
        text_unit_ids_col="text_unit_ids",
        document_ids_col=None,
    )
    # TODO: compute combined rank in indexer output
    return calculate_relationship_combined_rank(
        relationships=relationships, entities=entities, ranking_attribute="rank"
    )
