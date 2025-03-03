# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Encapsulates pipeline construction and selection."""

from typing import ClassVar

from graphrag.config.enums import IndexingMethod
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.pipeline import Pipeline
from graphrag.index.typing.workflow import WorkflowFunction


class PipelineFactory:
    """A factory class for workflow pipelines."""

    workflows: ClassVar[dict[str, WorkflowFunction]] = {}

    @classmethod
    def register(cls, name: str, workflow: WorkflowFunction):
        """Register a custom workflow function."""
        cls.workflows[name] = workflow

    @classmethod
    def register_all(cls, workflows: dict[str, WorkflowFunction]):
        """Register a dict of custom workflow functions."""
        for name, workflow in workflows.items():
            cls.register(name, workflow)

    @classmethod
    def create_pipeline(
        cls, config: GraphRagConfig, method: IndexingMethod = IndexingMethod.Standard
    ) -> Pipeline:
        """Create a pipeline generator."""
        workflows = _get_workflows_list(config, method)
        return Pipeline([(name, cls.workflows[name]) for name in workflows])


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
                "finalize_graph",
                *(["extract_covariates"] if config.extract_claims.enabled else []),
                "create_communities",
                "create_final_text_units",
                "create_community_reports",
                "generate_text_embeddings",
            ]
        case IndexingMethod.Fast:
            return [
                "create_base_text_units",
                "create_final_documents",
                "extract_graph_nlp",
                "prune_graph",
                "finalize_graph",
                "create_communities",
                "create_final_text_units",
                "create_community_reports_text",
                "generate_text_embeddings",
            ]
