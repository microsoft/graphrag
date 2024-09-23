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
    """
    base_text_embed = config.get("text_embed", {})
    relationship_description_embed_config = config.get(
        "relationship_description_embed", base_text_embed
    )
    skip_description_embedding = config.get("skip_description_embedding", False)

    return [
        {
            "verb": "unpack_graph",
            "args": {
                "column": "clustered_graph",
                "type": "edges",
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "verb": "rename",
            "args": {"columns": {"source_id": "text_unit_ids"}},
        },
        {
            "verb": "filter",
            "args": {
                "column": "level",
                "criteria": [{"type": "value", "operator": "equals", "value": 0}],
            },
        },
        {
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
            "id": "pruned_edges",
            "verb": "drop",
            "args": {"columns": ["level"]},
        },
        {
            "id": "filtered_nodes",
            "verb": "filter",
            "args": {
                "column": "level",
                "criteria": [{"type": "value", "operator": "equals", "value": 0}],
            },
            "input": "workflow:create_final_nodes",
        },
        {
            "verb": "compute_edge_combined_degree",
            "args": {"to": "rank"},
            "input": {
                "source": "pruned_edges",
                "nodes": "filtered_nodes",
            },
        },
        {
            "verb": "convert",
            "args": {
                "column": "human_readable_id",
                "type": "string",
                "to": "human_readable_id",
            },
        },
        {
            "verb": "convert",
            "args": {
                "column": "text_unit_ids",
                "type": "array",
                "to": "text_unit_ids",
            },
        },
    ]
