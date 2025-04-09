# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Query variable module."""

from typing import Any

import streamlit as st


class QueryVariable:
    """
    Manage reading and writing variables from the URL query string.

    We handle translation between string values and bools, accounting for always-lowercase URLs to avoid case issues.
    Note that all variables are managed via session state to account for widgets that auto-read.
    We just push them up to the query to keep it updated.
    """

    def __init__(self, key: str, default: Any | None):
        """Init method definition."""
        self._key = key
        val = st.query_params[key].lower() if key in st.query_params else default
        if val == "true":
            val = True
        elif val == "false":
            val = False
        if key not in st.session_state:
            st.session_state[key] = val

    @property
    def key(self) -> str:
        """Key property definition."""
        return self._key

    @property
    def value(self) -> Any:
        """Value property definition."""
        return st.session_state[self._key]

    @value.setter
    def value(self, value: Any) -> None:
        """Value setter definition."""
        st.session_state[self._key] = value
        st.query_params[self._key] = f"{value}".lower()
