from typing import Any, Optional

import streamlit as st


class QueryVariable:
    """
    This class manages reading and writing variables from the URL query string.
    We handle translation between string values and bools, accounting for always-lowercase URLs to avoid case issues.
    Note that all variables are managed via session state to account for widgets that auto-read.
    We just push them up to the query to keep it updated.
    """

    def __init__(self, key: str, default: Optional[Any]):
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
        return self._key

    @property
    def value(self) -> Any:
        return st.session_state[self._key]

    @value.setter
    def value(self, value: Any) -> None:
        st.session_state[self._key] = value
        st.query_params[self._key] = f"{value}".lower()
