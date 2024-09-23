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
            "id": "pre_embedding",
            "verb": "create_final_relationships_pre_embedding",
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "id": "description_embedding",
            "verb": "text_embed",
            "enabled": not skip_description_embedding,
            "args": {
                "embedding_name": "relationship_description",
                "column": "description",
                "to": "description_embedding",
                **relationship_description_embed_config,
            },
        },
        {
            "verb": "create_final_relationships_post_embedding",
            "input": {
                "source": "pre_embedding"
                if skip_description_embedding
                else "description_embedding",
                "nodes": "workflow:create_final_nodes",
            },
        },
    ]
