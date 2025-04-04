# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Data prep module."""

import logging

import data_config as config
import pandas as pd
import streamlit as st
from knowledge_loader.data_sources.typing import Datasource

"""
Contains functions to load and prep graph-indexed data from parquet files into dataframes.
These output dataframes will then be used to create knowledge model's objects to be used as inputs for the graphrag-orchestration functions
"""
logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@st.cache_data(ttl=config.default_ttl)
def get_entity_data(dataset: str, _datasource: Datasource) -> pd.DataFrame:
    """Return a dataframe with entity data from the indexed-data."""
    entity_details_df = _datasource.read(config.entity_table)

    print(f"Entity records: {len(entity_details_df)}")  # noqa T201
    print(f"Dataset: {dataset}")  # noqa T201
    return entity_details_df


@st.cache_data(ttl=config.default_ttl)
def get_relationship_data(dataset: str, _datasource: Datasource) -> pd.DataFrame:
    """Return a dataframe with entity-entity relationship data from the indexed-data."""
    relationship_df = _datasource.read(config.relationship_table)
    print(f"Relationship records: {len(relationship_df)}")  # noqa T201
    print(f"Dataset: {dataset}")  # noqa T201
    return relationship_df


@st.cache_data(ttl=config.default_ttl)
def get_covariate_data(dataset: str, _datasource: Datasource) -> pd.DataFrame:
    """Return a dataframe with covariate data from the indexed-data."""
    covariate_df = _datasource.read(config.covariate_table)
    print(f"Covariate records: {len(covariate_df)}")  # noqa T201
    print(f"Dataset: {dataset}")  # noqa T201
    return covariate_df


@st.cache_data(ttl=config.default_ttl)
def get_text_unit_data(dataset: str, _datasource: Datasource) -> pd.DataFrame:
    """Return a dataframe with text units (i.e. chunks of text from the raw documents) from the indexed-data."""
    text_unit_df = _datasource.read(config.text_unit_table)
    print(f"Text unit records: {len(text_unit_df)}")  # noqa T201
    print(f"Dataset: {dataset}")  # noqa T201
    return text_unit_df


@st.cache_data(ttl=config.default_ttl)
def get_community_report_data(
    _datasource: Datasource,
) -> pd.DataFrame:
    """Return a dataframe with community report data from the indexed-data."""
    report_df = _datasource.read(config.community_report_table)
    print(f"Report records: {len(report_df)}")  # noqa T201

    return report_df


@st.cache_data(ttl=config.default_ttl)
def get_communities_data(
    _datasource: Datasource,
) -> pd.DataFrame:
    """Return a dataframe with communities data from the indexed-data."""
    return _datasource.read(config.communities_table)
