# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_communities"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final communities table.

    ## Dependencies
    * `workflow:create_base_entity_graph`
    """
    return [
        {
            "id": "graph_nodes",
            "verb": "unpack_graph",
            "args": {
                "column": "clustered_graph",
                "type": "nodes",
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "id": "graph_edges",
            "verb": "unpack_graph",
            "args": {
                "column": "clustered_graph",
                "type": "edges",
            },
            "input": {"source": "workflow:create_base_entity_graph"},
        },
        {
            "id": "source_clusters",
            "verb": "join",
            "args": {
                "on": ["label", "source"],
            },
            "input": {"source": "graph_nodes", "others": ["graph_edges"]},
        },
        {
            "id": "target_clusters",
            "verb": "join",
            "args": {
                "on": ["label", "target"],
            },
            "input": {"source": "graph_nodes", "others": ["graph_edges"]},
        },
        {
            "id": "concatenated_clusters",
            "verb": "concat",
            "input": {
                "source": "source_clusters",
                "others": ["target_clusters"],
            },
        },
        {
            "id": "combined_clusters",
            "verb": "filter",
            "args": {
                # level_1 is the left side of the join
                # level_2 is the right side of the join
                "column": "level_1",
                "criteria": [
                    {"type": "column", "operator": "equals", "value": "level_2"}
                ],
            },
            "input": {"source": "concatenated_clusters"},
        },
        {
            "id": "cluster_relationships",
            "verb": "aggregate_override",
            "args": {
                "groupby": [
                    "cluster",
                    "level_1",  # level_1 is the left side of the join
                ],
                "aggregations": [
                    {
                        "column": "id_2",  # this is the id of the edge from the join steps above
                        "to": "relationship_ids",
                        "operation": "array_agg_distinct",
                    },
                    {
                        "column": "source_id_1",
                        "to": "text_unit_ids",
                        "operation": "array_agg_distinct",
                    },
                ],
            },
            "input": {"source": "combined_clusters"},
        },
        {
            "id": "all_clusters",
            "verb": "aggregate_override",
            "args": {
                "groupby": ["cluster", "level"],
                "aggregations": [{"column": "cluster", "to": "id", "operation": "any"}],
            },
            "input": {"source": "graph_nodes"},
        },
        {
            "verb": "join",
            "args": {
                "on": ["id", "cluster"],
            },
            "input": {"source": "all_clusters", "others": ["cluster_relationships"]},
        },
        {
            "verb": "filter",
            "args": {
                # level is the left side of the join
                # level_1 is the right side of the join
                "column": "level",
                "criteria": [
                    {"type": "column", "operator": "equals", "value": "level_1"}
                ],
            },
        },
        *create_community_title_wf,
        {
            # TODO: Rodrigo says "raw_community" is temporary
            "verb": "copy",
            "args": {
                "column": "id",
                "to": "raw_community",
            },
        },
        {
            "verb": "select",
            "args": {
                "columns": [
                    "id",
                    "title",
                    "level",
                    "raw_community",
                    "relationship_ids",
                    "text_unit_ids",
                ],
            },
        },
    ]


create_community_title_wf = [
    # Hack to string concat "Community " + id
    {
        "verb": "fill",
        "args": {
            "to": "__temp",
            "value": "Community ",
        },
    },
    {
        "verb": "merge",
        "args": {
            "columns": [
                "__temp",
                "id",
            ],
            "to": "title",
            "strategy": "concat",
            "preserveSource": True,
        },
    },
]
