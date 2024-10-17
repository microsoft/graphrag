# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

PARQUET_FILE_NAME__NODES: str = "create_final_nodes.parquet"
PARQUET_FILE_NAME__ENTITIES: str = "create_final_entities.parquet"
PARQUET_FILE_NAME__COMMUNITY_REPORTS: str = "create_final_community_reports.parquet"
PARQUET_FILE_NAME__TEXT_UNITS: str = "create_final_text_units.parquet"
PARQUET_FILE_NAME__RELATIONSHIPS: str = "create_final_relationships.parquet"
PARQUET_FILE_NAME__COVARIATES: str = "create_final_covariates.parquet"

COLUMN__ENTITY__ID: str = "id"
COLUMN__ENTITY__TITLE: str = "name"
COLUMN__ENTITY__TYPE: str = "type"
COLUMN__ENTITY__SHORT_ID: str = "human_readable_id"
COLUMN__ENTITY__DESCRIPTION: str = "description"
COLUMN__ENTITY__COMMUNITY: str = "community"
COLUMN__ENTITY__RANK: str = "rank"
COLUMN__ENTITY__NAME_EMBEDDING: typing.Optional[str] = None
COLUMN__ENTITY__DESCRIPTION_EMBEDDING: str = "description_embedding"
COLUMN__ENTITY__GRAPH_EMBEDDING: typing.Optional[str] = None
COLUMN__ENTITY__TEXT_UNIT_IDS: str = "text_unit_ids"
COLUMN__ENTITY__DOCUMENT_IDS: typing.Optional[str] = None
COLUMN__ENTITY__ATTRIBUTES: typing.Optional[typing.List[str]] = None

COLUMN__COMMUNITY_REPORT__ID: str = "community"
COLUMN__COMMUNITY_REPORT__SHORT_ID: str = "community"
COLUMN__COMMUNITY_REPORT__SUMMARY_EMBEDDING: typing.Optional[str] = None
COLUMN__COMMUNITY_REPORT__CONTENT_EMBEDDING: typing.Optional[str] = None

COLUMN__RELATIONSHIP__SHORT_ID: str = "human_readable_id"
COLUMN__RELATIONSHIP__DESCRIPTION_EMBEDDING: typing.Optional[str] = None
COLUMN__RELATIONSHIP__DOCUMENT_IDS: typing.Optional[str] = None
COLUMN__RELATIONSHIP__ATTRIBUTES: typing.List[str] = ["rank"]

COLUMN__COVARIATE__SHORT_ID: str = "human_readable_id"
COLUMN__COVARIATE__ATTRIBUTES: typing.List[str] = ["object_id", "status", "start_date", "end_date", "description"]
COLUMN__COVARIATE__TEXT_UNIT_IDS: typing.Optional[str] = None

COLUMN__TEXT_UNIT__SHORT_ID: typing.Optional[str] = None
COLUMN__TEXT_UNIT__COVARIATES: typing.Optional[str] = None
