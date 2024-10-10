# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_entities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final entities table.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    """
    base_text_embed = config.get("text_embed", {})
    entity_name_embed_config = config.get("entity_name_embed", base_text_embed)
    entity_name_description_embed_config = config.get(
        "entity_name_description_embed", base_text_embed
    )

    skip_name_embedding = config.get("skip_name_embedding", False)
    skip_description_embedding = config.get("skip_description_embedding", False)

    return [
        {
            "verb": "create_final_entities",
            "args": {
                "name_text_embed": entity_name_embed_config
                if not skip_name_embedding
                else None,
                "description_text_embed": entity_name_description_embed_config
                if not skip_description_embedding
                else None,
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
    ]
