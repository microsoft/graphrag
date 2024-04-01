#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine entities extraction package root."""
from .entity_extract import ExtractEntityStrategyType, entity_extract

__all__ = ["entity_extract", "ExtractEntityStrategyType"]
