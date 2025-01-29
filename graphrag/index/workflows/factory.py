# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Encapsulates pipeline construction and selection."""

from graphrag.config.enums import IndexingMethod
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing import Pipeline
from graphrag.index.workflows import all_workflows


def create_pipeline(
    config: GraphRagConfig, method: IndexingMethod = IndexingMethod.Standard
) -> Pipeline:
    """Create a pipeline generator."""
    workflows = _get_workflows_list(config, method)
    for name in workflows:
        yield name, all_workflows[name]


def _get_workflows_list(
    config: GraphRagConfig, method: IndexingMethod = IndexingMethod.Standard
) -> list[str]:
    """Return a list of workflows for the indexing pipeline."""
    if config.workflows:
        return config.workflows
    match method:
        case IndexingMethod.Standard:
            return [
                "create_base_text_units",
                "create_final_documents",
                "extract_graph",
                "create_final_relationships",
                "create_communities",
                *(["extract_covariates"] if config.claim_extraction.enabled else []),
                "create_final_text_units",
                "create_community_reports",
                "generate_text_embeddings",
            ]
        case IndexingMethod.Fast:
            return [
                "create_base_text_units",
                "create_final_documents",
                "extract_graph_nlp",
                "create_final_relationships",
                "create_communities",
                "create_final_text_units",
                "create_community_reports_text",
            ]
