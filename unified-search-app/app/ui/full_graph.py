import altair as alt
import pandas as pd
import streamlit as st
from state.session_variables import SessionVariables


def create_full_graph_ui(sv: SessionVariables):
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
    df = communities_entities[communities_entities["level"] == level]

    graph = (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x="x",
            y="y",
            color=alt.Color(
                "community",
                scale=alt.Scale(domain=df["community"].unique(), scheme="category10"),
            ),
            size=alt.Size("degree", scale=alt.Scale(range=[50, 1000]), legend=None),
            tooltip=["id_entities", "type", "description", "community"],
        )
        .properties(height=1000)
        .configure_axis(disable=True)
    )
    st.altair_chart(graph, use_container_width=True)
    return graph
