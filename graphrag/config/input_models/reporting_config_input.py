# Copyright (c) 2024 Microsoft Corporation.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired, TypedDict

from graphrag.config.enums import ReportingType


class ReportingConfigInput(TypedDict):
    """The default configuration section for Reporting."""

    type: NotRequired[ReportingType | str | None]
    base_dir: NotRequired[str | None]
    connection_string: NotRequired[str | None]
    container_name: NotRequired[str | None]
