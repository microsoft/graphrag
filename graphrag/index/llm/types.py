# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing the 'LLMtype' model."""

from collections.abc import Callable
from enum import Enum
from typing import TypeAlias

TextSplitter: TypeAlias = Callable[[str], list[str]]
TextListSplitter: TypeAlias = Callable[[list[str]], list[str]]
