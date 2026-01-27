# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.prompts.index.extract_claims import EXTRACT_CLAIMS_PROMPT


@dataclass
class ClaimExtractionPrompts:
    """Claim extraction prompt templates."""

    extraction_prompt: str


class ExtractClaimsConfig(BaseModel):
    """Configuration section for claim extraction."""

    enabled: bool = Field(
        description="Whether claim extraction is enabled.",
        default=graphrag_config_defaults.extract_claims.enabled,
    )
    completion_model_id: str = Field(
        description="The model ID to use for claim extraction.",
        default=graphrag_config_defaults.extract_claims.completion_model_id,
    )
    model_instance_name: str = Field(
        description="The model singleton instance name. This primarily affects the cache storage partitioning.",
        default=graphrag_config_defaults.extract_claims.model_instance_name,
    )
    prompt: str | None = Field(
        description="The claim extraction prompt to use.",
        default=graphrag_config_defaults.extract_claims.prompt,
    )
    description: str = Field(
        description="The claim description to use.",
        default=graphrag_config_defaults.extract_claims.description,
    )
    max_gleanings: int = Field(
        description="The maximum number of entity gleanings to use.",
        default=graphrag_config_defaults.extract_claims.max_gleanings,
    )

    def resolved_prompts(self) -> ClaimExtractionPrompts:
        """Get the resolved claim extraction prompts."""
        return ClaimExtractionPrompts(
            extraction_prompt=Path(self.prompt).read_text(encoding="utf-8")
            if self.prompt
            else EXTRACT_CLAIMS_PROMPT,
        )
