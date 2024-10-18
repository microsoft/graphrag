# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import abc
import json
import os
import pathlib
import types
import typing

from . import (
    _config as _cfg,  # alias for _config attribute of Client class
    _search,
    types as _types,
)
from ._search._engine import _base_engine

_Response_T = typing.TypeVar('_Response_T')


class ContextManager(abc.ABC):
    """
    Abstract base class for managing context in synchronous operations.

    Provides an interface for the use of `with` statements to manage resources.
    Subclasses must implement the `__enter__` and `__exit__` methods.
    """

    @abc.abstractmethod
    def __enter__(self) -> typing.Self: ...

    @abc.abstractmethod
    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> typing.Literal[False]: ...


class AsyncContextManager(abc.ABC):
    """
    Abstract base class for managing context in asynchronous operations.

    Provides an interface for the use of `async with` statements to manage
    resources. Subclasses must implement the `__aenter__` and `__aexit__`
    methods.
    """

    @abc.abstractmethod
    async def __aenter__(self) -> typing.Self:
        """
        Enter the runtime context and return the context manager instance.

        Returns:
            The context manager instance.
        """
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> typing.Literal[False]:
        """
        Exit the runtime context.

        Args:
            exc_type: The exception type if an exception was raised.
            exc_value: The exception instance if an exception was raised.
            traceback: The traceback object if an exception was raised.

        Returns:
            Always returns False to indicate any exceptions should be
            propagated.
        """
        ...


class BaseClient(abc.ABC, typing.Generic[_Response_T]):
    """
    The base class for a GraphRAG client, responsible for managing
    configuration, local and global search engines, and interactions with large
    language models (LLMs).

    This class provides an abstract interface for interacting with the GraphRAG
    system. Subclasses must implement methods to load the configuration,
    initialize components, handle chat queries, and manage the lifecycle of the
    client.

    Attributes:
        _config: The configuration object for the GraphRAG system.
        _chat_llm: The language model used for handling chat queries.
        _embedding: The embedding model for vectorizing queries and context.
        _local_search_engine: The search engine for executing local searches.
        _global_search_engine: The search engine for executing global searches.
        _logger: An optional logger for recording internal events.
    """

    _config: _cfg.GraphRAGConfig
    _chat_llm: typing.Union[_search.ChatLLM, _search.AsyncChatLLM]
    _embedding: _search.Embedding
    _local_search_engine: typing.Union[_search.LocalSearchEngine, _search.AsyncLocalSearchEngine]
    _global_search_engine: typing.Union[_search.GlobalSearchEngine, _search.AsyncGlobalSearchEngine]
    _logger: typing.Optional[_base_engine.Logger]

    @classmethod
    @abc.abstractmethod
    def from_config_file(cls, config_file: typing.Union[os.PathLike[str], pathlib.Path]) -> typing.Self:
        """
        Initializes the client from a configuration file.

        Args:
            config_file: Path to the configuration file.

        Returns:
            An instance of the client initialized with the given configuration.
        """
        ...

    @classmethod
    @abc.abstractmethod
    def from_config_dict(cls, config_dict: typing.Dict[str, typing.Any]) -> typing.Self:
        """
        Initializes the client from a configuration dictionary.

        Args:
            config_dict: A dictionary containing configuration parameters.

        Returns:
            An instance of the client initialized with the given configuration.
        """
        ...

    @abc.abstractmethod
    def __init__(
        self,
        *,
        _config: _cfg.GraphRAGConfig,
        _logger: typing.Optional[_base_engine.Logger],
        **kwargs: typing.Any
    ) -> None:
        """
        Initializes the client with the given configuration and optional logger.

        Args:
            _config: The configuration for the client.
            _logger: An optional logger instance.
            **kwargs: Additional keyword arguments.
        """
        ...

    @abc.abstractmethod
    def chat(
        self,
        *,
        engine: typing.Literal['local', 'global'] = 'local',
        message: _types.MessageParam_T,
        stream: bool = False,
        verbose: bool = False,
        **kwargs: typing.Any
    ) -> _Response_T:
        """
        Perform a chat-based interaction using the specified engine (local or
        global).

        This method sends a message to the chat language model (LLM) and returns
        the response, either as a complete response or in a streaming format.

        Args:
            engine:
                Specifies whether to use the local or global search engine.
                Defaults to 'local'.
            message:
                An iterable of dictionaries representing the entire chat
                history, including the current message. Each dictionary must
                contain the following keys:
                - 'role': The role of the message sender, which can be 'user',
                          'assistant', 'system', 'tool', or 'function'.
                          Currently, 'system', 'tool', and 'function' roles are
                          not supported and will be ignored.
                - content: The actual content of the message.
            stream:
                If True, enables streaming mode to receive the response
                incrementally. Defaults to False.
            verbose: If True, returns a detailed response. Defaults to False.
            **kwargs: Additional arguments.

        Returns:
            The response from the LLM, either complete or streamed,
            based on the `stream` argument.
        """
        ...

    @staticmethod
    def _verify_message(message: _types.MessageParam_T) -> bool:
        """
        Verifies the structure of the chat message.

        Ensures that the roles alternate correctly between user and assistant,
        and that the last role is always 'user'. Also ensures that 'system'
        messages do not alternate.

        Args:
            message: The message to verify.

        Returns:
            True if the message structure is valid, False otherwise.
        """
        msg_list = [msg for msg in message]
        return (all(
            (msg_list[i]['role'] != msg_list[i + 1]['role'])
            for i in range(len(msg_list) - 1)  # check if the roles are alternating
        ) and msg_list[-1]['role'] == 'user')  # check if the last role is user

    @abc.abstractmethod
    def close(self) -> typing.Union[None, typing.Awaitable[None]]:
        """
        Closes the client and releases any resources.
        """
        ...

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{json.dumps(self._config.model_dump(), indent=4)}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
