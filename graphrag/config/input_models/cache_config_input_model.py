# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict

from graphrag.config.enums import PipelineCacheType


class CacheConfigInputModel(TypedDict):
    """The default configuration section for Cache."""

    type: NotRequired[PipelineCacheType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
