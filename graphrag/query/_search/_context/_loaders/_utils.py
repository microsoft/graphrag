# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Module for reading and processing various graph data components such as
entities, community reports, relationships, covariates, and text units.

Functions:
    get_entities:
        Fetch and process entity data from a set of nodes and entities data
        frames.
    get_community_reports:
        Fetch and process community report data based on community levels.
    get_relationships: Fetch and process relationship data from a DataFrame.
    get_covariates: Fetch and process covariate data from a DataFrame.
    get_text_units: Fetch and process text unit data from a DataFrame.
    get_store: Store entity embeddings into a LanceDBVectorStore.
"""

from __future__ import annotations

import typing

import pandas as pd

from . import _defaults
from ... import _model
from ..._input._loaders import _dfs
from ...._vector_stores import LanceDBVectorStore


def get_entities(
    nodes: pd.DataFrame,
    entities: pd.DataFrame,
    community_level: int,
    *,
    id_col: typing.Optional[str] = None,
    short_id_col: typing.Optional[str] = None,
    title_col: typing.Optional[str] = None,
    type_col: typing.Optional[str] = None,
    description_col: typing.Optional[str] = None,
    name_embedding_col: typing.Optional[str] = None,
    description_embedding_col: typing.Optional[str] = None,
    graph_embedding_col: typing.Optional[str] = None,
    community_col: typing.Optional[str] = None,
    text_unit_ids_col: typing.Optional[str] = None,
    document_ids_col: typing.Optional[str] = None,
    rank_col: typing.Optional[str] = None,
    attributes_cols: typing.Optional[typing.List[str]] = None,
) -> typing.List[_model.Entity]:
    """
    Fetch and process entity data from a set of nodes and entities data frames,
    filtered by community level.

    Args:
        nodes: DataFrame containing the graph's node data.
        entities: DataFrame containing entity data.
        community_level: The maximum community level for filtering nodes.
        id_col: Column name for the entity ID.
        short_id_col: Column name for the entity's short ID.
        title_col: Column name for the entity's title.
        type_col: Column name for the entity's type.
        description_col: Column name for the entity's description.
        name_embedding_col: Column name for the entity name embeddings.
        description_embedding_col:
            Column name for the entity description embeddings.
        graph_embedding_col: Column name for the entity graph embeddings.
        community_col: Column name for the entity's community.
        text_unit_ids_col:
            Column name for the text unit IDs associated with the entity.
        document_ids_col:
            Column name for the document IDs associated with the entity.
        rank_col: Column name for the entity rank.
        attributes_cols: List of column names for the entity's attributes.

    Returns:
        A list of processed Entity objects.
    """
    # Filter entities by community level
    nodes_ = nodes.copy()
    nodes_ = typing.cast(pd.DataFrame, nodes_[nodes_.level <= community_level])

    # Rename columns
    nodes_ = nodes_[['title', 'degree', 'community']].copy()
    nodes_ = nodes_.rename(
        columns={"title": "name", "degree": "rank"}
    )

    # Fill missing values
    nodes_['community'] = nodes_['community'].fillna(-1)

    # Convert data types
    nodes_['community'] = nodes_['community'].astype(int)
    nodes_['rank'] = nodes_['rank'].astype(int)

    # Keep the entity with the highest community level
    nodes_ = nodes_.groupby(['name', 'rank']).agg({'community': 'max'}).reset_index()

    # Convert community to string
    nodes_['community'] = nodes_['community'].apply(lambda x: [str(x)])

    # Merge nodes and entities
    nodes_ = nodes_.merge(entities.copy(), on='name', how='inner').drop_duplicates(subset=['name'])

    return _dfs.read_entities(
        nodes_,
        id_col=id_col or _defaults.COLUMN__ENTITY__ID,
        title_col=title_col or _defaults.COLUMN__ENTITY__TITLE,
        type_col=type_col or _defaults.COLUMN__ENTITY__TYPE,
        short_id_col=short_id_col or _defaults.COLUMN__ENTITY__SHORT_ID,
        description_col=description_col or _defaults.COLUMN__ENTITY__DESCRIPTION,
        community_col=community_col or _defaults.COLUMN__ENTITY__COMMUNITY,
        rank_col=rank_col or _defaults.COLUMN__ENTITY__RANK,
        name_embedding_col=name_embedding_col or _defaults.COLUMN__ENTITY__NAME_EMBEDDING,
        description_embedding_col=description_embedding_col or _defaults.COLUMN__ENTITY__DESCRIPTION_EMBEDDING,
        graph_embedding_col=graph_embedding_col or _defaults.COLUMN__ENTITY__GRAPH_EMBEDDING,
        text_unit_ids_col=text_unit_ids_col or _defaults.COLUMN__ENTITY__TEXT_UNIT_IDS,
        document_ids_col=document_ids_col or _defaults.COLUMN__ENTITY__DOCUMENT_IDS,
        attributes_cols=attributes_cols or _defaults.COLUMN__ENTITY__ATTRIBUTES,
    )


def get_community_reports(
    community_reports: pd.DataFrame,
    nodes: pd.DataFrame,
    community_level: int,
    *,
    id_col: typing.Optional[str] = None,
    short_id_col: typing.Optional[str] = None,
    summary_embedding_col: typing.Optional[str] = None,
    content_embedding_col: typing.Optional[str] = None,
) -> typing.List[_model.CommunityReport]:
    """
    Fetch and process community report data based on the community level.

    Args:
        community_reports: DataFrame containing community report data.
        nodes: DataFrame containing the graph's node data.
        community_level: The maximum community level for filtering reports.
        id_col: Column name for the community report ID.
        short_id_col: Column name for the community report's short ID.
        summary_embedding_col: Column name for the summary embeddings.
        content_embedding_col: Column name for the content embeddings.

    Returns:
        A list of processed CommunityReport objects.
    """
    # Filter community reports by community level
    nodes_ = nodes.copy()
    nodes_ = nodes_[nodes_.level <= community_level]

    # Convert data types and fill missing values
    nodes_['community'] = nodes_['community'].fillna(-1).astype(int)

    # Group by title and aggregate community
    nodes_ = nodes_.groupby(['title']).agg({'community': 'max'}).reset_index()

    # Convert community to string and drop duplicates
    nodes__ = nodes_['community'].astype(str).drop_duplicates()

    community_reports_ = community_reports.copy()

    # Filter community reports by community level
    community_reports_ = community_reports_[community_reports_.level <= community_level]

    # Merge community reports and nodes
    community_reports_ = community_reports_.merge(nodes__, on='community', how='inner')

    return _dfs.read_community_reports(
        community_reports_,
        id_col=id_col or _defaults.COLUMN__COMMUNITY_REPORT__ID,
        short_id_col=short_id_col or _defaults.COLUMN__COMMUNITY_REPORT__SHORT_ID,
        summary_embedding_col=summary_embedding_col or _defaults.COLUMN__COMMUNITY_REPORT__SUMMARY_EMBEDDING,
        content_embedding_col=content_embedding_col or _defaults.COLUMN__COMMUNITY_REPORT__CONTENT_EMBEDDING,
    )


def get_relationships(
    relationships: pd.DataFrame,
    *,
    short_id_col: typing.Optional[str] = None,
    description_embedding_col: typing.Optional[str] = None,
    document_ids_col: typing.Optional[str] = None,
    attributes_cols: typing.Optional[typing.List[str]] = None,
) -> typing.List[_model.Relationship]:
    """
    Fetch and process relationship data from a DataFrame.

    Args:
        relationships: DataFrame containing relationship data.
        short_id_col: Column name for the relationship's short ID.
        description_embedding_col:
            Column name for the relationship description embeddings.
        document_ids_col:
            Column name for the document IDs associated with the relationship.
        attributes_cols: List of column names for the relationship's attributes.

    Returns:
        A list of processed Relationship objects.
    """
    return _dfs.read_relationships(
        relationships.copy(),
        short_id_col=short_id_col or _defaults.COLUMN__RELATIONSHIP__SHORT_ID,
        description_embedding_col=description_embedding_col or _defaults.COLUMN__RELATIONSHIP__DESCRIPTION_EMBEDDING,
        document_ids_col=document_ids_col or _defaults.COLUMN__RELATIONSHIP__DOCUMENT_IDS,
        attributes_cols=attributes_cols or _defaults.COLUMN__RELATIONSHIP__ATTRIBUTES,
    )


def get_covariates(
    covariates: pd.DataFrame,
    *,
    short_id_col: typing.Optional[str] = None,
    attributes_cols: typing.Optional[typing.List[str]] = None,
    text_unit_ids_col: typing.Optional[str] = None,
) -> typing.List[_model.Covariate]:
    """
    Fetch and process covariate data from a DataFrame.

    Args:
        covariates: DataFrame containing covariate data.
        short_id_col: Column name for the covariate's short ID.
        attributes_cols: List of column names for the covariate's attributes.
        text_unit_ids_col:
            Column name for the text unit IDs associated with the covariate.

    Returns:
        A list of processed Covariate objects.
    """
    covariates_ = covariates.copy()
    covariates_['id'] = covariates_['id'].astype(str)
    return _dfs.read_covariates(
        covariates_,
        short_id_col=short_id_col or _defaults.COLUMN__COVARIATE__SHORT_ID,
        attributes_cols=attributes_cols or _defaults.COLUMN__COVARIATE__ATTRIBUTES,
        text_unit_ids_col=text_unit_ids_col or _defaults.COLUMN__COVARIATE__TEXT_UNIT_IDS,
    )


def get_text_units(
    text_units: pd.DataFrame,
    *,
    short_id_col: typing.Optional[str] = None,
    covariates_col: typing.Optional[str] = None,
) -> typing.List[_model.TextUnit]:
    """
    Fetch and process text unit data from a DataFrame.

    Args:
        text_units: DataFrame containing text unit data.
        short_id_col: Column name for the text unit's short ID.
        covariates_col:
            Column name for the covariates associated with the text unit.

    Returns:
        A list of processed TextUnit objects.
    """
    return _dfs.read_text_units(
        text_units.copy(),
        short_id_col=short_id_col or _defaults.COLUMN__TEXT_UNIT__SHORT_ID,
        covariates_col=covariates_col or _defaults.COLUMN__TEXT_UNIT__COVARIATES,
    )


def get_store(entities: typing.List[_model.Entity], coll_name: str, uri: str) -> LanceDBVectorStore:
    """
    Store entity embeddings into a LanceDBVectorStore and return the store.

    Args:
        entities:
            A list of processed Entity objects whose embeddings will be stored.
        coll_name: The name of the collection in the vector store.
        uri: The URI of the LanceDB vector store.

    Returns:
        A LanceDBVectorStore object.
    """
    store = LanceDBVectorStore(
        collection_name=coll_name,
        uri=uri,
    )
    _dfs.store_entity_semantic_embeddings(entities=entities, vectorstore=store)
    return store
