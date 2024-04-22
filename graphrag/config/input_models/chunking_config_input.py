# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict


class ChunkingConfigInput(TypedDict):
    """Configuration section for chunking."""

    size: NotRequired[int | str | None]
    overlap: NotRequired[int | str | None]
    group_by_columns: NotRequired[list[str] | str | None]
    strategy: NotRequired[dict | None]
