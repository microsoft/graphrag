# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

import logging

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

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
    base_text_embed = config.get("text_embed", {})

    community_report_full_content_embed_config = config.get(
        "community_report_full_content_embed", base_text_embed
    )
    community_report_summary_embed_config = config.get(
        "community_report_summary_embed", base_text_embed
    )
    community_report_title_embed_config = config.get(
        "community_report_title_embed", base_text_embed
    )
    document_raw_content_embed_config = config.get(
        "document_raw_content_embed", base_text_embed
    )
    entity_name_embed_config = config.get("entity_name_embed", base_text_embed)
    entity_name_description_embed_config = config.get(
        "entity_name_description_embed", base_text_embed
    )
    relationship_description_embed_config = config.get(
        "relationship_description_embed", base_text_embed
    )
    text_unit_text_embed_config = config.get("text_unit_text_embed", base_text_embed)

    embedded_fields = config.get("embedded_fields", {})

    return [
        {
            "verb": "generate_text_embeddings",
            "args": {
                "embeddings_snapshot": config.get("snapshot_embeddings", False),
                "full_content_text_embed": community_report_full_content_embed_config,
                "summary_text_embed": community_report_summary_embed_config,
                "title_text_embed": community_report_title_embed_config,
                "raw_content_text_embed": document_raw_content_embed_config,
                "name_text_embed": entity_name_embed_config,
                "name_description_text_embed": entity_name_description_embed_config,
                "description_text_embed": relationship_description_embed_config,
                "text_text_embed": text_unit_text_embed_config,
                "embedded_fields": embedded_fields,
            },
            "input": input,
        },
    ]
