#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
    text_embed_config = config.get("text_embed", {})
    skip_name_embedding = config.get("skip_name_embedding", False)
    skip_description_embedding = config.get("skip_description_embedding", False)

    result = [
        {
            "verb": "unpack_graph",
            "args": {
                "column": "clustered_graph",
                "type": "nodes",
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {"verb": "rename", "args": {"columns": {"label": "title"}}},
        {
            "verb": "select",
            "args": {
                "columns": [
                    "id",
                    "title",
                    "type",
                    "description",
                    "human_readable_id",
                    "graph_embedding",
                    "source_id",
                ],
            },
        },
        {
            # create_base_entity_graph has multiple levels of clustering, which means there are multiple graphs with the same entities
            # this dedupes the entities so that there is only one of each entity
            "verb": "dedupe",
            "args": {"columns": ["id"]},
        },
        {"verb": "rename", "args": {"columns": {"title": "name"}}},
        {
            # ELIMINATE EMPTY NAMES
            "verb": "filter",
            "args": {
                "column": "name",
                "criteria": [
                    {
                        "type": "value",
                        "operator": "is not empty",
                    }
                ],
            },
        },
        {
            "verb": "text_split",
            "args": {"separator": ",", "column": "source_id", "to": "text_unit_ids"},
        },
        {"verb": "drop", "args": {"columns": ["source_id"]}},
    ]

    if not skip_name_embedding:
        result.append(
            {
                "verb": "text_embed",
                "args": {
                    "column": "name",
                    "to": "name_embedding",
                    **text_embed_config,
                },
            }
        )

    if not skip_description_embedding:
        result.extend(
            [
                {
                    "verb": "merge",
                    "args": {
                        "strategy": "concat",
                        "columns": ["name", "description"],
                        "to": "name_description",
                        "delimiter": ":",
                        "preserveSource": True,
                    },
                },
                {
                    "verb": "text_embed",
                    "args": {
                        "column": "name_description",
                        "to": "description_embedding",
                        **text_embed_config,
                    },
                },
                {
                    "verb": "drop",
                    "args": {
                        "columns": ["name_description"],
                    },
                },
                {
                    # ELIMINATE EMPTY DESCRIPTION EMBEDDINGS
                    "verb": "filter",
                    "args": {
                        "column": "description_embedding",
                        "criteria": [
                            {
                                "type": "value",
                                "operator": "is not empty",
                            }
                        ],
                    },
                },
            ]
        )

    return result
