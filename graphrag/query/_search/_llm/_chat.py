# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import httpx
import openai
import typing_extensions

from . import _base_llm, _types
from ... import _utils, errors as _errors


class ChatLLM(_base_llm.BaseChatLLM):
    """
    Synchronous implementation of a chat-based large language model (LLM) using
    the OpenAI API.

    This class provides methods for interacting with OpenAI's chat completion
    API in a synchronous manner. It handles sending messages and receiving
    responses, including support for message streaming.

    Attributes:
        _model: The model identifier for the chat LLM.
        _client: The OpenAI client instance used to communicate with the LLM.
    """

    _model: str
    _client: openai.OpenAI

    @property
    @typing_extensions.override
    def model(self) -> str:
        return self._model

    @model.setter
    @typing_extensions.override
    def model(self, value: str) -> None:
        self._model = value

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        organization: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        timeout: typing.Optional[float] = None,
        max_retries: typing.Optional[int] = None,
        http_client: typing.Optional[httpx.Client] = None,
        **kwargs: typing.Any
    ) -> None:
        """
        Initializes the ChatLLM with the specified model and OpenAI API settings.

        Args:
            model: The model identifier to use for chat completions.
            api_key: The API key for authenticating with the OpenAI API.
            organization: Optional. The organization ID for the OpenAI API.
            base_url: Optional. The base URL for the OpenAI API.
            timeout: Optional. The request timeout in seconds.
            max_retries:
                Optional. The maximum number of retries for failed requests.
            http_client:
                Optional. The HTTP client to use for making synchronous requests.
            **kwargs: Additional keyword arguments for `openai.OpenAI`.
        """
        self._client = openai.OpenAI(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries or 3,
            http_client=http_client,
            **_utils.filter_kwargs(openai.OpenAI, kwargs)
        )
        self._model = model

    @typing_extensions.override
    def chat(
        self,
        msg: _types.MessageParam_T,
        *,
        stream: bool = False,
        **kwargs: typing.Any
    ) -> typing.Union[_types.ChatResponse_T, _types.SyncChatStreamResponse_T]:
        """
        Sends a chat message to the OpenAI API and retrieves a response.

        Args:
            msg: The message payload to send to the LLM.
            stream: If True, enables streaming mode for the response.
            **kwargs:
                Additional keyword arguments for
                `openai.OpenAI.chat.completions.create`.

        Returns:
            A synchronous chat response, either as a single response or a stream
            of responses.

        Raises:
            OpenAIAPIError: If openai.APIError occurs while sending the message.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=msg,
                stream=stream,
                **_utils.filter_kwargs(self._client.chat.completions.create, kwargs)
            )
        except openai.APIError as e:
            raise _errors.OpenAIAPIError(e) from e
        return typing.cast(_types.ChatCompletion, response) \
            if not stream else (typing.cast(_types.ChatCompletionChunk, c) for c in response)

    @typing_extensions.override
    def close(self) -> None:
        self._client.close()


class AsyncChatLLM(_base_llm.BaseAsyncChatLLM):
    """
    Asynchronous implementation of a chat-based large language model (LLM) using
    the OpenAI API.

    This class provides methods for interacting with OpenAI's chat completion
    API asynchronously. It supports sending messages and receiving responses,
    with optional streaming for chat responses.

    Attributes:
        _model: The model identifier for the chat LLM.
        _aclient:
            The asynchronous OpenAI client instance used to communicate with
            the LLM.
    """

    @property
    @typing_extensions.override
    def model(self) -> str:
        return self._model

    @model.setter
    @typing_extensions.override
    def model(self, value: str) -> None:
        self._model = value

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        organization: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        timeout: typing.Optional[float] = None,
        max_retries: typing.Optional[int] = None,
        http_client: typing.Optional[httpx.AsyncClient] = None,
        **kwargs: typing.Any
    ) -> None:
        """
        Initializes the AsyncChatLLM with the specified model and OpenAI API
        settings.

        Args:
            model: The model identifier to use for chat completions.
            api_key: The API key for authenticating with the OpenAI API.
            organization: Optional. The organization ID for the OpenAI API.
            base_url: Optional. The base URL for the OpenAI API.
            timeout: Optional. The request timeout in seconds.
            max_retries:
                Optional. The maximum number of retries for failed requests.
            http_client:
                Optional. The HTTP client to use for making asynchronous
                requests.
            **kwargs: Additional keyword arguments for `openai.AsyncOpenAI`.
        """
        self._aclient = openai.AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries or 3,
            http_client=http_client,
            **_utils.filter_kwargs(openai.AsyncOpenAI, kwargs)
        )
        self._model = model

    @typing_extensions.override
    async def achat(
        self,
        msg: _types.MessageParam_T,
        *,
        stream: bool = False,
        **kwargs: typing.Any
    ) -> typing.Union[_types.ChatResponse_T, _types.AsyncChatStreamResponse_T]:
        """
        Asynchronously sends a chat message to the OpenAI API and retrieves a
        response.

        Args:
            msg: The message payload to send to the LLM.
            stream: If True, enables streaming mode for the response.
            **kwargs:
                Additional keyword arguments for
                `openai.AsyncOpenAI.chat.completions.create`.

        Returns:
            An asynchronous chat response, either as a single response or a
            stream of responses.

        Raises:
            OpenAIAPIError: If openai.APIError occurs while sending the message.
        """
        try:
            response = await self._aclient.chat.completions.create(
                model=self._model,
                messages=msg,
                stream=stream,
                **_utils.filter_kwargs(self._aclient.chat.completions.create, kwargs)
            )
        except openai.APIError as e:
            raise _errors.OpenAIAPIError(e) from e

        return typing.cast(_types.ChatCompletion, response) if not stream else (
            c async for c in typing.cast(_types.AsyncChatStreamResponse_T, response)
        )

    @typing_extensions.override
    async def aclose(self) -> None:
        await self._aclient.close()
