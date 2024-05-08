# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine graph extractors claims package root."""

from .claim_extractor import ClaimExtractor
from .prompts import CLAIM_EXTRACTION_PROMPT

__all__ = ["CLAIM_EXTRACTION_PROMPT", "ClaimExtractor"]
