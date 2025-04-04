# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Report details module."""

import json

import pandas as pd
import streamlit as st
from state.session_variables import SessionVariables
from ui.search import (
    display_graph_citations,
    format_response_hyperlinks,
    get_ids_per_key,
)


def create_report_details_ui(sv: SessionVariables):
    """Return report details UI component."""
    if sv.selected_report.value is not None and sv.selected_report.value.empty is False:
        text = ""
        entity_ids = []
        relationship_ids = []
        try:
            report = json.loads(sv.selected_report.value.full_content_json)
            title = report["title"]
            summary = report["summary"]
            rating = report["rating"]
            rating_explanation = report["rating_explanation"]
            findings = report["findings"]
            text += f"#### {title}\n\n{summary}\n\n"
            text += f"**Priority: {rating}**\n\n{rating_explanation}\n\n##### Key Findings\n\n"
            if isinstance(findings, list):
                for finding in findings:
                    # extract data for citations
                    entity_ids.extend(
                        get_ids_per_key(finding["explanation"], "Entities")
                    )
                    relationship_ids.extend(
                        get_ids_per_key(finding["explanation"], "Relationships")
                    )

                    formatted_text = format_response_hyperlinks(
                        finding["explanation"], "graph"
                    )
                    text += f"\n\n**{finding['summary']}**\n\n{formatted_text}"
            elif isinstance(findings, str):
                # extract data for citations
                entity_ids.extend(get_ids_per_key(finding["explanation"], "Entities"))  # type: ignore
                relationship_ids.extend(
                    get_ids_per_key(finding["explanation"], "Relationships")  # type: ignore
                )

                formatted_text = format_response_hyperlinks(findings, "graph")
                text += f"\n\n{formatted_text}"

        except json.JSONDecodeError:
            st.write("Error parsing report.")
            st.write(sv.selected_report.value.full_content_json)
        text_replacement = (
            text.replace("Entity_Relationships", "Relationships")
            .replace("Entity_Claims", "Claims")
            .replace("Entity_Details", "Entities")
        )
        st.markdown(f"{text_replacement}", unsafe_allow_html=True)

        # extract entities
        selected_entities = []
        for _index, row in sv.entities.value.iterrows():
            if str(row["human_readable_id"]) in entity_ids:
                selected_entities.append({
                    "id": str(row["human_readable_id"]),
                    "title": row["title"],
                    "description": row["description"],
                })

        sorted_entities = sorted(selected_entities, key=lambda x: int(x["id"]))

        # extract relationships
        selected_relationships = []
        for _index, row in sv.relationships.value.iterrows():
            if str(row["human_readable_id"]) in relationship_ids:
                selected_relationships.append({
                    "id": str(row["human_readable_id"]),
                    "source": row["source"],
                    "target": row["target"],
                    "description": row["description"],
                })

        sorted_relationships = sorted(
            selected_relationships, key=lambda x: int(x["id"])
        )

        display_graph_citations(
            pd.DataFrame(sorted_entities), pd.DataFrame(sorted_relationships), "graph"
        )
    else:
        st.write("No report selected")
