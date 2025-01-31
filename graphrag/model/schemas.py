# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Common field name definitions for community reports."""

ID = "id"
SHORT_ID = "human_readable_id"
TITLE = "title"
DESCRIPTION = "description"

# POST-PREP NODE TABLE SCHEMA
NODE_DEGREE = "degree"
NODE_FREQUENCY = "freq"
NODE_DETAILS = "node_details"

NODE_PARENT_COMMUNITY = "parent_community"

# POST-PREP EDGE TABLE SCHEMA
EDGE_SOURCE = "source"
EDGE_TARGET = "target"
EDGE_DEGREE = "combined_degree"
EDGE_DETAILS = "edge_details"
EDGE_WEIGHT = "weight"

# POST-PREP CLAIM TABLE SCHEMA
CLAIM_SUBJECT = "subject_id"
CLAIM_TYPE = "type"
CLAIM_STATUS = "status"
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
COMMUNITY_ID = "community"
COMMUNITY_LEVEL = "level"
TITLE = "title"
SUMMARY = "summary"
FINDINGS = "findings"
RATING = "rank"
EXPLANATION = "rating_explanation"
FULL_CONTENT = "full_content"
FULL_CONTENT_JSON = "full_content_json"

TEXT_UNIT_IDS = "text_unit_ids"

# text units
ENTITY_DEGREE = "entity_degree"
ALL_DETAILS = "all_details"
TEXT = "text"
