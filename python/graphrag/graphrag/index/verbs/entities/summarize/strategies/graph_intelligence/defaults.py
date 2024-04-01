#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A file containing some default responses."""

from graphrag.index.llm.types import LLMType

MOCK_LLM_RESPONSES = [
    """
    This is a MOCK response for the LLM. It is summarized!
    """.strip()
]

DEFAULT_LLM_CONFIG = {
    "type": LLMType.StaticResponse,
    "responses": MOCK_LLM_RESPONSES,
}
