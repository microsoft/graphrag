#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine entities package root."""

from .extraction import entity_extract
from .summarize import summarize_descriptions

__all__ = ["entity_extract", "summarize_descriptions"]
