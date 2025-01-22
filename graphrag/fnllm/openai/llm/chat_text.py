# Copyright (c) 2024 Microsoft Corporation.
"""The chat-based LLM implementation."""

from collections.abc import Iterator
from typing import Any, cast

from fnllm.base.base import BaseLLM
from fnllm.events.base import LLMEvents
from fnllm.openai.llm.services.history_extractor import OpenAIHistoryExtractor
from fnllm.openai.llm.services.usage_extractor import OpenAIUsageExtractor
from fnllm.openai.llm.utils import build_chat_messages
from fnllm.openai.types.aliases import OpenAIChatCompletionModel, OpenAIChatModel
from fnllm.openai.types.chat.io import (
    OpenAIChatCompletionInput,
    OpenAIChatHistoryEntry,
    OpenAIChatOutput,
)
from fnllm.openai.types.chat.parameters import OpenAIChatParameters
from fnllm.openai.types.client import OpenAIClient
from fnllm.services.cache_interactor import CacheInteractor
from fnllm.services.json import JsonHandler
from fnllm.services.rate_limiter import RateLimiter
from fnllm.services.retryer import Retryer
from fnllm.services.variable_injector import VariableInjector
from fnllm.types.generics import TJsonModel
from fnllm.types.io import LLMInput
from fnllm.types.metrics import LLMUsageMetrics
from langchain_core.messages import AIMessage
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from typing_extensions import Unpack

from graphrag.llm.others.factories import is_valid_llm_type, use_chat_llm

AIMessage.model_dump = AIMessage.to_json


class OpenAITextChatLLMImpl(
    BaseLLM[
        OpenAIChatCompletionInput,
        OpenAIChatOutput,
        OpenAIChatHistoryEntry,
        OpenAIChatParameters,
    ]
):
    """A chat-based LLM."""

    def __init__(
        self,
        client: OpenAIClient,
        model: str | OpenAIChatModel,
        cache: CacheInteractor,
        *,
        usage_extractor: OpenAIUsageExtractor[OpenAIChatOutput] | None = None,
        history_extractor: OpenAIHistoryExtractor | None = None,
        variable_injector: VariableInjector | None = None,
        rate_limiter: RateLimiter[
            OpenAIChatCompletionInput,
            OpenAIChatOutput,
            OpenAIChatHistoryEntry,
            OpenAIChatParameters,
        ]
        | None = None,
        retryer: Retryer[
            OpenAIChatCompletionInput,
            OpenAIChatOutput,
            OpenAIChatHistoryEntry,
            OpenAIChatParameters,
        ]
        | None = None,
        model_parameters: OpenAIChatParameters | None = None,
        events: LLMEvents | None = None,
        json_handler: JsonHandler[OpenAIChatOutput, OpenAIChatHistoryEntry]
        | None = None,
    ):
        """Create a new OpenAIChatLLM."""
        super().__init__(
            events=events,
            usage_extractor=usage_extractor,
            history_extractor=history_extractor,
            variable_injector=variable_injector,
            retryer=retryer,
            rate_limiter=rate_limiter,
            json_handler=json_handler,
        )
        self._client = client
        self._model = model
        self._global_model_parameters = model_parameters or {}
        self._cache = cache

    def child(self, name: str) -> Any:
        """Create a child LLM."""
        return OpenAITextChatLLMImpl(
            self._client,
            self._model,
            self._cache.child(name),
            events=self.events,
            usage_extractor=cast(
                "OpenAIUsageExtractor[OpenAIChatOutput]", self._usage_extractor
            ),
            history_extractor=cast("OpenAIHistoryExtractor", self._history_extractor),
            variable_injector=self._variable_injector,
            rate_limiter=self._rate_limiter,
            retryer=self._retryer,
            model_parameters=self._global_model_parameters,
            json_handler=self._json_handler,
        )

    def _build_completion_parameters(
        self, local_parameters: OpenAIChatParameters | None
    ) -> OpenAIChatParameters:
        params: OpenAIChatParameters = {
            "model": self._model,
            **self._global_model_parameters,
            **(local_parameters or {}),
        }
        return params

    async def _call_completion_or_cache(
        self,
        name: str | None,
        *,
        messages: list[OpenAIChatHistoryEntry],
        parameters: OpenAIChatParameters,
        bypass_cache: bool,
    ) -> OpenAIChatCompletionModel:
        def execute_llm():
            model = parameters.get("model", "")
            llm_type, *models = model.split(".")
            if is_valid_llm_type(llm_type):
                args = {**parameters, "model": ".".join(models)}
                chat_llm = use_chat_llm(llm_type, model=args["model"])
                return chat_llm.ainvoke(messages, **args)
            return self._client.chat.completions.create(
                messages=cast("Iterator[ChatCompletionMessageParam]", messages),
                **parameters,
            )

        # TODO: check if we need to remove max_tokens and n from the keys
        return await self._cache.get_or_insert(
            execute_llm,
            prefix=f"chat_{name}" if name else "chat",
            key_data={"messages": messages, "parameters": parameters},
            name=name,
            json_model=OpenAIChatCompletionModel,
            bypass_cache=bypass_cache,
        )

    async def _execute_llm(
        self,
        prompt: OpenAIChatCompletionInput,
        **kwargs: Unpack[
            LLMInput[TJsonModel, OpenAIChatHistoryEntry, OpenAIChatParameters]
        ],
    ) -> OpenAIChatOutput:
        name = kwargs.get("name")
        history = kwargs.get("history", [])
        bypass_cache = kwargs.get("bypass_cache", False)
        local_model_parameters = kwargs.get("model_parameters")
        messages, prompt_message = build_chat_messages(prompt, history)
        completion_parameters = self._build_completion_parameters(
            local_model_parameters
        )
        completion = await self._call_completion_or_cache(
            name,
            messages=messages,
            parameters=completion_parameters,
            bypass_cache=bypass_cache,
        )
        model = completion_parameters.get("model", "")
        llm_type, *_ = model.split(".")
        if is_valid_llm_type(llm_type):
            message = cast("AIMessage", completion)
            token_usage = (
                (
                    message.response_metadata
                    and message.response_metadata.get("token_usage")
                )
                or message.response_metadata.get("usage")
                or None
            )
            return OpenAIChatOutput(
                raw_input=prompt_message,
                raw_output=to_chat_completion_message(message),
                content=message.content,
                usage=LLMUsageMetrics(
                    input_tokens=(
                        token_usage.get("prompt_tokens")
                        or token_usage.get("input_tokens")
                    ),
                    output_tokens=(
                        token_usage.get("completion_tokens")
                        or token_usage.get("output_tokens")
                    ),
                )
                if token_usage
                else None,
            )
        response = completion.choices[0].message
        return OpenAIChatOutput(
            raw_input=prompt_message,
            raw_output=response,
            content=response.content,
            usage=LLMUsageMetrics(
                input_tokens=completion.usage.prompt_tokens,
                output_tokens=completion.usage.completion_tokens,
            )
            if completion.usage
            else None,
        )


def to_chat_completion_message(message: AIMessage) -> ChatCompletionMessage:
    return ChatCompletionMessage(
        content=message.content, role="assistant", tool_calls=message.tool_calls
    )
