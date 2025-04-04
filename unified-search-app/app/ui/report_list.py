# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Report list module."""

import streamlit as st
from state.session_variables import SessionVariables


def create_report_list_ui(sv: SessionVariables):
    """Return report list UI component."""
    selection = st.dataframe(
        sv.community_reports.value,
        height=1000,
        hide_index=True,
        column_order=["id", "title"],
        selection_mode="single-row",
        on_select="rerun",
    )
    rows = selection.selection.rows
    if len(rows) > 0:
        report_index = selection.selection.rows[0]
        sv.selected_report.value = sv.community_reports.value.iloc[report_index]
    else:
        sv.selected_report.value = None
