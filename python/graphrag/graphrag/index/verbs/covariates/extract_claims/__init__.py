#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine text extract claims package root."""
from .extract_claims import ExtractClaimsStrategyType, extract_claims

__all__ = ["extract_claims", "ExtractClaimsStrategyType"]
