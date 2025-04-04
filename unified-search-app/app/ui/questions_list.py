# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Question list module."""

import streamlit as st
from state.session_variables import SessionVariables


def create_questions_list_ui(sv: SessionVariables):
    """Return question list UI component."""
    selection = st.dataframe(
        sv.generated_questions.value,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        column_config={"value": "question"},
        on_select="rerun",
    )
    rows = selection.selection.rows
    if len(rows) > 0:
        question_index = selection.selection.rows[0]
        sv.selected_question.value = sv.generated_questions.value[question_index]
