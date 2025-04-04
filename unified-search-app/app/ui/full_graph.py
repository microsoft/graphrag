# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Full graph module."""

import altair as alt
import pandas as pd
import streamlit as st
from state.session_variables import SessionVariables


def create_full_graph_ui(sv: SessionVariables):
    """Return graph UI object."""
    entities = sv.entities.value.copy()
    communities = sv.communities.value.copy()

    if not communities.empty and not entities.empty:
        communities_entities = (
            communities.explode("entity_ids")
            .merge(
                entities,
                left_on="entity_ids",
                right_on="id",
                suffixes=("_entities", "_communities"),
            )
            .dropna(subset=["x", "y"])
        )
    else:
        communities_entities = pd.DataFrame()

    level = sv.graph_community_level.value
    communities_entities_filtered = communities_entities[
        communities_entities["level"] == level
    ]

    graph = (
        alt.Chart(communities_entities_filtered)
        .mark_circle()
        .encode(
            x="x",
            y="y",
            color=alt.Color(
                "community",
                scale=alt.Scale(
                    domain=communities_entities_filtered["community"].unique(),
                    scheme="category10",
                ),
            ),
            size=alt.Size("degree", scale=alt.Scale(range=[50, 1000]), legend=None),
            tooltip=["id_entities", "type", "description", "community"],
        )
        .properties(height=1000)
        .configure_axis(disable=True)
    )
    st.altair_chart(graph, use_container_width=True)
    return graph
