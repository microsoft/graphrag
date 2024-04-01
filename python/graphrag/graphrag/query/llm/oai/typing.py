#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""OpenAI wrapper options."""
from enum import Enum
from typing import Any, cast

import openai

OPENAI_RETRY_ERROR_TYPES = (
    # TODO: update these when we update to OpenAI 1+ library
    cast(Any, openai).RateLimitError,
    cast(Any, openai).APIConnectionError,
    # TODO: replace with comparable OpenAI 1+ error
)


class OpenaiApiType(str, Enum):
    """The OpenAI Flavor."""

    OpenAI = "openai"
    AzureOpenAI = "azure"
