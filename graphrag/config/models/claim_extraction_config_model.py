# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import Field

from graphrag.config.defaults import (
    DEFAULT_CLAIM_DESCRIPTION,
    DEFAULT_CLAIM_MAX_GLEANINGS,
)

from .llm_config_model import LLMConfigModel


class ClaimExtractionConfigModel(LLMConfigModel):
    """Configuration section for claim extraction."""

    prompt: str | None = Field(
        description="The claim extraction prompt to use.", default=None
    )
    description: str = Field(
        description="The claim description to use.",
        default=DEFAULT_CLAIM_DESCRIPTION,
    )
    max_gleanings: int = Field(
        description="The maximum number of entity gleanings to use.",
        default=DEFAULT_CLAIM_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )

    def resolved_strategy(self, root_dir: str) -> dict:
        """Get the resolved claim extraction strategy."""
        from graphrag.index.verbs.covariates.extract_covariates import (
            ExtractClaimsStrategyType,
        )

        return self.strategy or {
            "type": ExtractClaimsStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt).read_text()
            if self.prompt
            else None,
            "claim_description": self.description,
            "max_gleanings": self.max_gleanings,
        }
