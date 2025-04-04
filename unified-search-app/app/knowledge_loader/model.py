# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Model module."""

from dataclasses import dataclass

import pandas as pd
import streamlit as st
from data_config import (
    default_ttl,
)
from knowledge_loader.data_prep import (
    get_communities_data,
    get_community_report_data,
    get_covariate_data,
    get_entity_data,
    get_relationship_data,
    get_text_unit_data,
)
from knowledge_loader.data_sources.typing import Datasource

"""
Contain functions to load graph-indexed data into collections of knowledge model objects.
These collections will be used as inputs for the graphrag-orchestration functions
"""


@st.cache_data(ttl=default_ttl)
def load_entities(
    dataset: str,
    _datasource: Datasource,
) -> pd.DataFrame:
    """Return a list of Entity objects."""
    return get_entity_data(dataset, _datasource)


@st.cache_data(ttl=default_ttl)
def load_entity_relationships(
    dataset: str,
    _datasource: Datasource,
) -> pd.DataFrame:
    """Return lists of Entity and Relationship objects."""
    return get_relationship_data(dataset, _datasource)


@st.cache_data(ttl=default_ttl)
def load_covariates(dataset: str, _datasource: Datasource) -> pd.DataFrame:
    """Return a dictionary of Covariate objects, with the key being the covariate type."""
    return get_covariate_data(dataset, _datasource)


@st.cache_data(ttl=default_ttl)
def load_community_reports(
    _datasource: Datasource,
) -> pd.DataFrame:
    """Return a list of CommunityReport objects."""
    return get_community_report_data(_datasource)


@st.cache_data(ttl=default_ttl)
def load_communities(
    _datasource: Datasource,
) -> pd.DataFrame:
    """Return a list of Communities objects."""
    return get_communities_data(_datasource)


@st.cache_data(ttl=default_ttl)
def load_text_units(dataset: str, _datasource: Datasource) -> pd.DataFrame:
    """Return a list of TextUnit objects."""
    return get_text_unit_data(dataset, _datasource)


@dataclass
class KnowledgeModel:
    """KnowledgeModel class definition."""

    entities: pd.DataFrame
    relationships: pd.DataFrame
    community_reports: pd.DataFrame
    communities: pd.DataFrame
    text_units: pd.DataFrame
    covariates: pd.DataFrame | None = None


def load_model(
    dataset: str,
    datasource: Datasource,
):
    """
    Load all relevant graph-indexed data into collections of knowledge model objects and store the model collections in the session variables.

    This is a one-time data retrieval and preparation per session.
    """
    entities = load_entities(dataset, datasource)
    relationships = load_entity_relationships(dataset, datasource)
    covariates = load_covariates(dataset, datasource)
    community_reports = load_community_reports(datasource)
    communities = load_communities(datasource)
    text_units = load_text_units(dataset, datasource)

    return KnowledgeModel(
        entities=entities,
        relationships=relationships,
        community_reports=community_reports,
        communities=communities,
        text_units=text_units,
        covariates=(None if covariates.empty else covariates),
    )
