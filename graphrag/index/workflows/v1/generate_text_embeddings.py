# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

import logging

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

log = logging.getLogger(__name__)

workflow_name = "generate_text_embeddings"

input = {
    "source": "workflow:create_final_documents",
    "relationships": "workflow:create_final_relationships",
    "text_units": "workflow:create_final_text_units",
    "entities": "workflow:create_final_entities",
    "community_reports": "workflow:create_final_community_reports",
}


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final embeddings files.

    ## Dependencies
    * `workflow:create_final_documents`
    * `workflow:create_final_relationships`
    * `workflow:create_final_text_units`
    * `workflow:create_final_entities`
    * `workflow:create_final_community_reports`
    """
    text_embed = config.get("text_embed", {})
    embedded_fields = config.get("embedded_fields", {})
    snapshot_embeddings = config.get("snapshot_embeddings", False)
    return [
        {
            "verb": "generate_text_embeddings",
            "args": {
                "text_embed": text_embed,
                "embedded_fields": embedded_fields,
                "snapshot_embeddings_enabled": snapshot_embeddings,
            },
            "input": input,
        },
    ]
