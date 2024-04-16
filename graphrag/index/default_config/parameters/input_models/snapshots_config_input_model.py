# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing import TypedDict

from typing_extensions import NotRequired


class SnapshotsConfigInputModel(TypedDict):
    """Configuration section for snapshots."""

    graphml: NotRequired[bool | str | None]
    raw_entities: NotRequired[bool | str | None]
    top_level_nodes: NotRequired[bool | str | None]
