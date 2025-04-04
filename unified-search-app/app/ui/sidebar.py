# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Sidebar module."""

import streamlit as st
from app_logic import dataset_name, load_dataset
from state.session_variables import SessionVariables


def reset_app():
    """Reset app to its original state."""
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()


def update_dataset(sv: SessionVariables):
    """Update dataset from the dropdown."""
    value = st.session_state[sv.dataset.key]
    st.cache_data.clear()
    if "response_lengths" not in st.session_state:
        st.session_state.response_lengths = []
    st.session_state.response_lengths = []
    load_dataset(value, sv)


def update_basic_rag(sv: SessionVariables):
    """Update basic rag state."""
    sv.include_basic_rag.value = st.session_state[sv.include_basic_rag.key]


def update_drift_search(sv: SessionVariables):
    """Update drift rag state."""
    sv.include_drift_search.value = st.session_state[sv.include_drift_search.key]


def update_local_search(sv: SessionVariables):
    """Update local rag state."""
    sv.include_local_search.value = st.session_state[sv.include_local_search.key]


def update_global_search(sv: SessionVariables):
    """Update global rag state."""
    sv.include_global_search.value = st.session_state[sv.include_global_search.key]


def create_side_bar(sv: SessionVariables):
    """Create a side bar panel.."""
    with st.sidebar:
        st.subheader("Options")

        options = [d.key for d in sv.datasets.value]

        def lookup_label(key: str):
            return dataset_name(key, sv)

        st.selectbox(
            "Dataset",
            key=sv.dataset.key,
            on_change=update_dataset,
            kwargs={"sv": sv},
            options=options,
            format_func=lookup_label,
        )
        st.number_input(
            "Number of suggested questions",
            key=sv.suggested_questions.key,
            min_value=1,
            max_value=100,
            step=1,
        )
        st.subheader("Search options:")
        st.toggle(
            "Include basic RAG",
            key=sv.include_basic_rag.key,
            on_change=update_basic_rag,
            kwargs={"sv": sv},
        )
        st.toggle(
            "Include local search",
            key=sv.include_local_search.key,
            on_change=update_local_search,
            kwargs={"sv": sv},
        )
        st.toggle(
            "Include global search",
            key=sv.include_global_search.key,
            on_change=update_global_search,
            kwargs={"sv": sv},
        )
        st.toggle(
            "Include drift search",
            key=sv.include_drift_search.key,
            on_change=update_drift_search,
            kwargs={"sv": sv},
        )
