# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""OpenAI Wrappers for Orchestration."""

import logging
from typing import Any

from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from graphrag.query.llm.base import BaseLLMCallback
from graphrag.query.llm.oai.base import OpenAILLMImpl
from graphrag.query.llm.oai.typing import (
    OPENAI_RETRY_ERROR_TYPES,
    OpenaiApiType,
)

log = logging.getLogger(__name__)


class OpenAI(OpenAILLMImpl):
    """Wrapper for OpenAI Completion models."""

    def __init__(
        self,
        api_key: str,
        model: str,
        deployment_name: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        api_type: OpenaiApiType = OpenaiApiType.OpenAI,
        organization: str | None = None,
        max_retries: int = 10,
        retry_error_types: tuple[type[BaseException]] = OPENAI_RETRY_ERROR_TYPES,  # type: ignore
    ):
        self.api_key = api_key
        self.model = model
        self.deployment_name = deployment_name
        self.api_base = api_base
        self.api_version = api_version
        self.api_type = api_type
        self.organization = organization
        self.max_retries = max_retries
        self.retry_error_types = retry_error_types

    def generate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text."""
        try:
            retryer = Retrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(self.retry_error_types),
            )
            for attempt in retryer:
                with attempt:
                    return self._generate(
                        messages=messages,
                        streaming=streaming,
                        callbacks=callbacks,
                        **kwargs,
                    )
        except RetryError:
            log.exception("RetryError at generate(): %s")
            return ""
        else:
            # TODO: why not just throw in this case?
            return ""

    async def agenerate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate Text Asynchronously."""
        try:
            retryer = AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(self.retry_error_types),
            )
            async for attempt in retryer:
                with attempt:
                    return await self._agenerate(
                        messages=messages,
                        streaming=streaming,
                        callbacks=callbacks,
                        **kwargs,
                    )
        except RetryError:
            log.exception("Error at agenerate()")
            return ""
        else:
            # TODO: why not just throw in this case?
            return ""

    def _generate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        response = self.sync_client.chat.completions.create(  # type: ignore
            model=self.model,
            messages=messages,  # type: ignore
            stream=streaming,
            **kwargs,
        )  # type: ignore
        if streaming:
            full_response = ""
            while True:
                try:
                    chunk = response.__next__()  # type: ignore
                    if not chunk or not chunk.choices:
                        continue

                    delta = (
                        chunk.choices[0].delta.content
                        if chunk.choices[0].delta and chunk.choices[0].delta.content
                        else ""
                    )  # type: ignore

                    full_response += delta
                    if callbacks:
                        for callback in callbacks:
                            callback.on_llm_new_token(delta)
                    if chunk.choices[0].finish_reason == "stop":  # type: ignore
                        break
                except StopIteration:
                    break
            return full_response
        return response.choices[0].message.content or ""  # type: ignore

    async def _agenerate(
        self,
        messages: str | list[str],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        response = await self.async_client.chat.completions.create(  # type: ignore
            model=self.model,
            messages=messages,  # type: ignore
            stream=streaming,
            **kwargs,
        )
        if streaming:
            full_response = ""
            while True:
                try:
                    chunk = await response.__anext__()  # type: ignore
                    if not chunk or not chunk.choices:
                        continue

                    delta = (
                        chunk.choices[0].delta.content
                        if chunk.choices[0].delta and chunk.choices[0].delta.content
                        else ""
                    )  # type: ignore

                    full_response += delta
                    if callbacks:
                        for callback in callbacks:
                            callback.on_llm_new_token(delta)
                    if chunk.choices[0].finish_reason == "stop":  # type: ignore
                        break
                except StopIteration:
                    break
            return full_response
        return response.choices[0].message.content or ""  # type: ignore
