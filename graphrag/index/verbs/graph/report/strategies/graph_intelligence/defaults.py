# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing DEFAULT_CHUNK_SIZE and MOCK_RESPONSES definitions."""

import json

DEFAULT_CHUNK_SIZE = 3000
MOCK_RESPONSES = [
    json.dumps({
        "title": "<report_title>",
        "summary": "<executive_summary>",
        "rating": 2,
        "rating_explanation": "<rating_explanation>",
        "findings": [
            {
                "summary": "<insight_1_summary>",
                "explanation": "<insight_1_explanation",
            },
            {
                "summary": "<farts insight_2_summary>",
                "explanation": "<insight_2_explanation",
            },
        ],
    })
]
