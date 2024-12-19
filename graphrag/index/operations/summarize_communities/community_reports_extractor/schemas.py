# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Common field name definitions for community reports."""

# POST-PREP NODE TABLE SCHEMA
NODE_ID = "human_readable_id"
NODE_NAME = "title"
NODE_DESCRIPTION = "description"
NODE_DEGREE = "degree"
NODE_DETAILS = "node_details"
NODE_COMMUNITY = "community"
NODE_LEVEL = "level"

# POST-PREP EDGE TABLE SCHEMA
EDGE_ID = "human_readable_id"
EDGE_SOURCE = "source"
EDGE_TARGET = "target"
EDGE_DESCRIPTION = "description"
EDGE_DEGREE = "combined_degree"
EDGE_DETAILS = "edge_details"
EDGE_WEIGHT = "weight"

# POST-PREP CLAIM TABLE SCHEMA
CLAIM_ID = "human_readable_id"
CLAIM_SUBJECT = "subject_id"
CLAIM_TYPE = "type"
CLAIM_STATUS = "status"
CLAIM_DESCRIPTION = "description"
CLAIM_DETAILS = "claim_details"

# COMMUNITY HIERARCHY TABLE SCHEMA
SUB_COMMUNITY = "sub_community"
SUB_COMMUNITY_SIZE = "sub_community_size"
COMMUNITY_LEVEL = "level"

# COMMUNITY CONTEXT TABLE SCHEMA
ALL_CONTEXT = "all_context"
CONTEXT_STRING = "context_string"
CONTEXT_SIZE = "context_size"
CONTEXT_EXCEED_FLAG = "context_exceed_limit"

# COMMUNITY REPORT TABLE SCHEMA
REPORT_ID = "id"
COMMUNITY_ID = "community"
COMMUNITY_LEVEL = "level"
TITLE = "title"
SUMMARY = "summary"
FINDINGS = "findings"
RATING = "rank"
EXPLANATION = "rating_explanation"
FULL_CONTENT = "full_content"
FULL_CONTENT_JSON = "full_content_json"
