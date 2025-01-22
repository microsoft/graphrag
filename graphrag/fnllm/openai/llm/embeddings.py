# Copyright (c) 2024 Microsoft Corporation.

"""The EmbeddingsLLM class."""

from typing import cast

from fnllm.base.base import BaseLLM
from fnllm.events.base import LLMEvents
from fnllm.openai.config import OpenAIConfig
from fnllm.openai.llm.services.usage_extractor import OpenAIUsageExtractor
from fnllm.openai.types.aliases import OpenAICreateEmbeddingResponseModel
from fnllm.openai.types.client import OpenAIClient
from fnllm.openai.types.embeddings.io import (
    OpenAIEmbeddingsInput,
    OpenAIEmbeddingsOutput,
)
from fnllm.openai.types.embeddings.parameters import OpenAIEmbeddingsParameters
from fnllm.services.cache_interactor import CacheInteractor
from fnllm.services.rate_limiter import RateLimiter
from fnllm.services.retryer import Retryer
from fnllm.services.variable_injector import VariableInjector
from fnllm.types.io import LLMInput
from fnllm.types.metrics import LLMUsageMetrics
from openai.types.embedding import Embedding
from pydantic import BaseModel
from typing_extensions import Unpack

from graphrag.llm.others.factories import is_valid_llm_type, use_embeddings


class Embeddings(BaseModel):
    values: list[list[float]]


class OpenAIEmbeddingsLLMImpl(
    BaseLLM[
        OpenAIEmbeddingsInput, OpenAIEmbeddingsOutput, None, OpenAIEmbeddingsParameters
    ],
):
    """A text-embedding generator LLM."""

    def __init__(
        self,
        config: OpenAIConfig,
        client: OpenAIClient,
        model: str,
        cache: CacheInteractor,
        *,
        usage_extractor: OpenAIUsageExtractor[OpenAIEmbeddingsOutput] | None = None,
        variable_injector: VariableInjector | None = None,
        rate_limiter: RateLimiter[
            OpenAIEmbeddingsInput,
            OpenAIEmbeddingsOutput,
            None,
            OpenAIEmbeddingsParameters,
        ]
        | None = None,
        retryer: Retryer[
            OpenAIEmbeddingsInput,
            OpenAIEmbeddingsOutput,
            None,
            OpenAIEmbeddingsParameters,
        ]
        | None = None,
        model_parameters: OpenAIEmbeddingsParameters | None = None,
        events: LLMEvents | None = None,
    ):
        """Create a new OpenAIEmbeddingsLLM."""
        super().__init__(
            events=events,
            usage_extractor=usage_extractor,
            variable_injector=variable_injector,
            rate_limiter=rate_limiter,
            retryer=retryer,
        )

        self._config = config
        self._client = client
        self._model = model
        self._cache = cache
        self._global_model_parameters = model_parameters or {}

    def child(self, name: str) -> "OpenAIEmbeddingsLLMImpl":
        """Create a child LLM."""
        return OpenAIEmbeddingsLLMImpl(
            self._client,
            self._model,
            self._cache.child(name),
            usage_extractor=cast(
                "OpenAIUsageExtractor[OpenAIEmbeddingsOutput]", self._usage_extractor
            ),
            variable_injector=self._variable_injector,
            rate_limiter=self._rate_limiter,
            retryer=self._retryer,
            model_parameters=self._global_model_parameters,
            events=self._events,
        )

    def _build_embeddings_parameters(
        self, local_parameters: OpenAIEmbeddingsParameters | None
    ) -> OpenAIEmbeddingsParameters:
        params: OpenAIEmbeddingsParameters = {
            "model": self._model,
            **self._global_model_parameters,
            **(local_parameters or {}),
        }

        return params

    async def _call_embeddings_or_cache(
        self,
        name: str | None,
        *,
        prompt: OpenAIEmbeddingsInput,
        parameters: OpenAIEmbeddingsParameters,
        bypass_cache: bool,
    ) -> OpenAICreateEmbeddingResponseModel:
        async def execute_llm():
            model = parameters.get("model", "")
            llm_type, *models = model.split(".")
            if is_valid_llm_type(llm_type):
                args = {**parameters, "model": ".".join(models)}
                embeddings_llm = use_embeddings(llm_type, **args)
                values = await embeddings_llm.aembed_documents(
                    [prompt] if isinstance(prompt, str) else prompt
                )
                return Embeddings(values=values)

            return await self._client.embeddings.create(
                input=prompt,
                **parameters,
            )

        # TODO: check if we need to remove max_tokens and n from the keys
        return await self._cache.get_or_insert(
            execute_llm,
            prefix=f"embeddings_{name}" if name else "embeddings",
            key_data={"input": prompt, "parameters": parameters},
            name=name,
            bypass_cache=bypass_cache,
            json_model=OpenAICreateEmbeddingResponseModel,
        )

    async def _execute_llm(
        self, prompt: OpenAIEmbeddingsInput, **kwargs: Unpack[LLMInput]
    ) -> OpenAIEmbeddingsOutput:
        name = kwargs.get("name")
        local_model_parameters = kwargs.get("model_parameters")
        bypass_cache = kwargs.get("bypass_cache", False)

        embeddings_parameters = self._build_embeddings_parameters(
            local_model_parameters
        )

        response = await self._call_embeddings_or_cache(
            name,
            prompt=prompt,
            parameters=embeddings_parameters,
            bypass_cache=bypass_cache,
        )

        model = embeddings_parameters.get("model", "")
        llm_type, *models = model.split(".")
        if is_valid_llm_type(llm_type):
            result = cast("Embeddings", response)
            embeddings = to_embeddings(result.values)
            return OpenAIEmbeddingsOutput(
                raw_input=prompt,
                raw_output=embeddings,
                embeddings=[d.embedding for d in embeddings],
                usage=None,
            )

        return OpenAIEmbeddingsOutput(
            raw_input=prompt,
            raw_output=response.data,
            embeddings=[d.embedding for d in response.data],
            usage=LLMUsageMetrics(
                input_tokens=response.usage.prompt_tokens,
            )
            if response.usage
            else None,
        )


def to_embeddings(values: list[list[float]]) -> list[Embedding]:
    return [
        Embedding(embedding=v, index=i, object="embedding")
        for i, v in enumerate(values)
    ]
