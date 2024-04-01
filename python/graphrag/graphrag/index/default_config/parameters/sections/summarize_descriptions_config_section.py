#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
)
from graphrag.index.default_config.parameters.models import (
    LLMConfigModel,
    SummarizeDescriptionsConfigModel,
)
from graphrag.index.verbs.entities.summarize import SummarizeStrategyType

from .config_section import read_text_file
from .llm_config_section import LLMConfigSection


class SummarizeDescriptionsConfigSection(LLMConfigSection):
    """The default configuration section for SummarizeDescriptions, loaded from environment variables."""

    _values: SummarizeDescriptionsConfigModel
    _root_dir: str

    def __init__(
        self,
        values: SummarizeDescriptionsConfigModel,
        root: LLMConfigModel,
        root_dir: str,
        env: Env,
    ):
        """Create a new instance of the parameters class."""
        super().__init__(values, root, env)
        self._values = values
        self._root_dir = root_dir

    @property
    def prompt(self) -> str | None:
        """The summarize descriptions prompt to use."""
        file = self.replace(self._values.prompt)
        if file is not None:
            return read_text_file(self._root_dir, file)
        return None

    @property
    def max_length(self) -> int | None:
        """The description summarization maximum length."""
        return self.replace(
            self._values.max_length, DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH
        )

    @property
    def strategy(self) -> dict | None:
        """The override strategy to use."""
        return self.replace_dict(self._values.strategy) or {
            "type": SummarizeStrategyType.graph_intelligence,
            "llm": self.llm,
            "summarize_prompt": self.prompt,
            "max_summary_length": self.max_length,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "prompt": self.prompt,
            "max_length": self.max_length,
            "strategy": self._values.strategy,
            **super().to_dict(),
        }
