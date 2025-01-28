# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Contains the schema for the community hierarchy, community membership, and community report tables."""

# common fields shared by all tables
COMMUNITY_ID = "community"
COMMUNITY_LEVEL = "level"

# community membership fields
ENTITY_IDS = "entity_ids"
RELATIONSHIP_IDS = "relationship_ids"
TEXT_UNIT_IDS = "text_unit_ids"
PARENT_COMMUNITY_ID = "parent_community"

# community hierarchy fields
SUB_COMMUNITY_ID = "sub_community"
SUB_COMMUNITY_SIZE = "sub_community_size"

# community report fields

# COMMUNITY CONTEXT TABLE SCHEMA
ALL_CONTEXT = "all_context"
CONTEXT_STRING = "context_string"
CONTEXT_SIZE = "context_size"
CONTEXT_EXCEED_FLAG = "context_exceed_limit"

# COMMUNITY REPORT TABLE SCHEMA
REPORT_ID = "id"
TITLE = "title"
SUMMARY = "summary"
FINDINGS = "findings"
RATING = "rank"
EXPLANATION = "rating_explanation"
FULL_CONTENT = "full_content"
DATE_RANGE = "date_range"
FULL_CONTENT_JSON = "full_content_json"
