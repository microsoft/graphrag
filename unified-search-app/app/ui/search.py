# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Search module."""

import json
import re
from dataclasses import dataclass

import pandas as pd
import streamlit as st
from rag.typing import SearchResult, SearchType
from streamlit.delta_generator import DeltaGenerator


def init_search_ui(
    container: DeltaGenerator, search_type: SearchType, title: str, caption: str
):
    """Initialize search UI component."""
    with container:
        st.markdown(title)
        st.caption(caption)

        ui_tag = search_type.value.lower()
        st.session_state[f"{ui_tag}_response_placeholder"] = st.empty()
        st.session_state[f"{ui_tag}_context_placeholder"] = st.empty()
        st.session_state[f"{ui_tag}_container"] = container


@dataclass
class SearchStats:
    """SearchStats class definition."""

    completion_time: float
    llm_calls: int
    prompt_tokens: int


def display_search_result(
    container: DeltaGenerator, result: SearchResult, stats: SearchStats | None = None
):
    """Display search results data into the UI."""
    response_placeholder_attr = (
        result.search_type.value.lower() + "_response_placeholder"
    )

    with container:
        # display response
        response = format_response_hyperlinks(
            result.response, result.search_type.value.lower()
        )

        if stats is not None and stats.completion_time is not None:
            st.markdown(
                f"*{stats.prompt_tokens:,} tokens used, {stats.llm_calls} LLM calls, {int(stats.completion_time)} seconds elapsed.*"
            )
        st.session_state[response_placeholder_attr] = st.markdown(
            f"<div id='{result.search_type.value.lower()}-response'>{response}</div>",
            unsafe_allow_html=True,
        )


def display_citations(
    container: DeltaGenerator | None = None, result: SearchResult | None = None
):
    """Display citations into the UI."""
    if container is not None:
        with container:
            # display context used for generating the response
            if result is not None:
                context_data = result.context
                context_data = dict(sorted(context_data.items()))

                st.markdown("---")
                st.markdown("### Citations")
                for key, value in context_data.items():
                    if len(value) > 0:
                        key_type = key
                        if key == "sources":
                            st.markdown(
                                f"Relevant chunks of source documents **({len(value)})**:"
                            )
                            key_type = "sources"
                        elif key == "reports":
                            st.markdown(
                                f"Relevant AI-generated network reports **({len(value)})**:"
                            )
                        else:
                            st.markdown(
                                f"Relevant AI-extracted {key} **({len(value)})**:"
                            )
                        st.markdown(
                            render_html_table(
                                value, result.search_type.value.lower(), key_type
                            ),
                            unsafe_allow_html=True,
                        )


def format_response_hyperlinks(str_response: str, search_type: str = ""):
    """Format response to show hyperlinks inside the response UI."""
    results_with_hyperlinks = format_response_hyperlinks_by_key(
        str_response, "Entities", "Entities", search_type
    )
    results_with_hyperlinks = format_response_hyperlinks_by_key(
        results_with_hyperlinks, "Sources", "Sources", search_type
    )
    results_with_hyperlinks = format_response_hyperlinks_by_key(
        results_with_hyperlinks, "Documents", "Sources", search_type
    )
    results_with_hyperlinks = format_response_hyperlinks_by_key(
        results_with_hyperlinks, "Relationships", "Relationships", search_type
    )
    results_with_hyperlinks = format_response_hyperlinks_by_key(
        results_with_hyperlinks, "Reports", "Reports", search_type
    )

    return results_with_hyperlinks  # noqa: RET504


def format_response_hyperlinks_by_key(
    str_response: str, key: str, anchor: str, search_type: str = ""
):
    """Format response to show hyperlinks inside the response UI by key."""
    pattern = r"\(\d+(?:,\s*\d+)*(?:,\s*\+more)?\)"

    citations_list = re.findall(f"{key} {pattern}", str_response)

    results_with_hyperlinks = str_response
    if len(citations_list) > 0:
        for occurrence in citations_list:
            string_occurrence = str(occurrence)
            numbers_list = string_occurrence[
                string_occurrence.find("(") + 1 : string_occurrence.find(")")
            ].split(",")
            string_occurrence_hyperlinks = string_occurrence
            for number in numbers_list:
                if number.lower().strip() != "+more":
                    string_occurrence_hyperlinks = string_occurrence_hyperlinks.replace(
                        number,
                        f'<a href="#{search_type.lower().strip()}-{anchor.lower().strip()}-{number.strip()}">{number}</a>',
                    )

            results_with_hyperlinks = results_with_hyperlinks.replace(
                occurrence, string_occurrence_hyperlinks
            )

    return results_with_hyperlinks


def format_suggested_questions(questions: str):
    """Format suggested questions to the UI."""
    citations_pattern = r"\[.*?\]"
    substring = re.sub(citations_pattern, "", questions).strip()
    return convert_numbered_list_to_array(substring)


def convert_numbered_list_to_array(numbered_list_str):
    """Convert numbered list result into an array of elements."""
    lines = numbered_list_str.strip().split("\n")
    items = []

    for line in lines:
        match = re.match(r"^\d+\.\s*(.*)", line)
        if match:
            item = match.group(1).strip()
            items.append(item)

    return items


def get_ids_per_key(str_response: str, key: str):
    """Filter ids per key."""
    pattern = r"\(\d+(?:,\s*\d+)*(?:,\s*\+more)?\)"
    citations_list = re.findall(f"{key} {pattern}", str_response)
    numbers_list = []
    if len(citations_list) > 0:
        for occurrence in citations_list:
            string_occurrence = str(occurrence)
            numbers_list = string_occurrence[
                string_occurrence.find("(") + 1 : string_occurrence.find(")")
            ].split(",")

    return numbers_list


SHORT_WORDS = 12
LONG_WORDS = 200


# Function to generate HTML table with ids
def render_html_table(df: pd.DataFrame, search_type: str, key: str):
    """Render HTML table into the UI."""
    table_container = """
        max-width: 100%;
        overflow: hidden;
        margin: 0 auto;
    """

    table_style = """
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    """

    th_style = """
        word-wrap: break-word;
        white-space: normal;
    """

    td_style = """
        border: 1px solid #efefef;
        word-wrap: break-word;
        white-space: normal;
    """

    table_html = f'<div style="{table_container}">'
    table_html += f'<table style="{table_style}">'

    table_html += "<thead><tr>"
    for col in pd.DataFrame(df).columns:
        table_html += f'<th style="{th_style}">{col}</th>'
    table_html += "</tr></thead>"

    table_html += "<tbody>"
    for index, row in pd.DataFrame(df).iterrows():
        html_id = (
            f"{search_type.lower().strip()}-{key.lower().strip()}-{row.id.strip()}"
            if "id" in row
            else f"row-{index}"
        )
        table_html += f'<tr id="{html_id}">'
        for value in row:
            if isinstance(value, str):
                if value[0:1] == "{":
                    value_casted = json.loads(value)
                    value = value_casted["summary"]
                value_array = str(value).split(" ")
                td_value = (
                    " ".join(value_array[:SHORT_WORDS]) + "..."
                    if len(value_array) >= SHORT_WORDS
                    else value
                )
                title_value = (
                    " ".join(value_array[:LONG_WORDS]) + "..."
                    if len(value_array) >= LONG_WORDS
                    else value
                )
                title_value = (
                    title_value.replace('"', "&quot;")
                    .replace("'", "&apos;")
                    .replace("\n", " ")
                    .replace("\n\n", " ")
                    .replace("\r\n", " ")
                )
                table_html += (
                    f'<td style="{td_style}" title="{title_value}">{td_value}</td>'
                )
            else:
                table_html += f'<td style="{td_style}" title="{value}">{value}</td>'
        table_html += "</tr>"
    table_html += "</tbody></table></div>"

    return table_html


def display_graph_citations(
    entities: pd.DataFrame, relationships: pd.DataFrame, citation_type: str
):
    """Display graph citations into the UI."""
    st.markdown("---")
    st.markdown("### Citations")

    st.markdown(f"Relevant AI-extracted entities **({len(entities)})**:")
    st.markdown(
        render_html_table(entities, citation_type, "entities"),
        unsafe_allow_html=True,
    )

    st.markdown(f"Relevant AI-extracted relationships **({len(relationships)})**:")
    st.markdown(
        render_html_table(relationships, citation_type, "relationships"),
        unsafe_allow_html=True,
    )
