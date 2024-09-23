# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine community reports package root."""

import graphrag.index.graph.extractors.community_reports.schemas as schemas

from .build_mixed_context import build_mixed_context
from .community_reports_extractor import CommunityReportsExtractor
from .prep_community_report_context import prep_community_report_context
from .prompts import COMMUNITY_REPORT_PROMPT
from .sort_context import sort_context
from .utils import (
    filter_claims_to_nodes,
    filter_edges_to_nodes,
    filter_nodes_to_level,
    get_levels,
    set_context_exceeds_flag,
    set_context_size,
)

__all__ = [
    "COMMUNITY_REPORT_PROMPT",
    "CommunityReportsExtractor",
    "build_mixed_context",
    "filter_claims_to_nodes",
    "filter_edges_to_nodes",
    "filter_nodes_to_level",
    "get_levels",
    "prep_community_report_context",
    "schemas",
    "set_context_exceeds_flag",
    "set_context_size",
    "sort_context",
]
