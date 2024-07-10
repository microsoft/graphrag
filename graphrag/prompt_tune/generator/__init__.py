# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Prompt generation module."""

from .community_report_rating import generate_community_report_rating
from .community_report_summarization import create_community_summarization_prompt
from .community_reporter_role import generate_community_reporter_role
from .defaults import MAX_TOKEN_COUNT
from .domain import generate_domain
from .entity_extraction_prompt import create_entity_extraction_prompt
from .entity_relationship import generate_entity_relationship_examples
from .entity_summarization_prompt import create_entity_summarization_prompt
from .entity_types import generate_entity_types
from .language import detect_language
from .persona import generate_persona

__all__ = [
    "MAX_TOKEN_COUNT",
    "create_community_summarization_prompt",
    "create_entity_extraction_prompt",
    "create_entity_summarization_prompt",
    "detect_language",
    "generate_community_report_rating",
    "generate_community_reporter_role",
    "generate_domain",
    "generate_entity_relationship_examples",
    "generate_entity_types",
    "generate_persona",
]
