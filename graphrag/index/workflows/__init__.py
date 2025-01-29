# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""A package containing all built-in workflow definitions."""

from graphrag.index.typing import WorkflowFunction

from .compute_communities import (
    run_workflow as run_compute_communities,
)
from .compute_communities import (
    workflow_name as compute_communities,
)
from .create_base_text_units import (
    run_workflow as run_create_base_text_units,
)
from .create_base_text_units import (
    workflow_name as create_base_text_units,
)
from .create_final_communities import (
    run_workflow as run_create_final_communities,
)
from .create_final_communities import (
    workflow_name as create_final_communities,
)
from .create_final_community_reports import (
    run_workflow as run_create_final_community_reports,
)
from .create_final_community_reports import (
    workflow_name as create_final_community_reports,
)
from .create_final_community_reports_text import (
    run_workflow as run_create_final_community_reports_text,
)
from .create_final_community_reports_text import (
    workflow_name as create_final_community_reports_text,
)
from .create_final_covariates import (
    run_workflow as run_create_final_covariates,
)
from .create_final_covariates import (
    workflow_name as create_final_covariates,
)
from .create_final_documents import (
    run_workflow as run_create_final_documents,
)
from .create_final_documents import (
    workflow_name as create_final_documents,
)
from .create_final_entities import (
    run_workflow as run_create_final_entities,
)
from .create_final_entities import (
    workflow_name as create_final_entities,
)
from .create_final_nodes import (
    run_workflow as run_create_final_nodes,
)
from .create_final_nodes import (
    workflow_name as create_final_nodes,
)
from .create_final_relationships import (
    run_workflow as run_create_final_relationships,
)
from .create_final_relationships import (
    workflow_name as create_final_relationships,
)
from .create_final_text_units import (
    run_workflow as run_create_final_text_units,
)
from .create_final_text_units import (
    workflow_name as create_final_text_units,
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
    compute_communities: run_compute_communities,
    create_base_text_units: run_create_base_text_units,
    create_final_communities: run_create_final_communities,
    create_final_community_reports_text: run_create_final_community_reports_text,
    create_final_community_reports: run_create_final_community_reports,
    create_final_covariates: run_create_final_covariates,
    create_final_documents: run_create_final_documents,
    create_final_entities: run_create_final_entities,
    create_final_nodes: run_create_final_nodes,
    create_final_relationships: run_create_final_relationships,
    create_final_text_units: run_create_final_text_units,
    extract_graph_nlp: run_extract_graph_nlp,
    extract_graph: run_extract_graph,
    generate_text_embeddings: run_generate_text_embeddings,
}
"""This is a dictionary of all build-in workflows. To be replace with an injectable provider!"""
