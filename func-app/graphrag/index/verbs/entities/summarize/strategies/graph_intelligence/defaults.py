# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A file containing some default responses."""

from graphrag.config.enums import LLMType

MOCK_LLM_RESPONSES = [
    """
    This is a MOCK response for the LLM. It is summarized!
    """.strip()
]

DEFAULT_LLM_CONFIG = {
    "type": LLMType.StaticResponse,
    "responses": MOCK_LLM_RESPONSES,
}
