# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_relationships"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final relationships table.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    * `workflow:create_final_nodes`
    """
    base_text_embed = config.get("text_embed", {})
    relationship_description_embed_config = config.get(
        "relationship_description_embed", base_text_embed
    )
    skip_description_embedding = config.get("skip_description_embedding", False)
    return [
        {
            "verb": "create_final_relationships",
            "args": {
                "skip_embedding": skip_description_embedding,
                "text_embed": relationship_description_embed_config,
            },
            "input": {
                "source": "workflow:create_base_entity_graph",
                "nodes": "workflow:create_final_nodes",
            },
        },
    ]
