# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Common field name definitions for data frames."""

ID = "id"
SHORT_ID = "human_readable_id"
TITLE = "title"
DESCRIPTION = "description"

TYPE = "type"

# POST-PREP NODE TABLE SCHEMA
NODE_DEGREE = "degree"
NODE_FREQUENCY = "frequency"
NODE_DETAILS = "node_details"
NODE_X = "x"
NODE_Y = "y"

# POST-PREP EDGE TABLE SCHEMA
EDGE_SOURCE = "source"
EDGE_TARGET = "target"
EDGE_DEGREE = "combined_degree"
EDGE_DETAILS = "edge_details"
EDGE_WEIGHT = "weight"

# POST-PREP CLAIM TABLE SCHEMA
CLAIM_SUBJECT = "subject_id"
CLAIM_STATUS = "status"
CLAIM_DETAILS = "claim_details"

# COMMUNITY HIERARCHY TABLE SCHEMA
SUB_COMMUNITY = "sub_community"

# COMMUNITY CONTEXT TABLE SCHEMA
ALL_CONTEXT = "all_context"
CONTEXT_STRING = "context_string"
CONTEXT_SIZE = "context_size"
CONTEXT_EXCEED_FLAG = "context_exceed_limit"

# COMMUNITY REPORT TABLE SCHEMA
COMMUNITY_ID = "community"
COMMUNITY_LEVEL = "level"
COMMUNITY_PARENT = "parent"
COMMUNITY_CHILDREN = "children"
TITLE = "title"
SUMMARY = "summary"
FINDINGS = "findings"
RATING = "rank"
EXPLANATION = "rating_explanation"
FULL_CONTENT = "full_content"
FULL_CONTENT_JSON = "full_content_json"

ENTITY_IDS = "entity_ids"
RELATIONSHIP_IDS = "relationship_ids"
TEXT_UNIT_IDS = "text_unit_ids"
COVARIATE_IDS = "covariate_ids"
DOCUMENT_IDS = "document_ids"

PERIOD = "period"
SIZE = "size"

# text units
ENTITY_DEGREE = "entity_degree"
ALL_DETAILS = "all_details"
TEXT = "text"
N_TOKENS = "n_tokens"

CREATION_DATE = "creation_date"
METADATA = "metadata"

# the following lists define the final content and ordering of columns in the data model parquet outputs
ENTITIES_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    TITLE,
    TYPE,
    DESCRIPTION,
    TEXT_UNIT_IDS,
    NODE_FREQUENCY,
    NODE_DEGREE,
    NODE_X,
    NODE_Y,
]

RELATIONSHIPS_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    EDGE_SOURCE,
    EDGE_TARGET,
    DESCRIPTION,
    EDGE_WEIGHT,
    EDGE_DEGREE,
    TEXT_UNIT_IDS,
]

COMMUNITIES_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    COMMUNITY_ID,
    COMMUNITY_LEVEL,
    COMMUNITY_PARENT,
    COMMUNITY_CHILDREN,
    TITLE,
    ENTITY_IDS,
    RELATIONSHIP_IDS,
    TEXT_UNIT_IDS,
    PERIOD,
    SIZE,
]

COMMUNITY_REPORTS_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    COMMUNITY_ID,
    COMMUNITY_LEVEL,
    COMMUNITY_PARENT,
    COMMUNITY_CHILDREN,
    TITLE,
    SUMMARY,
    FULL_CONTENT,
    RATING,
    EXPLANATION,
    FINDINGS,
    FULL_CONTENT_JSON,
    PERIOD,
    SIZE,
]

COVARIATES_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    "covariate_type",
    TYPE,
    DESCRIPTION,
    "subject_id",
    "object_id",
    "status",
    "start_date",
    "end_date",
    "source_text",
    "text_unit_id",
]

TEXT_UNITS_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    TEXT,
    N_TOKENS,
    DOCUMENT_IDS,
    ENTITY_IDS,
    RELATIONSHIP_IDS,
    COVARIATE_IDS,
]

DOCUMENTS_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    TITLE,
    TEXT,
    TEXT_UNIT_IDS,
    CREATION_DATE,
    METADATA,
]
