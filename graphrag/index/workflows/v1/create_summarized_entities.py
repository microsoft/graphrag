# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import AsyncType

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_summarized_entities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for extracted entities.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    entity_extraction_config = config.get("entity_extract", {})
    column = entity_extraction_config.get("text_column", "chunk")
    id_column = entity_extraction_config.get("id_column", "chunk_id")
    async_mode = entity_extraction_config.get("async_mode", AsyncType.AsyncIO)
    extraction_strategy = entity_extraction_config.get("strategy")
    extraction_num_threads = entity_extraction_config.get("num_threads", 4)
    entity_types = entity_extraction_config.get("entity_types")

    graph_merge_operations_config = config.get(
        "graph_merge_operations",
        {
            "nodes": {
                "source_id": {
                    "operation": "concat",
                    "delimiter": ", ",
                    "distinct": True,
                },
                "description": ({
                    "operation": "concat",
                    "separator": "\n",
                    "distinct": False,
                }),
            },
            "edges": {
                "source_id": {
                    "operation": "concat",
                    "delimiter": ", ",
                    "distinct": True,
                },
                "description": ({
                    "operation": "concat",
                    "separator": "\n",
                    "distinct": False,
                }),
                "weight": "sum",
            },
        },
    )
    node_merge_config = graph_merge_operations_config.get("nodes")
    edge_merge_config = graph_merge_operations_config.get("edges")

    summarize_descriptions_config = config.get("summarize_descriptions", {})
    summarization_strategy = summarize_descriptions_config.get("strategy")
    summarization_num_threads = summarize_descriptions_config.get("num_threads", 4)

    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False
    raw_entity_snapshot_enabled = config.get("raw_entity_snapshot", False) or False

    return [
        {
            "verb": "create_summarized_entities",
            "args": {
                "column": column,
                "id_column": id_column,
                "extraction_strategy": extraction_strategy,
                "extraction_num_threads": extraction_num_threads,
                "extraction_async_mode": async_mode,
                "entity_types": entity_types,
                "node_merge_config": node_merge_config,
                "edge_merge_config": edge_merge_config,
                "summarization_strategy": summarization_strategy,
                "summarization_num_threads": summarization_num_threads,
                "raw_entity_snapshot_enabled": raw_entity_snapshot_enabled,
                "graphml_snapshot_enabled": graphml_snapshot_enabled,
            },
            "input": {"source": "workflow:create_base_text_units"},
        },
    ]
