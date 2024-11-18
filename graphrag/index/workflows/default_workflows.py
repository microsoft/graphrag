# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing default workflows definitions."""

# load and register all subflows
from graphrag.index.workflows.v1.subflows import *  # noqa

from graphrag.index.workflows.typing import WorkflowDefinitions
from graphrag.index.workflows.v1.create_base_entity_graph import (
    build_steps as build_create_base_entity_graph_steps,
)
from graphrag.index.workflows.v1.create_base_entity_graph import (
    workflow_name as create_base_entity_graph,
)
from graphrag.index.workflows.v1.create_base_text_units import (
    build_steps as build_create_base_text_units_steps,
)
from graphrag.index.workflows.v1.create_base_text_units import (
    workflow_name as create_base_text_units,
)
from graphrag.index.workflows.v1.create_final_communities import (
    build_steps as build_create_final_communities_steps,
)
from graphrag.index.workflows.v1.create_final_communities import (
    workflow_name as create_final_communities,
)
from graphrag.index.workflows.v1.create_final_community_reports import (
    build_steps as build_create_final_community_reports_steps,
)
from graphrag.index.workflows.v1.create_final_community_reports import (
    workflow_name as create_final_community_reports,
)
from graphrag.index.workflows.v1.create_final_covariates import (
    build_steps as build_create_final_covariates_steps,
)
from graphrag.index.workflows.v1.create_final_covariates import (
    workflow_name as create_final_covariates,
)
from graphrag.index.workflows.v1.create_final_documents import (
    build_steps as build_create_final_documents_steps,
)
from graphrag.index.workflows.v1.create_final_documents import (
    workflow_name as create_final_documents,
)
from graphrag.index.workflows.v1.create_final_entities import (
    build_steps as build_create_final_entities_steps,
)
from graphrag.index.workflows.v1.create_final_entities import (
    workflow_name as create_final_entities,
)
from graphrag.index.workflows.v1.create_final_nodes import (
    build_steps as build_create_final_nodes_steps,
)
from graphrag.index.workflows.v1.create_final_nodes import (
    workflow_name as create_final_nodes,
)
from graphrag.index.workflows.v1.create_final_relationships import (
    build_steps as build_create_final_relationships_steps,
)
from graphrag.index.workflows.v1.create_final_relationships import (
    workflow_name as create_final_relationships,
)
from graphrag.index.workflows.v1.create_final_text_units import (
    build_steps as build_create_final_text_units,
)
from graphrag.index.workflows.v1.create_final_text_units import (
    workflow_name as create_final_text_units,
)
from graphrag.index.workflows.v1.generate_text_embeddings import (
    build_steps as build_generate_text_embeddings_steps,
)

from graphrag.index.workflows.v1.generate_text_embeddings import (
    workflow_name as generate_text_embeddings,
)

default_workflows: WorkflowDefinitions = {
    create_base_entity_graph: build_create_base_entity_graph_steps,
    create_base_text_units: build_create_base_text_units_steps,
    create_final_text_units: build_create_final_text_units,
    create_final_community_reports: build_create_final_community_reports_steps,
    create_final_nodes: build_create_final_nodes_steps,
    create_final_relationships: build_create_final_relationships_steps,
    create_final_documents: build_create_final_documents_steps,
    create_final_covariates: build_create_final_covariates_steps,
    create_final_entities: build_create_final_entities_steps,
    create_final_communities: build_create_final_communities_steps,
    generate_text_embeddings: build_generate_text_embeddings_steps,
}
