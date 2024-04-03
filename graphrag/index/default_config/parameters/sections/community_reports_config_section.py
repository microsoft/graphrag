# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH,
    DEFAULT_COMMUNITY_REPORT_MAX_LENGTH,
)
from graphrag.index.default_config.parameters.models import (
    CommunityReportsConfigModel,
    LLMConfigModel,
)
from graphrag.index.verbs.graph.report import CreateCommunityReportsStrategyType

from .config_section import read_text_file
from .llm_config_section import LLMConfigSection


class CommunityReportsConfigSection(LLMConfigSection):
    """The default configuration section for CommunityReports, loaded from environment variables."""

    _root_dir: str

    def __init__(
        self,
        values: CommunityReportsConfigModel,
        root: LLMConfigModel,
        root_dir: str,
        env: Env,
    ):
        """Create a new instance of the parameters class."""
        super().__init__(values, root, env)
        self._root_dir = root_dir

    @property
    def prompt(self) -> str | None:
        """The community report extraction prompt to use."""
        file = self.replace(self._values.prompt, None)
        if file is not None:
            return read_text_file(self._root_dir, file)
        return None

    @property
    def max_length(self) -> int | None:
        """The community report maximum length in tokens."""
        return self.replace(
            self._values.max_length, DEFAULT_COMMUNITY_REPORT_MAX_LENGTH
        )

    @property
    def max_input_length(self) -> int | None:
        """The community report maximum length in tokens."""
        return self.replace(
            self._values.max_length, DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH
        )

    @property
    def strategy(self) -> dict | None:
        """The override strategy to use."""
        return self.replace_dict(self._values.strategy) or {
            "type": CreateCommunityReportsStrategyType.graph_intelligence,
            "llm": self.llm,
            "extraction_prompt": self.prompt,
            "max_report_length": self.max_length,
            "max_input_length": self.max_input_length,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "prompt": self.prompt,
            "max_length": self.max_length,
            "strategy": self._values.strategy,
            **super().to_dict(),
        }
