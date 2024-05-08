# Copyright (c) 2024 Microsoft Corporation.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict


class UmapConfigInput(TypedDict):
    """Configuration section for UMAP."""

    enabled: NotRequired[bool | str | None]
