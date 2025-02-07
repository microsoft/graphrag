# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""A package containing all built-in workflow definitions."""

from graphrag.index.typing import WorkflowFunction

from .create_base_text_units import (
    run_workflow as run_create_base_text_units,
)
from .create_base_text_units import (
    workflow_name as create_base_text_units,
)
from .create_communities import (
    run_workflow as run_create_communities,
)
from .create_communities import (
    workflow_name as create_communities,
)
from .create_community_reports import (
    run_workflow as run_create_community_reports,
)
from .create_community_reports import (
    workflow_name as create_community_reports,
)
from .create_community_reports_text import (
    run_workflow as run_create_community_reports_text,
)
from .create_community_reports_text import (
    workflow_name as create_community_reports_text,
)
from .create_final_documents import (
    run_workflow as run_create_final_documents,
)
from .create_final_documents import (
    workflow_name as create_final_documents,
)
from .create_final_text_units import (
    run_workflow as run_create_final_text_units,
)
from .create_final_text_units import (
    workflow_name as create_final_text_units,
)
from .extract_covariates import (
    run_workflow as run_extract_covariates,
)
from .extract_covariates import (
    workflow_name as extract_covariates,
)
from .extract_graph import (
    run_workflow as run_extract_graph,
)
from .extract_graph import (
    workflow_name as extract_graph,
)
from .extract_graph_nlp import (
    run_workflow as run_extract_graph_nlp,
)
from .extract_graph_nlp import (
    workflow_name as extract_graph_nlp,
)
from .generate_text_embeddings import (
    run_workflow as run_generate_text_embeddings,
)
from .generate_text_embeddings import (
    workflow_name as generate_text_embeddings,
)

all_workflows: dict[
    str,
    WorkflowFunction,
] = {
    create_base_text_units: run_create_base_text_units,
    create_communities: run_create_communities,
    create_community_reports_text: run_create_community_reports_text,
    create_community_reports: run_create_community_reports,
    extract_covariates: run_extract_covariates,
    create_final_documents: run_create_final_documents,
    create_final_text_units: run_create_final_text_units,
    extract_graph_nlp: run_extract_graph_nlp,
    extract_graph: run_extract_graph,
    generate_text_embeddings: run_generate_text_embeddings,
}
"""This is a dictionary of all build-in workflows. To be replace with an injectable provider!"""
