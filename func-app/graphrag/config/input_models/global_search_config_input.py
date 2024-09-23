# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict


class GlobalSearchConfigInput(TypedDict):
    """The default configuration section for Cache."""

    max_tokens: NotRequired[int | str | None]
    data_max_tokens: NotRequired[int | str | None]
    map_max_tokens: NotRequired[int | str | None]
    reduce_max_tokens: NotRequired[int | str | None]
    concurrency: NotRequired[int | str | None]
