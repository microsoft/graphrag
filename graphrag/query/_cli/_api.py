# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import collections
import sys
import types
import typing

import typing_extensions

from . import _utils
from .. import (
    _base_client,
    _client,
    _config,
    types as _types,
)
from .._search import _types as _search_types


class GraphRAGCli(_base_client.ContextManager):
    """
    Synchronous Command Line Interface (CLI) client for interacting with the
    GraphRAG system.

    This class allows users to interact with the GraphRAG system via the command
    line in a synchronous manner. It manages conversation history, handles user
    messages, and outputs assistant responses to the console. It integrates with
    the `GraphRAGClient` to perform local or global searches based on user
    input.

    Attributes:
        _verbose: A boolean indicating whether verbose logging is enabled.
        _engine: Specifies the search engine to use ('local' or 'global').
        _stream: A boolean indicating whether to use streaming responses.
        _conversation_history:
            A deque storing the conversation history with a maximum length.
        _graphrag_client:
            An instance of `GraphRAGClient` used to interact with the GraphRAG
            system.
    """
    _verbose: bool
    _engine: typing.Literal['local', 'global']
    _stream: bool
    _conversation_history: typing.Deque[typing.Dict[typing.Literal['role', 'content'], str]]
    _graphrag_client: _client.GraphRAGClient

    @property
    def stream(self) -> bool:
        return self._stream

    def __init__(
        self,
        *,
        verbose: bool,
        chat_llm_base_url: typing.Optional[str],
        chat_llm_api_key: str,
        chat_llm_model: str,
        embedding_base_url: typing.Optional[str],
        embedding_api_key: str,
        embedding_model: str,
        context_dir: str,
        engine: typing.Literal['local', 'global'],
        stream: bool,
    ):
        """
        Initializes the GraphRAGCli with the provided configuration and parameters.

        Args:
            verbose: If True, enables verbose logging.
            chat_llm_base_url: Optional base URL for the chat language model API.
            chat_llm_api_key: API key for the chat language model.
            chat_llm_model: Name of the chat language model to use.
            embedding_base_url: Optional base URL for the embedding model API.
            embedding_api_key: API key for the embedding model.
            embedding_model: Name of the embedding model to use.
            context_dir: Directory path where context data files are stored.
            engine: Specifies whether to use the 'local' or 'global' search engine.
            stream: If True, enables streaming mode for responses.
        """
        self._verbose = verbose
        self._engine = engine
        self._stream = stream
        self._conversation_history = collections.deque(maxlen=30)
        self._logger = _utils.CLILogger()

        self._graphrag_client = _client.GraphRAGClient(
            config=_config.GraphRAGConfig(
                chat_llm=_config.ChatLLMConfig(
                    base_url=chat_llm_base_url,
                    api_key=chat_llm_api_key,
                    model=chat_llm_model,
                ),
                embedding=_config.EmbeddingConfig(
                    base_url=embedding_base_url,
                    api_key=embedding_api_key,
                    model=embedding_model,
                ),
                context=_config.ContextConfig(
                    directory=context_dir,
                ),
                logging=_config.LoggingConfig(
                    enabled=verbose,
                ),
            ),
            logger=self._logger,
        )

    def chat(self, message: str, **kwargs: typing.Any) -> typing.Union[typing.Iterator[str], str]:
        """
        Sends a message to the assistant and returns the assistant's response.

        Args:
            message: The user's input message to send to the assistant.
            **kwargs: Additional keyword arguments.

        Returns:
            The assistant's response. If streaming is enabled, returns an
            iterator over response chunks; otherwise, returns the full response
            string.
        """
        self._conversation_history.append({'role': 'user', 'content': message})
        response = self._graphrag_client.chat(
            engine=self._engine,
            message=typing.cast(_types.MessageParam_T, self._conversation_history),
            stream=self._stream,
            **kwargs,
        )
        if self._stream:
            response = typing.cast(_search_types.StreamSearchResult_T, response)
            return self._parse_stream_response(response)
        else:
            response = typing.cast(_search_types.SearchResult_T, response)
            return self._parse_response(response)

    def clear_history(self) -> None:
        """
        Clears the conversation history.
        """
        self._conversation_history.clear()

    def _parse_stream_response(self, response: _search_types.StreamSearchResult_T) -> typing.Iterator[str]:
        """
        Parses a streaming response from the assistant and yields response
        chunks.

        Args:
            response: The streaming response object from the assistant.

        Yields:
            Chunks of the assistant's response as they are received.
        """
        content = ''
        response = typing.cast(_search_types.StreamSearchResult_T, response)
        for chunk in response:
            sys.stdout.write(chunk.choice.delta.content or '')
            sys.stdout.flush()
            yield chunk.choice.delta.content or ''
            content += chunk.choice.delta.content or ''
        sys.stdout.write('\n')
        sys.stdout.flush()
        self._conversation_history.append({'role': 'assistant', 'content': content})

    def _parse_response(self, response: _search_types.SearchResult_T) -> str:
        """
        Parses a complete response from the assistant and returns it.

        Args:
            response: The complete response object from the assistant.

        Returns:
            The assistant's response as a string.
        """
        response = typing.cast(_search_types.SearchResult_T, response)
        sys.stdout.write(str(response.choice.message.content) or '')
        sys.stdout.write('\n')
        sys.stdout.flush()
        self._conversation_history.append({'role': 'assistant', 'content': str(response.choice.message.content)})
        return str(response.choice.message.content)

    def close(self) -> None:
        """
        Closes the underlying GraphRAG client and releases resources.
        """
        self._graphrag_client.close()

    def conversation_history(self) -> typing.List[typing.Dict[typing.Literal['role', 'content'], str]]:
        """
        Retrieves the current conversation history.

        Returns:
            The conversation history as a list of message dictionaries.
        """
        return list(self._conversation_history)

    @typing_extensions.override
    def __enter__(self) -> GraphRAGCli:
        return self

    @typing_extensions.override
    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> typing.Literal[False]:
        self.close()
        return False

    @typing_extensions.override
    def __str__(self):
        return str(self._graphrag_client)

    @typing_extensions.override
    def __repr__(self):
        return repr(self._graphrag_client)


class AsyncGraphRAGCli(_base_client.AsyncContextManager):
    """
    Asynchronous Command Line Interface (CLI) client for interacting with the
    GraphRAG system.

    This class allows users to interact with the GraphRAG system via the command
    line in an asynchronous manner. It manages conversation history, handles
    user messages, and outputs assistant responses to the console. It integrates
    with the `AsyncGraphRAGClient` to perform local or global searches based on
    user input.

    Attributes:
        _verbose: A boolean indicating whether verbose logging is enabled.
        _engine: Specifies the search engine to use ('local' or 'global').
        _stream: A boolean indicating whether to use streaming responses.
        _conversation_history:
            A deque storing the conversation history with a maximum length.
        _graphrag_client:
            An instance of `AsyncGraphRAGClient` used to interact with the
            GraphRAG system.
    """
    _verbose: bool
    _engine: typing.Literal['local', 'global']
    _stream: bool
    _conversation_history: typing.Deque[typing.Dict[typing.Literal['role', 'content'], str]]
    _graphrag_client: _client.AsyncGraphRAGClient

    def __init__(
        self,
        *,
        verbose: bool,
        chat_llm_base_url: typing.Optional[str],
        chat_llm_api_key: str,
        chat_llm_model: str,
        embedding_base_url: typing.Optional[str],
        embedding_api_key: str,
        embedding_model: str,
        context_dir: str,
        engine: typing.Literal['local', 'global'],
        stream: bool,
    ):
        """
        Initializes the AsyncGraphRAGCli with the provided configuration and
        parameters.

        Args:
            verbose: If True, enables verbose logging.
            chat_llm_base_url:
                Optional base URL for the chat language model API.
            chat_llm_api_key: API key for the chat language model.
            chat_llm_model: Name of the chat language model to use.
            embedding_base_url: Optional base URL for the embedding model API.
            embedding_api_key: API key for the embedding model.
            embedding_model: Name of the embedding model to use.
            context_dir: Directory path where context data files are stored.
            engine:
                Specifies whether to use the 'local' or 'global' search engine.
            stream: If True, enables streaming mode for responses.
        """
        self._verbose = verbose
        self._engine = engine
        self._stream = stream
        self._conversation_history = collections.deque(maxlen=10)  # only keep the last 10 messages
        self._logger = _utils.CLILogger()
        self._graphrag_client = _client.AsyncGraphRAGClient(
            config=_config.GraphRAGConfig(
                chat_llm=_config.ChatLLMConfig(
                    base_url=chat_llm_base_url,
                    api_key=chat_llm_api_key,
                    model=chat_llm_model,
                ),
                embedding=_config.EmbeddingConfig(
                    base_url=embedding_base_url,
                    api_key=embedding_api_key,
                    model=embedding_model,
                ),
                context=_config.ContextConfig(
                    directory=context_dir,
                ),
                logging=_config.LoggingConfig(
                    enabled=verbose,
                ),
            ),
            logger=self._logger,
        )

    async def chat(self, message: str, **kwargs: typing.Any) -> None:
        """
        Asynchronously sends a message to the assistant and outputs the
        assistant's response.

        Args:
            message: The user's input message to send to the assistant.
            **kwargs: Additional keyword arguments to pass to the chat method.
        """
        self._conversation_history.append({'role': 'user', 'content': message})
        response = await self._graphrag_client.chat(
            engine=self._engine,
            message=typing.cast(_types.MessageParam_T, self._conversation_history),
            stream=self._stream,
            **kwargs,
        )
        if self._stream:
            content = ''
            response = typing.cast(_search_types.AsyncStreamSearchResult_T, response)
            async for chunk in response:
                sys.stdout.write(chunk.choice.delta.content or '')
                sys.stdout.flush()
                content += chunk.choice.delta.content or ''
            sys.stdout.write('\n')
            sys.stdout.flush()
            self._conversation_history.append({'role': 'assistant', 'content': content})
        else:
            response = typing.cast(_search_types.SearchResult_T, response)
            sys.stdout.write(str(response.choice.message.content) or '')
            sys.stdout.write('\n')
            sys.stdout.flush()
            self._conversation_history.append({'role': 'assistant', 'content': str(response.choice.message.content)})

    async def close(self) -> None:
        """
        Asynchronously closes the underlying GraphRAG client and releases
        resources.
        """
        await self._graphrag_client.close()

    @typing_extensions.override
    async def __aenter__(self) -> AsyncGraphRAGCli:
        return self

    @typing_extensions.override
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> typing.Literal[False]:
        await self.close()
        return False

    @typing_extensions.override
    def __str__(self):
        return str(self._graphrag_client)

    @typing_extensions.override
    def __repr__(self):
        return repr(self._graphrag_client)
