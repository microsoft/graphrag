# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import Field

import graphrag.config.defaults as defs

from .llm_config import LLMConfig


class ClaimExtractionConfig(LLMConfig):
    """Configuration section for claim extraction."""

    enabled: bool = Field(
        description="Whether claim extraction is enabled.",
    )
    prompt: str | None = Field(
        description="The claim extraction prompt to use.", default=None
    )
    description: str = Field(
        description="The claim description to use.",
        default=defs.CLAIM_DESCRIPTION,
    )
    max_gleanings: int = Field(
        description="The maximum number of entity gleanings to use.",
        default=defs.CLAIM_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
    encoding_model: str | None = Field(
        default=None, description="The encoding model to use."
    )

    def resolved_strategy(self, root_dir: str, encoding_model: str) -> dict:
        """Get the resolved claim extraction strategy."""
        from graphrag.index.verbs.covariates.extract_covariates import (
            ExtractClaimsStrategyType,
        )

        return self.strategy or {
            "type": ExtractClaimsStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt)
            .read_bytes()
            .decode(encoding="utf-8")
            if self.prompt
            else None,
            "claim_description": self.description,
            "max_gleanings": self.max_gleanings,
            "encoding_name": self.encoding_model or encoding_model,
        }
