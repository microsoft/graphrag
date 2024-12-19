# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict


class BasicSearchConfigInput(TypedDict):
    """The default configuration section for Cache."""

    text_unit_prop: NotRequired[float | str | None]
    conversation_history_max_turns: NotRequired[int | str | None]
    max_tokens: NotRequired[int | str | None]
    llm_max_tokens: NotRequired[int | str | None]
