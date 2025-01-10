# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Contains the schema for the node and edge tables."""

# NODE TABLE SCHEMA
NODE_ID = "id"
NODE_SHORT_ID = "human_readable_id"
NODE_NAME = "title"
NODE_DEGREE = "degree"
NODE_FREQUENCY = "freq"
NODE_DESCRIPTION = "description"
NODE_COMMUNITY = "community"
NODE_PARENT_COMMUNITY = "parent_community"
NODE_LEVEL = "level"
NODE_TEXT_UNIT_IDS = "text_unit_ids"

# EDGE TABLE SCHEMA
EDGE_ID = "id"
EDGE_SHORT_ID = "human_readable_id"
EDGE_SOURCE = "source"
EDGE_TARGET = "target"
EDGE_DESCRIPTION = "description"
EDGE_DEGREE = "combined_degree"
EDGE_WEIGHT = "weight"
EDGE_TEXT_UNIT_IDS = "text_unit_ids"
