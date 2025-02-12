# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.models.language_model_config import LanguageModelConfig


class ClaimExtractionConfig(BaseModel):
    """Configuration section for claim extraction."""

    enabled: bool = Field(
        description="Whether claim extraction is enabled.",
        default=defs.EXTRACT_CLAIMS_ENABLED,
    )
    prompt: str | None = Field(
        description="The claim extraction prompt to use.", default=None
    )
    description: str = Field(
        description="The claim description to use.",
        default=defs.DESCRIPTION,
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
    model_id: str = Field(
        description="The model ID to use for claim extraction.",
        default=defs.EXTRACT_CLAIMS_MODEL_ID,
    )

    def resolved_strategy(
        self, root_dir: str, model_config: LanguageModelConfig
    ) -> dict:
        """Get the resolved claim extraction strategy."""
        return self.strategy or {
            "llm": model_config.model_dump(),
            "num_threads": model_config.concurrent_requests,
            "extraction_prompt": (Path(root_dir) / self.prompt).read_text(
                encoding="utf-8"
            )
            if self.prompt
            else None,
            "claim_description": self.description,
            "max_gleanings": self.max_gleanings,
            "encoding_name": model_config.encoding_model,
        }
