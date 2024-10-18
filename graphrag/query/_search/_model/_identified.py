# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import pydantic


class Identified(pydantic.BaseModel):
    """A protocol for an item with an ID."""

    id: str = ""
    """The ID of the item."""

    short_id: typing.Optional[str] = None
    """
    Human readable ID used to refer to this community in prompts or texts 
    displayed to users, such as in a report text (optional).
    """
