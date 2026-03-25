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
CURRENT_STATE = "current_state"
TIMELINE_EVENTS = "timeline_events"
SUPERSEDED_FACTS = "superseded_facts"
DATE_RANGE = "date_range"

ENTITY_IDS = "entity_ids"
RELATIONSHIP_IDS = "relationship_ids"
TEXT_UNIT_IDS = "text_unit_ids"
COVARIATE_IDS = "covariate_ids"
DOCUMENT_ID = "document_id"

PERIOD = "period"
SIZE = "size"

# text units
ENTITY_DEGREE = "entity_degree"
ALL_DETAILS = "all_details"
TEXT = "text"
N_TOKENS = "n_tokens"

CREATION_DATE = "creation_date"
RAW_DATA = "raw_data"
CONVERSATION_ID = "conversation_id"
TURN_INDEX = "turn_index"
TURN_TIMESTAMP = "turn_timestamp"
TURN_ROLE = "turn_role"
START_TURN_INDEX = "start_turn_index"
END_TURN_INDEX = "end_turn_index"
TURN_TIMESTAMP_START = "turn_timestamp_start"
TURN_TIMESTAMP_END = "turn_timestamp_end"
INCLUDED_ROLES = "included_roles"
CHUNK_INDEX_IN_DOCUMENT = "chunk_index_in_document"
CHUNK_INDEX_IN_CONVERSATION = "chunk_index_in_conversation"
FIRST_SEEN_TURN_INDEX = "first_seen_turn_index"
LAST_SEEN_TURN_INDEX = "last_seen_turn_index"
FIRST_SEEN_TIMESTAMP = "first_seen_timestamp"
LAST_SEEN_TIMESTAMP = "last_seen_timestamp"
FIRST_SEEN_TEXT_UNIT_ID = "first_seen_text_unit_id"
LAST_SEEN_TEXT_UNIT_ID = "last_seen_text_unit_id"
EVIDENCE_COUNT = "evidence_count"

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
    FIRST_SEEN_TURN_INDEX,
    LAST_SEEN_TURN_INDEX,
    FIRST_SEEN_TIMESTAMP,
    LAST_SEEN_TIMESTAMP,
    FIRST_SEEN_TEXT_UNIT_ID,
    LAST_SEEN_TEXT_UNIT_ID,
    EVIDENCE_COUNT,
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
    FIRST_SEEN_TURN_INDEX,
    LAST_SEEN_TURN_INDEX,
    FIRST_SEEN_TIMESTAMP,
    LAST_SEEN_TIMESTAMP,
    FIRST_SEEN_TEXT_UNIT_ID,
    LAST_SEEN_TEXT_UNIT_ID,
    EVIDENCE_COUNT,
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
    CURRENT_STATE,
    TIMELINE_EVENTS,
    SUPERSEDED_FACTS,
    DATE_RANGE,
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
    DOCUMENT_ID,
    CONVERSATION_ID,
    TURN_INDEX,
    TURN_TIMESTAMP,
    TURN_ROLE,
    START_TURN_INDEX,
    END_TURN_INDEX,
    TURN_TIMESTAMP_START,
    TURN_TIMESTAMP_END,
    INCLUDED_ROLES,
    CHUNK_INDEX_IN_DOCUMENT,
    CHUNK_INDEX_IN_CONVERSATION,
    ENTITY_IDS,
    RELATIONSHIP_IDS,
    COVARIATE_IDS,
]

DOCUMENTS_FINAL_COLUMNS = [
    ID,
    SHORT_ID,
    TITLE,
    TEXT,
    CONVERSATION_ID,
    TURN_INDEX,
    TURN_TIMESTAMP,
    TURN_ROLE,
    TEXT_UNIT_IDS,
    CREATION_DATE,
    RAW_DATA,
]
