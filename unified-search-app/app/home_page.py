# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Home Page module."""

import asyncio

import streamlit as st
from app_logic import dataset_name, initialize, run_all_searches, run_generate_questions
from rag.typing import SearchType
from st_tabs import TabBar
from state.session_variables import SessionVariables
from ui.full_graph import create_full_graph_ui
from ui.questions_list import create_questions_list_ui
from ui.report_details import create_report_details_ui
from ui.report_list import create_report_list_ui
from ui.search import display_citations, format_suggested_questions, init_search_ui
from ui.sidebar import create_side_bar


async def main():
    """Return main streamlit component to render the app."""
    sv = initialize()

    create_side_bar(sv)

    st.markdown(
        "#### GraphRAG: A Novel Knowledge Graph-based Approach to Retrieval Augmented Generation (RAG)"
    )
    st.markdown("##### Dataset selected: " + dataset_name(sv.dataset.value, sv))
    st.markdown(sv.dataset_config.value.description)

    def on_click_reset(sv: SessionVariables):
        sv.generated_questions.value = []
        sv.selected_question.value = ""
        sv.show_text_input.value = True

    def on_change(sv: SessionVariables):
        sv.question.value = st.session_state[question_input]

    question_input = "question_input"

    generate_questions = st.button("Suggest some questions")

    question = ""

    if len(sv.question.value.strip()) > 0:
        question = sv.question.value

    if generate_questions:
        with st.spinner("Generating suggested questions..."):
            try:
                result = await run_generate_questions(
                    query=f"Generate numbered list only with the top {sv.suggested_questions.value} most important questions of this dataset (numbered list only without titles or anything extra)",
                    sv=sv,
                )
                for result_item in result:
                    questions = format_suggested_questions(result_item.response)
                    sv.generated_questions.value = questions
                    sv.show_text_input.value = False
            except Exception as e:  # noqa: BLE001
                print(f"Search exception: {e}")  # noqa T201
                st.write(e)

    if sv.show_text_input.value is True:
        st.text_input(
            "Ask a question to compare the results",
            key=question_input,
            on_change=on_change,
            value=question,
            kwargs={"sv": sv},
        )

    if len(sv.generated_questions.value) != 0:
        create_questions_list_ui(sv)

    if sv.show_text_input.value is False:
        st.button(label="Reset", on_click=on_click_reset, kwargs={"sv": sv})

    tab_id = TabBar(
        tabs=["Search", "Graph Explorer"],
        color="#fc9e9e",
        activeColor="#ff4b4b",
        default=0,
    )

    if tab_id == 0:
        if len(sv.question.value.strip()) > 0:
            question = sv.question.value

        if sv.selected_question.value != "":
            question = sv.selected_question.value
            sv.question.value = question

        if question:
            st.write(f"##### Answering the question: *{question}*")

        ss_basic = None
        ss_local = None
        ss_global = None
        ss_drift = None

        ss_basic_citations = None
        ss_local_citations = None
        ss_global_citations = None
        ss_drift_citations = None

        count = sum([
            sv.include_basic_rag.value,
            sv.include_local_search.value,
            sv.include_global_search.value,
            sv.include_drift_search.value,
        ])

        if count > 0:
            columns = st.columns(count)
            index = 0
            if sv.include_basic_rag.value:
                ss_basic = columns[index]
                index += 1
            if sv.include_local_search.value:
                ss_local = columns[index]
                index += 1
            if sv.include_global_search.value:
                ss_global = columns[index]
                index += 1
            if sv.include_drift_search.value:
                ss_drift = columns[index]

        else:
            st.write("Please select at least one search option from the sidebar.")

        with st.container():
            if ss_basic:
                with ss_basic:
                    init_search_ui(
                        container=ss_basic,
                        search_type=SearchType.Basic,
                        title="##### GraphRAG: Basic RAG",
                        caption="###### Answer context: Fixed number of text chunks of raw documents",
                    )

            if ss_local:
                with ss_local:
                    init_search_ui(
                        container=ss_local,
                        search_type=SearchType.Local,
                        title="##### GraphRAG: Local Search",
                        caption="###### Answer context: Graph index query results with relevant document text chunks",
                    )

            if ss_global:
                with ss_global:
                    init_search_ui(
                        container=ss_global,
                        search_type=SearchType.Global,
                        title="##### GraphRAG: Global Search",
                        caption="###### Answer context: AI-generated network reports covering all input documents",
                    )

            if ss_drift:
                with ss_drift:
                    init_search_ui(
                        container=ss_drift,
                        search_type=SearchType.Drift,
                        title="##### GraphRAG: Drift Search",
                        caption="###### Answer context: Includes community information",
                    )

        count = sum([
            sv.include_basic_rag.value,
            sv.include_local_search.value,
            sv.include_global_search.value,
            sv.include_drift_search.value,
        ])

        if count > 0:
            columns = st.columns(count)
            index = 0
            if sv.include_basic_rag.value:
                ss_basic_citations = columns[index]
                index += 1
            if sv.include_local_search.value:
                ss_local_citations = columns[index]
                index += 1
            if sv.include_global_search.value:
                ss_global_citations = columns[index]
                index += 1
            if sv.include_drift_search.value:
                ss_drift_citations = columns[index]

        with st.container():
            if ss_basic_citations:
                with ss_basic_citations:
                    st.empty()
            if ss_local_citations:
                with ss_local_citations:
                    st.empty()
            if ss_global_citations:
                with ss_global_citations:
                    st.empty()
            if ss_drift_citations:
                with ss_drift_citations:
                    st.empty()

        if question != "" and question != sv.question_in_progress.value:
            sv.question_in_progress.value = question
            try:
                await run_all_searches(query=question, sv=sv)

                if "response_lengths" not in st.session_state:
                    st.session_state.response_lengths = []

                for result in st.session_state.response_lengths:
                    if result["search"] == SearchType.Basic.value.lower():
                        display_citations(
                            container=ss_basic_citations,
                            result=result["result"],
                        )
                    if result["search"] == SearchType.Local.value.lower():
                        display_citations(
                            container=ss_local_citations,
                            result=result["result"],
                        )
                    if result["search"] == SearchType.Global.value.lower():
                        display_citations(
                            container=ss_global_citations,
                            result=result["result"],
                        )
                    elif result["search"] == SearchType.Drift.value.lower():
                        display_citations(
                            container=ss_drift_citations,
                            result=result["result"],
                        )
            except Exception as e:  # noqa: BLE001
                print(f"Search exception: {e}")  # noqa T201
                st.write(e)

    if tab_id == 1:
        report_list, graph, report_content = st.columns([0.20, 0.55, 0.25])

        with report_list:
            st.markdown("##### Community Reports")
            create_report_list_ui(sv)

        with graph:
            title, dropdown = st.columns([0.80, 0.20])
            title.markdown("##### Entity Graph (All entities)")
            dropdown.selectbox(
                "Community level", options=[0, 1], key=sv.graph_community_level.key
            )
            create_full_graph_ui(sv)

        with report_content:
            st.markdown("##### Selected Report")
            create_report_details_ui(sv)


if __name__ == "__main__":
    asyncio.run(main())
