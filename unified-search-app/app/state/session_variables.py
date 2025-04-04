# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Session variables module."""

from data_config import (
    default_suggested_questions,
)
from state.query_variable import QueryVariable
from state.session_variable import SessionVariable


class SessionVariables:
    """Define all the session variables that will be used in the app."""

    def __init__(self):
        """Init method definition."""
        self.dataset = QueryVariable("dataset", "")
        self.datasets = SessionVariable([])
        self.dataset_config = SessionVariable()
        self.datasource = SessionVariable()
        self.graphrag_config = SessionVariable()
        self.question = QueryVariable("question", "")
        self.suggested_questions = SessionVariable(default_suggested_questions)
        self.entities = SessionVariable([])
        self.relationships = SessionVariable([])
        self.covariates = SessionVariable({})
        self.communities = SessionVariable([])
        self.community_reports = SessionVariable([])
        self.text_units = SessionVariable([])
        self.question_in_progress = SessionVariable("")
        self.include_global_search = QueryVariable("include_global_search", True)
        self.include_local_search = QueryVariable("include_local_search", True)
        self.include_drift_search = QueryVariable("include_drift_search", False)
        self.include_basic_rag = QueryVariable("include_basic_rag", False)

        self.selected_report = SessionVariable()
        self.graph_community_level = SessionVariable(0)

        self.selected_question = SessionVariable("")
        self.generated_questions = SessionVariable([])
        self.show_text_input = SessionVariable(True)
