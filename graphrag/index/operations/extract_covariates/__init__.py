# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine text extract claims package root."""

from graphrag.index.operations.extract_covariates.extract_covariates import (
    ExtractClaimsStrategyType,
    extract_covariates,
)

__all__ = ["ExtractClaimsStrategyType", "extract_covariates"]
