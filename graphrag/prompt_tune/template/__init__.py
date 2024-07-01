# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning prompts for entity extraction, entity summarization, and community report summarization."""

from .community_report_summarization import COMMUNITY_REPORT_SUMMARIZATION_PROMPT
from .entity_extraction import (
    EXAMPLE_EXTRACTION_TEMPLATE,
    GRAPH_EXTRACTION_JSON_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
    UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE,
    UNTYPED_GRAPH_EXTRACTION_PROMPT,
)
from .entity_summarization import ENTITY_SUMMARIZATION_PROMPT

__all__ = [
    "COMMUNITY_REPORT_SUMMARIZATION_PROMPT",
    "ENTITY_SUMMARIZATION_PROMPT",
    "EXAMPLE_EXTRACTION_TEMPLATE",
    "GRAPH_EXTRACTION_JSON_PROMPT",
    "GRAPH_EXTRACTION_PROMPT",
    "UNTYPED_EXAMPLE_EXTRACTION_TEMPLATE",
    "UNTYPED_GRAPH_EXTRACTION_PROMPT",
]
