# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""A package containing all built-in workflow definitions."""

from graphrag.index.workflows.factory import PipelineFactory

from .create_base_text_units import (
    run_workflow as run_create_base_text_units,
)
from .create_communities import (
    run_workflow as run_create_communities,
)
from .create_community_reports import (
    run_workflow as run_create_community_reports,
)
from .create_community_reports_text import (
    run_workflow as run_create_community_reports_text,
)
from .create_final_documents import (
    run_workflow as run_create_final_documents,
)
from .create_final_text_units import (
    run_workflow as run_create_final_text_units,
)
from .extract_covariates import (
    run_workflow as run_extract_covariates,
)
from .extract_graph import (
    run_workflow as run_extract_graph,
)
from .extract_graph_nlp import (
    run_workflow as run_extract_graph_nlp,
)
from .finalize_graph import (
    run_workflow as run_finalize_graph,
)
from .generate_text_embeddings import (
    run_workflow as run_generate_text_embeddings,
)
from .prune_graph import (
    run_workflow as run_prune_graph,
)
from .update_clean_state import (
    run_workflow as run_update_clean_state,
)
from .update_communities import (
    run_workflow as run_update_communities,
)
from .update_community_reports import (
    run_workflow as run_update_community_reports,
)
from .update_covariates import (
    run_workflow as run_update_covariates,
)
from .update_entities_relationships import (
    run_workflow as run_update_entities_relationships,
)
from .update_final_documents import (
    run_workflow as run_update_final_documents,
)
from .update_text_embeddings import (
    run_workflow as run_update_text_embeddings,
)
from .update_text_units import (
    run_workflow as run_update_text_units,
)

# register all of our built-in workflows at once
PipelineFactory.register_all({
    "create_base_text_units": run_create_base_text_units,
    "create_communities": run_create_communities,
    "create_community_reports_text": run_create_community_reports_text,
    "create_community_reports": run_create_community_reports,
    "extract_covariates": run_extract_covariates,
    "create_final_documents": run_create_final_documents,
    "create_final_text_units": run_create_final_text_units,
    "extract_graph_nlp": run_extract_graph_nlp,
    "extract_graph": run_extract_graph,
    "finalize_graph": run_finalize_graph,
    "generate_text_embeddings": run_generate_text_embeddings,
    "prune_graph": run_prune_graph,
    "update_final_documents": run_update_final_documents,
    "update_text_embeddings": run_update_text_embeddings,
    "update_community_reports": run_update_community_reports,
    "update_entities_relationships": run_update_entities_relationships,
    "update_communities": run_update_communities,
    "update_covariates": run_update_covariates,
    "update_text_units": run_update_text_units,
    "update_clean_state": run_update_clean_state,
})
