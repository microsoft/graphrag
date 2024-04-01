#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Root package for resolution entities."""

from .description_summarize import SummarizeStrategyType, summarize_descriptions

__all__ = ["summarize_descriptions", "SummarizeStrategyType"]
