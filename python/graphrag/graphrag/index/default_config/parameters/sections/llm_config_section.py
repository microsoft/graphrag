# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from typing import Any, Generic, TypeVar, cast

from datashaper import AsyncType
from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_LLM_CONCURRENT_REQUESTS,
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_MAX_RETRY_WAIT,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_REQUEST_TIMEOUT,
    DEFAULT_LLM_REQUESTS_PER_MINUTE,
    DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
    DEFAULT_LLM_TOKENS_PER_MINUTE,
    DEFAULT_LLM_TYPE,
    DEFAULT_PARALLELIZATION_NUM_THREADS,
    DEFAULT_PARALLELIZATION_STAGGER,
)
from graphrag.index.default_config.parameters.models import (
    LLMConfigModel,
)

from .config_section import ConfigSection

TConfigSection = TypeVar("TConfigSection")


class LLMConfigSection(ConfigSection, Generic[TConfigSection]):
    """The default configuration section for LLM, loaded from environment variables."""

    _values: TConfigSection
    _root: LLMConfigModel
    _env: Env

    def __init__(self, values: TConfigSection, root: LLMConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values
        self._root = root
        self._env = env

    @property
    def llm(self) -> dict:
        """The LLM configuration to use."""
        root = self._root.llm.model_dump()
        section = cast(LLMConfigModel, self._values).llm.model_dump()
        opts = cast(
            dict,
            self.replace_dict({
                **{k: v for k, v in root.items() if v is not None},
                **{k: v for k, v in section.items() if v is not None},
            }),
        )
        return {
            **opts,
            "type": self.readopt(opts, "type", DEFAULT_LLM_TYPE),
            "model": self.readopt(opts, "model", DEFAULT_LLM_MODEL),
            "api_key": self.readopt(opts, "api_key"),
            "max_tokens": self.readopt(opts, "max_tokens", DEFAULT_LLM_MAX_TOKENS),
            # 3 minutes because translation can take forever some times.
            "request_timeout": self.readopt(
                opts, "request_timeout", DEFAULT_LLM_REQUEST_TIMEOUT
            ),
            "tokens_per_minute": self.readopt(
                opts, "tokens_per_minute", DEFAULT_LLM_TOKENS_PER_MINUTE
            ),
            "requests_per_minute": self.readopt(
                opts, "requests_per_minute", DEFAULT_LLM_REQUESTS_PER_MINUTE
            ),
            "max_retries": self.readopt(opts, "max_retries", DEFAULT_LLM_MAX_RETRIES),
            "max_retry_wait": self.readopt(
                opts, "max_retry_wait", DEFAULT_LLM_MAX_RETRY_WAIT
            ),
            "sleep_on_rate_limit_recommendation": self.readopt(
                opts,
                "sleep_on_rate_limit_recommendation",
                DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
            ),
            "concurrent_requests": self.readopt(
                opts, "concurrent_requests", DEFAULT_LLM_CONCURRENT_REQUESTS
            ),
        }

    @property
    def parallelization(self) -> dict[str, Any]:
        """The parallelization configuration to use for llm invocations."""
        root = self._root.parallelization.model_dump()
        section = cast(LLMConfigModel, self._values).parallelization.model_dump()
        opts = {
            **{k: v for k, v in root.items() if v is not None},
            **{k: v for k, v in section.items() if v is not None},
        }
        return {
            "stagger": self.readopt(opts, "stagger", DEFAULT_PARALLELIZATION_STAGGER),
            "num_threads": self.readopt(
                opts, "num_threads", DEFAULT_PARALLELIZATION_NUM_THREADS
            ),
        }

    @property
    def async_mode(self) -> AsyncType:
        """The async mode to use."""
        return self.replace(
            cast(LLMConfigModel, self._values).async_mode, AsyncType.Threaded
        )

    def to_dict(self) -> dict:
        """Return a JSON representation of the parameters."""
        return {
            "llm": self.llm,
            "parallelization": self.parallelization,
            "async_mode": self.async_mode,
        }
