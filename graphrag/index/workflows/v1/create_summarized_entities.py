# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

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
    summarize_descriptions_config = config.get("summarize_descriptions", {})
    summarization_strategy = summarize_descriptions_config.get("strategy")
    num_threads = summarize_descriptions_config.get("num_threads", 4)

    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False

    return [
        {
            "verb": "create_summarized_entities",
            "args": {
                "summarization_strategy": summarization_strategy,
                "num_threads": num_threads,
                "graphml_snapshot_enabled": graphml_snapshot_enabled,
            },
            "input": {"source": "workflow:create_base_extracted_entities"},
        },
    ]
