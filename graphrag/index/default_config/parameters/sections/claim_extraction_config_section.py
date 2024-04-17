# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_CLAIM_DESCRIPTION,
    DEFAULT_CLAIM_MAX_GLEANINGS,
)
from graphrag.index.default_config.parameters.models import (
    ClaimExtractionConfigModel,
    LLMConfigModel,
)
from graphrag.index.verbs.covariates.extract_covariates import ExtractClaimsStrategyType

from .config_section import read_text_file
from .llm_config_section import LLMConfigSection


class ClaimExtractionConfigSection(LLMConfigSection):
    """The default configuration section for ClaimExtraction, loaded from environment variables."""

    _root_dir: str
    _values: ClaimExtractionConfigModel

    def __init__(
        self,
        values: ClaimExtractionConfigModel,
        root: LLMConfigModel,
        root_dir: str,
        env: Env,
    ):
        """Create a new instance of the parameters class."""
        super().__init__(values, root, env)
        self._root_dir = root_dir

    @property
    def description(self) -> str | None:
        """The claim description to use."""
        return self.replace(
            self._values.description,
            DEFAULT_CLAIM_DESCRIPTION,
        )

    @property
    def prompt(self) -> str | None:
        """The claim extraction prompt to use."""
        file = self.replace(self._values.prompt, None)
        if file is not None:
            return read_text_file(self._root_dir, file)
        return None

    @property
    def max_gleanings(self) -> int:
        """The maximum number of entity gleanings to use."""
        return self.replace(self._values.max_gleanings, DEFAULT_CLAIM_MAX_GLEANINGS)

    @property
    def strategy(self) -> dict | None:
        """The override strategy to use."""
        return self.replace_dict(self._values.strategy) or {
            "type": ExtractClaimsStrategyType.graph_intelligence,
            "async_mode": self.async_mode,
            "llm": self.llm,
            "extraction_prompt": self.prompt,
            "claim_description": self.description,
            "max_gleanings": self.max_gleanings,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            **super().to_dict(),
            "description": self.description,
            "prompt": self.prompt,
            "max_gleanings": self.max_gleanings,
            "strategy": self._values.strategy,
        }
