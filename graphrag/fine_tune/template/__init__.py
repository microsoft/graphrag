# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from .entity_extraction import (
    EXAMPLE_EXTRACTION_TEMPLATE,
    GRAPH_EXTRACTION_PROMPT,
    GRAPH_EXTRACTION_JSON_PROMPT,
)

from .entity_summarization import ENTITY_SUMMARIZATION_PROMPT

from .community_report_summarization import COMMUNITY_REPORT_SUMMARIZATION_PROMPT


__all__ = [
    "EXAMPLE_EXTRACTION_TEMPLATE",
    "GRAPH_EXTRACTION_PROMPT",
    "GRAPH_EXTRACTION_JSON_PROMPT",
    "ENTITY_SUMMARIZATION_PROMPT",
    "COMMUNITY_REPORT_SUMMARIZATION_PROMPT",
]
