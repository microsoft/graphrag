# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.config import PipelineReportingType
from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_REPORTING_BASE_DIR,
    DEFAULT_REPORTING_TYPE,
)
from graphrag.index.default_config.parameters.models import (
    ReportingConfigModel,
)

from .config_section import ConfigSection


class ReportingConfigSection(ConfigSection):
    """The default configuration section for Reporting, loaded from environment variables."""

    _values: ReportingConfigModel

    def __init__(self, values: ReportingConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def type(self) -> PipelineReportingType:
        """The reporting type to use."""
        return self.replace(self._values.type, DEFAULT_REPORTING_TYPE)

    @property
    def connection_string(self) -> str:
        """The reporting connection string to use."""
        return self.replace(self._values.connection_string)

    @property
    def container_name(self) -> str:
        """The reporting container name to use."""
        return self.replace(self._values.container_name)

    @property
    def base_dir(self) -> str:
        """The base directory for the reporting."""
        return self.replace(self._values.base_dir, DEFAULT_REPORTING_BASE_DIR)

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "type": self.type,
            "connection_string": self.connection_string,
            "container_name": self.container_name,
            "base_dir": self.base_dir,
        }
