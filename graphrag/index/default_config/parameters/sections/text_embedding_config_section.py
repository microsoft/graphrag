# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from typing import cast

from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_TARGET,
    DEFAULT_EMBEDDING_TYPE,
    DEFAULT_LLM_CONCURRENT_REQUESTS,
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_MAX_RETRY_WAIT,
    DEFAULT_LLM_REQUESTS_PER_MINUTE,
    DEFAULT_LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
    DEFAULT_LLM_TOKENS_PER_MINUTE,
)
from graphrag.index.default_config.parameters.models import (
    TextEmbeddingConfigModel,
    TextEmbeddingTarget,
)
from graphrag.index.verbs.text.embed import TextEmbedStrategyType

from .llm_config_section import LLMConfigModel, LLMConfigSection


class TextEmbeddingConfigSection(LLMConfigSection):
    """The default configuration section for TextEmbedding, loaded from environment variables."""

    _values: TextEmbeddingConfigModel
    _encoding_model: str
    _root: LLMConfigModel

    def __init__(
        self,
        values: TextEmbeddingConfigModel,
        root: LLMConfigModel,
        encoding_model: str,
        env: Env,
    ):
        """Create a new instance of the parameters class."""
        super().__init__(values, values, env)
        self._values = values
        self._env = env
        self._encoding_model = encoding_model
        self._root = root

    @property
    def llm(self) -> dict:
        """The embeddings LLM configuration to use."""
        root = self._root.llm.model_dump()
        opts: dict = self._values.llm.model_dump()
        opts = cast(
            dict,
            self.replace_dict({
                **{k: v for k, v in root.items() if v is not None},
                **{k: v for k, v in opts.items() if v is not None},
            }),
        )
        return {
            **opts,
            "api_key": self.readopt(opts, "api_key"),
            "type": self.readopt(opts, "type", DEFAULT_EMBEDDING_TYPE),
            "model": self.readopt(opts, "model", DEFAULT_EMBEDDING_MODEL),
            "encoding_model": opts.get("encoding_model", self._encoding_model),
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
    def batch_size(self) -> int:
        """The text embedding batch size."""
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
        # According to this embeddings reference, Azure limits us to 16 concurrent embeddings and 8191 tokens per request
        return self.replace(self._values.batch_size, DEFAULT_EMBEDDING_BATCH_SIZE)

    @property
    def batch_max_tokens(self) -> int:
        """The per-batch token limit of embeddings."""
        # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
        # According to this embeddings reference, Azure limits us to 16 concurrent embeddings and 8191 tokens per request
        return self.replace(
            self._values.batch_max_tokens, DEFAULT_EMBEDDING_BATCH_MAX_TOKENS
        )

    @property
    def target(self) -> TextEmbeddingTarget:
        """The target to use. 'all' or 'required'."""
        return self.replace(self._values.target, DEFAULT_EMBEDDING_TARGET)

    @property
    def skip(self) -> list[str]:
        """The specific embeddings to skip."""
        return self.replace(self._values.skip, [])

    @property
    def vector_store(self) -> dict | None:
        """The vector storage configuration."""
        return self.replace_dict(self._values.vector_store)

    @property
    def strategy(self) -> dict | None:
        """The embeddings strategy."""
        return self.replace_dict(self._values.strategy) or {
            "type": TextEmbedStrategyType.openai,
            "llm": self.llm,
            **self.parallelization,
            "batch_size": self.batch_size,
            "batch_max_tokens": self.batch_max_tokens,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            **super().to_dict(),
            "batch_size": self.batch_size,
            "batch_max_tokens": self.batch_max_tokens,
            "target": self.target,
            "skip": self.skip,
            "strategy": self._values.strategy,
            "vector_store": self._values.vector_store,
        }
