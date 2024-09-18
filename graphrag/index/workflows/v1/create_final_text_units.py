# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final text-units table.

    ## Dependencies
    * `workflow:create_base_text_units`
    * `workflow:create_final_entities`
    * `workflow:create_final_communities`
    """
    base_text_embed = config.get("text_embed", {})
    text_unit_text_embed_config = config.get("text_unit_text_embed", base_text_embed)
    covariates_enabled = config.get("covariates_enabled", False)
    skip_text_unit_embedding = config.get("skip_text_unit_embedding", False)
    is_using_vector_store = (
        text_unit_text_embed_config.get("strategy", {}).get("vector_store", None)
        is not None
    )

    others = [
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
    ]
    if covariates_enabled:
        others.append("workflow:create_final_covariates")

    return [
        {
            "verb": "create_final_text_units_pre_embedding",
            "args": {
                "covariates_enabled": covariates_enabled,
            },
            "input": {
                "source": "workflow:create_base_text_units",
                "others": others,
            },
        },
        # Text-Embed after final aggregations
        {
            "id": "embedded_text_units",
            "verb": "text_embed",
            "enabled": not skip_text_unit_embedding,
            "args": {
                "column": config.get("column", "text"),
                "to": config.get("to", "text_embedding"),
                **text_unit_text_embed_config,
            },
        },
        {
            "verb": "select",
            "args": {
                # Final select to get output in the correct shape
                "columns": [
                    "id",
                    "text",
                    *(
                        []
                        if (skip_text_unit_embedding or is_using_vector_store)
                        else ["text_embedding"]
                    ),
                    "n_tokens",
                    "document_ids",
                    "entity_ids",
                    "relationship_ids",
                    *([] if not covariates_enabled else ["covariate_ids"]),
                ],
            },
        },
    ]
