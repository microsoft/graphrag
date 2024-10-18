# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import abc
import typing

import openai
import typing_extensions

from . import _types


class BaseChatLLM(abc.ABC):
    """
    Abstract base class for synchronous chat-based LLMs. This class defines the
    core interface for interacting with a chat LLM in a synchronous manner,
    including methods for sending messages and retrieving responses.

    Attributes:
        _client: The OpenAI client instance used to communicate with the LLM.
    """
    _client: openai.OpenAI

    @property
    @abc.abstractmethod
    def model(self) -> str: ...

    @model.setter
    @abc.abstractmethod
    def model(self, value: str) -> None: ...

    @abc.abstractmethod
    def chat(
        self,
        msg: _types.MessageParam_T,
        *,
        stream: bool,
        **kwargs: typing.Any
    ) -> typing.Union[_types.ChatResponse_T, _types.SyncChatStreamResponse_T]:
        """
        Sends a message to the LLM and retrieves a response.

        Args:
            msg: The message payload to send to the LLM.
            stream: If True, enables streaming mode for the response.
            **kwargs: Additional keyword arguments for customization.

        Returns:
            A synchronous chat response, either as a single response or as a stream of responses.
        """
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """
        Closes any open connections or resources used by the LLM client.
        """
        ...

    @typing_extensions.override
    def __str__(self) -> str:
        return f"ChatLLM(model={self.model})"

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class BaseAsyncChatLLM(abc.ABC):
    """
    Abstract base class for asynchronous chat-based LLMs. This class defines the
    core interface for interacting with a chat LLM asynchronously, including
    methods for sending messages and retrieving responses.

    Attributes:
        _aclient:
            The asynchronous OpenAI client instance used to communicate with
            the LLM.
    """
    _aclient: openai.AsyncOpenAI

    @property
    @abc.abstractmethod
    def model(self) -> str: ...

    @model.setter
    @abc.abstractmethod
    def model(self, value: str) -> None: ...

    @abc.abstractmethod
    async def achat(
        self,
        msg: _types.MessageParam_T,
        *,
        stream: bool,
        **kwargs: typing.Any
    ) -> typing.Union[_types.ChatResponse_T, _types.AsyncChatStreamResponse_T]:
        """
        Sends a message to the LLM and asynchronously retrieves a response.

        Args:
            msg: The message payload to send to the LLM.
            stream: If True, enables streaming mode for the response.
            **kwargs: Additional keyword arguments for customization.

        Returns:
            An asynchronous chat response, either as a single response or as a
            stream of responses.
        """
        ...

    @abc.abstractmethod
    async def aclose(self) -> None:
        """
        Closes any open connections or resources used by the LLM client.
        """
        ...

    @typing_extensions.override
    def __str__(self) -> str:
        return f"AsyncChatLLM(model={self.model})"

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class BaseEmbedding(abc.ABC):
    """
    Abstract base class for synchronous embedding models. This class defines the
    interface for generating embeddings from text data in a synchronous manner.

    Attributes:
        _client: The OpenAI client instance used to generate embeddings.
    """
    _client: openai.OpenAI

    @property
    @abc.abstractmethod
    def model(self) -> str: ...

    @model.setter
    @abc.abstractmethod
    def model(self, value: str) -> None: ...

    @abc.abstractmethod
    def embed(self, text: str, **kwargs: typing.Any) -> _types.EmbeddingResponse_T:
        """
        Generates an embedding for the given text.

        Args:
            text: The text to embed.
            **kwargs: Additional keyword arguments.

        Returns:
            An EmbeddingResponse object containing the embedding data.
        """
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """
        Closes any open connections or resources used by the embedding client.
        """
        ...

    @typing_extensions.override
    def __str__(self) -> str:
        return f"Embedding(model={self.model})"

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class BaseAsyncEmbedding(abc.ABC):
    """
    Abstract base class for asynchronous embedding models. This class defines
    the interface for generating embeddings from text data asynchronously.

    Attributes:
        _aclient:
            The asynchronous OpenAI client instance used to generate embeddings.
    """
    _aclient: openai.AsyncOpenAI

    @property
    @abc.abstractmethod
    def model(self) -> str: ...

    @model.setter
    @abc.abstractmethod
    def model(self, value: str) -> None: ...

    @abc.abstractmethod
    async def aembed(self, text: str, **kwargs: typing.Any) -> _types.EmbeddingResponse_T:
        """
        Asynchronously generates an embedding for the given text.

        Args:
            text: The text to embed.
            **kwargs: Additional keyword arguments.

        Returns:
            An EmbeddingResponse object containing the embedding data.
        """
        ...

    @abc.abstractmethod
    async def aclose(self) -> None:
        """
        Closes any open connections or resources used by the asynchronous
        embedding client.
        """
        ...

    @typing_extensions.override
    def __str__(self) -> str:
        return f"AsyncEmbedding(model={self.model})"

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()
