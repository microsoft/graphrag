#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine graph extractors claims package root."""
from .claim_extractor import ClaimExtractor
from .prompts import CLAIM_EXTRACTION_PROMPT, CLAIM_SUMMARY_PROMPT

__all__ = ["ClaimExtractor", "CLAIM_EXTRACTION_PROMPT", "CLAIM_SUMMARY_PROMPT"]
