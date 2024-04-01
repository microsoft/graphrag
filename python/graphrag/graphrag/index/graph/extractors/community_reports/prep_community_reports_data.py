#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing prep_community_reports_data method definition."""
import logging

from graphrag.index.text_splitting import check_token_limit

log = logging.getLogger(__name__)

_DEFAULT_MISSING_DESCRIPTION_TEXT = "No Description"


def prep_community_reports_data(
    nodes: list[dict],
    edges: list[dict],
    claims: list[dict] | None,
    max_tokens: int = 25000,
) -> dict:
    """Prep community reports data method definition."""
    communities = {}
    for node in nodes:
        community = node.get("cluster", node.get("community", None))
        if community is not None and community not in communities:
            communities[community] = {
                "entity_details": [],
                "entity_relationships": [],
                "entity_claims": [],
            }
            # node details
            node_details = f'{node["human_readable_id"]},{node["label"]},{node.get("description", _DEFAULT_MISSING_DESCRIPTION_TEXT)}'
            communities[community]["entity_details"].append(node_details)

            # node_edges
            node_edges = [edge for edge in edges if edge["source"] == node["label"]]
            for edge in node_edges:
                edge_description = f'{edge["human_readable_id"]},{edge["source"]},{edge["target"]},{edge.get("description", _DEFAULT_MISSING_DESCRIPTION_TEXT)}'
                communities[community]["entity_relationships"].append(edge_description)

            # claims
            if claims is not None:
                node_claims = [
                    claim for claim in claims if claim["subject"] == node["label"]
                ]
                for claim in node_claims:
                    claim_description = f'{claim["human_readable_id"]},{claim["subject"]},{claim["type"]},{claim["status"]},{claim.get("description", _DEFAULT_MISSING_DESCRIPTION_TEXT)}'
                    communities[community]["entity_claims"].append(claim_description)

    community_descriptions = {}
    for community in communities:
        description_list = ["Entities\n", "id,entity,description"]
        entity_details = communities[community]["entity_details"]
        description_list.extend(entity_details)

        description_list.extend(["\nClaims\n", "id,subject,type,status,description"])
        entity_claims = communities[community]["entity_claims"]
        description_list.extend(entity_claims)

        description_list.extend(["\nRelationships\n", "id,source,target,description"])
        entity_relationships = communities[community]["entity_relationships"]
        description_list.extend(entity_relationships)

        all_descriptions = ""
        for record in description_list:
            updated_description = all_descriptions + "\n" + record
            if check_token_limit(updated_description, max_tokens) == 0:
                log.info("community %s: text is trimmed", community)
                break

            all_descriptions = updated_description
        community_descriptions[community] = all_descriptions
    return community_descriptions
