# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing fnllm model provider definitions."""

from typing import TYPE_CHECKING

from fnllm.openai import (
    create_openai_chat_llm,
    create_openai_client,
    create_openai_embeddings_llm,
)

from graphrag.config.models.language_model_config import (
    LanguageModelConfig,  # noqa: TC001
)
from graphrag.llm.providers.fnllm.events import FNLLMEvents
from graphrag.llm.providers.fnllm.utils import (
    _create_cache,
    _create_error_handler,
    _create_openai_config,
)

if TYPE_CHECKING:
    from fnllm.types import ChatLLM as FNLLMChatLLM
    from fnllm.types import EmbeddingsLLM as FNLLMEmbeddingLLM

    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks


class OpenAIChatFNLLM:
    llm: FNLLMChatLLM

    def __init__(
        self,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, False)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_chat_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    def chat(self, text: str, **kwargs: Any) -> str:
        pass


class OpenAIEmbeddingFNLLM:
    llm: FNLLMEmbeddingLLM

    def __init__(
        self,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, False)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_embeddings_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        pass


class AzureOpenAIChatFNLLM:
    llm: FNLLMChatLLM

    def __init__(
        self,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, True)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_chat_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    def chat(self, text: str, **kwargs: Any) -> str:
        pass


class AzureOpenAIEmbeddingFNLLM:
    llm: FNLLMEmbeddingLLM

    def __init__(
        self,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, True)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_embeddings_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        pass
