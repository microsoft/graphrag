# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
)
from graphrag.index.default_config.parameters.models import (
    EntityExtractionConfigModel,
    LLMConfigModel,
)
from graphrag.index.verbs.entities.extraction import ExtractEntityStrategyType

from .config_section import read_text_file
from .llm_config_section import LLMConfigSection


class EntityExtractionConfigSection(LLMConfigSection):
    """The default configuration section for EntityExtraction, loaded from environment variables."""

    _values: EntityExtractionConfigModel
    _root_dir: str
    _encoding_model: str

    def __init__(
        self,
        values: EntityExtractionConfigModel,
        root: LLMConfigModel,
        root_dir: str,
        encoding_model: str,
        env: Env,
    ):
        """Create a new instance of the parameters class."""
        super().__init__(values, root, env)
        self._values = values
        self._root_dir = root_dir
        self._encoding_model = encoding_model

    @property
    def entity_types(self) -> list[str]:
        """The entity extraction entity types to use."""
        return self.replace(
            self._values.entity_types,
            DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
        )

    @property
    def max_gleanings(self) -> int:
        """The maximum number of entity gleanings to use."""
        return self.replace(
            self._values.max_gleanings, DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS
        )

    @property
    def prompt(self) -> str | None:
        """The entity extraction prompt to use."""
        file = self.replace(self._values.prompt, None)
        if file is not None:
            return read_text_file(self._root_dir, file)
        return None

    @property
    def strategy(self) -> dict | None:
        """The entity extraction strategy to use, overriding the default tokenization strategy."""
        return self.replace_dict(self._values.strategy) or {
            "type": ExtractEntityStrategyType.graph_intelligence,
            "llm": self.llm,
            "extraction_prompt": self.prompt,
            "max_gleanings": self.max_gleanings,
            # It's prechunked in create_base_text_units
            "encoding_name": self._encoding_model,
            "prechunked": True,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "prompt": self.prompt,
            "entity_types": self.entity_types,
            "max_gleanings": self.max_gleanings,
            "strategy": self._values.strategy,
            **super().to_dict(),
        }
