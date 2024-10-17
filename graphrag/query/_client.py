# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import os
import pathlib
import types
import typing

import tiktoken
import typing_extensions

from . import (
    _base_client,
    _config as _cfg,  # alias for _config attribute of Client class
    _defaults,
    _search,
    errors as _errors,
    types as _types,
)
from ._search._engine import _base_engine

__all__ = [
    'GraphRAGClient',
    'AsyncGraphRAGClient',
]


class GraphRAGClient(
    _base_client.BaseClient[typing.Union[_types.Response_T, _types.StreamResponse_T]],
    _base_client.ContextManager,
):
    """
    Synchronous client for interacting with the GraphRAG system.

    This class integrates configuration, local and global search engines, and
    logging to perform the entire GraphRAG lifecycle. It allows users to execute
    chat-based interactions using either local or global search strategies,
    manage resources, and handle logging.

    Attributes:
        _config: The configuration object for the GraphRAG system.
        _chat_llm: The synchronous language model used for chat interactions.
        _embedding: The embedding model used for handling entity embeddings.
        _local_search_engine: The search engine for performing local searches.
        _global_search_engine: The search engine for performing global searches.
        _logger:
            Optional logger for recording internal events and debugging
            information.
    """
    _config: _cfg.GraphRAGConfig
    _chat_llm: _search.ChatLLM
    _embedding: _search.Embedding
    _local_search_engine: _search.LocalSearchEngine
    _global_search_engine: _search.GlobalSearchEngine
    _logger: typing.Optional[_base_engine.Logger]

    @property
    def logger(self) -> typing.Optional[_base_engine.Logger]:
        return self._logger

    @logger.setter
    def logger(self, logger: _base_engine.Logger) -> None:
        self._logger = logger

    @classmethod
    @typing_extensions.override
    def from_config_file(cls, config_file: typing.Union[os.PathLike[str], pathlib.Path, str]) -> typing.Self:
        """Initialize client from a config file (JSON, YAML, TOML)."""
        return cls(config=_cfg.GraphRAGConfig.from_config_file(config_file))

    @classmethod
    @typing_extensions.override
    def from_config_dict(cls, config_dict: typing.Dict[str, typing.Any]) -> typing.Self:
        """Initialize client from a configuration dictionary."""
        return cls(config=_cfg.GraphRAGConfig(**config_dict))

    def __init__(
        self,
        *,
        config: _cfg.GraphRAGConfig,
        logger: typing.Optional[_base_engine.Logger] = None,
    ) -> None:
        """
        Initializes the GraphRAGClient with the given configuration and logger.

        Args:
            config: The configuration object for the GraphRAG system.
            logger:
                Optional logger for logging client events. If not provided, a
                default logger will be created based on the configuration
                settings.
        """
        self._config = config
        self._logger = logger or _defaults.get_default_logger(
            level=self._config.logging.level,
            fmt=self._config.logging.format,
            out_file=self._config.logging.out_file,
            err_file=self._config.logging.err_file,
            rotation=self._config.logging.rotation,
            retention=self._config.logging.retention,
            serialize=self._config.logging.serialize,
        ) if self._config.logging.enabled else None

        # Initialize LLMs
        if self._logger:
            self._logger.info(f'Initializing the ChatLLM with model: {self._config.chat_llm.model}')
        self._chat_llm = _search.ChatLLM(
            model=self._config.chat_llm.model,
            api_key=self._config.chat_llm.api_key,
            organization=self._config.chat_llm.organization,
            base_url=self._config.chat_llm.base_url,
            timeout=self._config.chat_llm.timeout,
            max_retries=self._config.chat_llm.max_retries,
            **(self._config.chat_llm.kwargs or {}),
        )

        if self._logger:
            self._logger.info(f'Initializing the Embedding with model: {self._config.embedding.model}')
        self._embedding = _search.Embedding(
            model=self._config.embedding.model,
            api_key=self._config.embedding.api_key,
            organization=self._config.embedding.organization,
            base_url=self._config.embedding.base_url,
            timeout=self._config.embedding.timeout,
            max_retries=self._config.embedding.max_retries,
            max_tokens=self._config.embedding.max_tokens,
            token_encoder=tiktoken.get_encoding(
                self._config.embedding.token_encoder
            )
            if self._config.embedding.token_encoder
            else None,
            **(self._config.embedding.kwargs or {}),
        )

        # Initialize ContextLoader objects
        if self._logger:
            self._logger.info(f'Initializing the LocalContextLoader with directory: {self._config.context.directory}')
        local_context_loader = _search.LocalContextLoader.from_parquet_directory(
            self._config.context.directory,
            **(self._config.context.kwargs or {}),
        )

        if self._logger:
            self._logger.info(f'Initializing the GlobalContextLoader with directory: {self._config.context.directory}')

        # Initialize search engines
        if self._logger:
            self._logger.info('Initializing the LocalSearchEngine')
        self._local_search_engine = _search.LocalSearchEngine(
            chat_llm=self._chat_llm,
            embedding=self._embedding,
            context_loader=local_context_loader,
            sys_prompt=self._config.local_search.sys_prompt,
            community_level=self._config.local_search.community_level,
            store_coll_name=self._config.local_search.store_coll_name,
            store_uri=self._config.local_search.store_uri,
            encoding_model=self._config.local_search.encoding_model,
            logger=self._logger,
            **(self._config.local_search.kwargs or {}),
        )
        if self._logger:
            self._logger.debug(f'LocalSearchEngine initialized: {self._local_search_engine}')
            self._logger.info('Initializing the GlobalSearchEngine')
        self._global_search_engine = _search.GlobalSearchEngine(
            chat_llm=self._chat_llm,
            embedding=self._embedding,
            context_builder=_search.GlobalContextBuilder.from_local_context_builder(
                self._local_search_engine.context_builder
            ),
            map_sys_prompt=self._config.global_search.map_sys_prompt,
            reduce_sys_prompt=self._config.global_search.reduce_sys_prompt,
            allow_general_knowledge=self._config.global_search.allow_general_knowledge,
            general_knowledge_sys_prompt=self._config.global_search.general_knowledge_sys_prompt,
            no_data_answer=self._config.global_search.no_data_answer,
            json_mode=self._config.global_search.json_mode,
            max_data_tokens=self._config.global_search.max_data_tokens,
            community_level=self._config.global_search.community_level,
            encoding_model=self._config.global_search.encoding_model,
            logger=self._logger,
            **(self._config.global_search.kwargs or {}),
        )
        if self._logger:
            self._logger.debug(f'GlobalSearchEngine initialized: {self._global_search_engine}')

    @typing_extensions.override
    def chat(
        self,
        *,
        engine: typing.Literal['local', 'global'] = 'local',
        message: _types.MessageParam_T,
        stream: bool = False,
        verbose: bool = False,
        **kwargs: typing.Any
    ) -> typing.Union[_types.Response_T, _types.StreamResponse_T]:
        """
        Performs a chat-based interaction using the specified search engine
        (local or global).

        Args:
            engine:
                Specifies whether to use the local or global search engine.
                Defaults to 'local'.
            message:
                An iterable of dictionaries representing the entire chat history
                and the current message.
                Each dictionary must contain the following keys:
                - 'role': The role of the message sender, which can be 'user',
                          'assistant', 'system', 'tool', or 'function'.
                          Currently, 'system', 'tool', and 'function' roles are
                          not supported and will be ignored.
                - 'content': The actual content of the message.
            stream:
                If True, enables streaming mode to receive the response
                incrementally. Defaults to False.
            verbose:
                If True, returns a detailed response with additional
                information. Recommended to be False in production environments.
                Defaults to False.
            **kwargs: Additional arguments.

        Returns:
            The response from the LLM, either complete or streamed, based on the
            `stream` argument.

        Raises:
            InvalidMessageError: If the message format is invalid.
            InvalidEngineError: If the specified engine is not recognized.
        """
        # TODO: Add support for system, function, and tool roles
        message = [msg for msg in message if msg['role'] not in ['system', 'function', 'tool']]
        if not self._verify_message(message):
            if self._logger:
                self._logger.error(f'Invalid message: {message}')
            raise _errors.InvalidMessageError()

        # Convert iterable objects to list
        msg_list = [typing.cast(typing.Dict[typing.Literal["role", "content"], str], msg) for msg in message]
        conversation_history = _search.ConversationHistory.from_list(msg_list[:-1])  # exclude the last message
        if engine == 'local':
            if self._logger:
                self._logger.info(f'Local search with message: {msg_list[-1]["content"]}')
            response = self._local_search_engine.search(
                msg_list[-1]['content'],
                conversation_history=conversation_history,
                stream=stream,
                verbose=verbose,
                **kwargs
            )
        elif engine == 'global':
            if self._logger:
                self._logger.info(f'Global search with message: {msg_list[-1]["content"]}')
            response = self._global_search_engine.search(
                msg_list[-1]['content'],
                conversation_history=conversation_history,
                stream=stream,
                verbose=verbose,
                **kwargs
            )
        else:
            raise _errors.InvalidEngineError(engine)

        return response

    @typing_extensions.override
    def close(self) -> None:
        """
        Closes the client and releases any resources held by the search engines
        and language models.
        """
        self._local_search_engine.close()
        self._global_search_engine.close()

    # Support for context manager
    @typing_extensions.override
    def __enter__(self) -> typing.Self:
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


class AsyncGraphRAGClient(
    _base_client.BaseClient[typing.Awaitable[typing.Union[_types.Response_T, _types.AsyncStreamResponse_T]]],
    _base_client.AsyncContextManager,
):
    """
    Asynchronous client for interacting with the GraphRAG system.

    This class provides an asynchronous implementation for integrating
    configuration, local and global search engines, and logging to perform the
    entire GraphRAG lifecycle. It allows users to execute chat-based
    interactions asynchronously using either local or global search strategies,
    manage resources, and handle logging.

    Attributes:
        _config: The configuration object for the GraphRAG system.
        _chat_llm: The asynchronous language model used for chat interactions.
        _embedding: The embedding model used for handling entity embeddings.
        _local_search_engine:
            The search engine for performing local searches asynchronously.
        _global_search_engine:
            The search engine for performing global searches asynchronously.
        _logger:
            Optional logger for recording internal events and debugging
            information.
    """
    _config: _cfg.GraphRAGConfig
    _chat_llm: _search.AsyncChatLLM
    _embedding: _search.Embedding
    _local_search_engine: _search.AsyncLocalSearchEngine
    _global_search_engine: _search.AsyncGlobalSearchEngine
    _logger: typing.Optional[_base_engine.Logger]

    @property
    def logger(self) -> typing.Optional[_base_engine.Logger]:
        return self._logger

    @logger.setter
    def logger(self, logger: _base_engine.Logger) -> None:
        self._logger = logger

    @classmethod
    @typing_extensions.override
    def from_config_file(cls, config_file: typing.Union[os.PathLike[str], pathlib.Path, str]) -> typing.Self:
        return cls(config=_cfg.GraphRAGConfig.from_config_file(config_file))

    @classmethod
    @typing_extensions.override
    def from_config_dict(cls, config_dict: typing.Dict[str, typing.Any]) -> typing.Self:
        return cls(config=_cfg.GraphRAGConfig(**config_dict))

    def __init__(
        self,
        *,
        config: _cfg.GraphRAGConfig,
        logger: typing.Optional[_base_engine.Logger] = None,
    ) -> None:
        """
        Initializes the AsyncGraphRAGClient with the given configuration and
        logger.

        Args:
            config: The configuration object for the GraphRAG system.
            logger:
                Optional logger for logging client events. If not provided, a
                default logger will be created based on the configuration
                settings.
        """
        self._config = config
        self._logger = logger or _defaults.get_default_logger(
            level=self._config.logging.level,
            fmt=self._config.logging.format,
            out_file=self._config.logging.out_file,
            err_file=self._config.logging.err_file,
            rotation=self._config.logging.rotation,
            retention=self._config.logging.retention,
            serialize=self._config.logging.serialize,
        ) if self._config.logging.enabled else None

        if self._logger:
            self._logger.info(f'Initializing the AsyncChatLLM with model: {self._config.chat_llm.model}')

        self._chat_llm = _search.AsyncChatLLM(
            model=self._config.chat_llm.model,
            api_key=self._config.chat_llm.api_key,
            organization=self._config.chat_llm.organization,
            base_url=self._config.chat_llm.base_url,
            timeout=self._config.chat_llm.timeout,
            max_retries=self._config.chat_llm.max_retries,
            **(self._config.chat_llm.kwargs or {}),
        )

        if self._logger:
            self._logger.info(f'Initializing the Embedding with model: {self._config.embedding.model}')

        self._embedding = _search.Embedding(
            model=self._config.embedding.model,
            api_key=self._config.embedding.api_key,
            organization=self._config.embedding.organization,
            base_url=self._config.embedding.base_url,
            timeout=self._config.embedding.timeout,
            max_retries=self._config.embedding.max_retries,
            max_tokens=self._config.embedding.max_tokens,
            token_encoder=tiktoken.get_encoding(
                self._config.embedding.token_encoder
            )
            if self._config.embedding.token_encoder
            else None,
            **(self._config.embedding.kwargs or {}),
        )

        if self._logger:
            self._logger.info(f'Initializing the LocalContextLoader with directory: {self._config.context.directory}')
        local_context_loader = _search.LocalContextLoader.from_parquet_directory(
            self._config.context.directory,
            **(self._config.context.kwargs or {}),
        )

        if self._logger:
            self._logger.info('Initializing the LocalSearchEngine')
        self._local_search_engine = _search.AsyncLocalSearchEngine(
            chat_llm=self._chat_llm,
            embedding=self._embedding,
            context_loader=local_context_loader,
            sys_prompt=self._config.local_search.sys_prompt,
            community_level=self._config.local_search.community_level,
            store_coll_name=self._config.local_search.store_coll_name,
            store_uri=self._config.local_search.store_uri,
            encoding_model=self._config.local_search.encoding_model,
            logger=self._logger,
            **(self._config.local_search.kwargs or {}),
        )

        if self._logger:
            self._logger.debug(f'LocalSearchEngine initialized: {self._local_search_engine}')
            self._logger.info('Initializing the GlobalSearchEngine')
        self._global_search_engine = _search.AsyncGlobalSearchEngine(
            chat_llm=self._chat_llm,
            embedding=self._embedding,
            context_builder=_search.GlobalContextBuilder.from_local_context_builder(
                self._local_search_engine.context_builder
            ),
            map_sys_prompt=self._config.global_search.map_sys_prompt,
            reduce_sys_prompt=self._config.global_search.reduce_sys_prompt,
            allow_general_knowledge=self._config.global_search.allow_general_knowledge,
            general_knowledge_sys_prompt=self._config.global_search.general_knowledge_sys_prompt,
            no_data_answer=self._config.global_search.no_data_answer,
            json_mode=self._config.global_search.json_mode,
            max_data_tokens=self._config.global_search.max_data_tokens,
            community_level=self._config.global_search.community_level,
            encoding_model=self._config.global_search.encoding_model,
            logger=self._logger,
            **(self._config.global_search.kwargs or {}),
        )
        if self._logger:
            self._logger.debug(f'GlobalSearchEngine initialized: {self._global_search_engine}')

    @typing_extensions.override
    async def chat(
        self,
        *,
        engine: typing.Literal['local', 'global'] = 'local',
        message: _types.MessageParam_T,
        stream: bool = False,
        verbose: bool = False,
        **kwargs: typing.Any
    ) -> typing.Union[_types.Response_T, _types.AsyncStreamResponse_T]:
        """
        Asynchronously performs a chat-based interaction using the specified
        search engine (local or global).

        Args:
            engine:
                Specifies whether to use the local or global search engine.
                Defaults to 'local'.
            message:
                An iterable of dictionaries representing the entire chat history
                and the current message. Each dictionary must contain the
                following keys:
                - 'role': The role of the message sender, which can be 'user',
                          'assistant', 'system', 'tool', or 'function'.
                          Currently, 'system', 'tool', and 'function' roles are
                          not supported and will be ignored.
                - 'content': The actual content of the message.
            stream:
                If True, enables streaming mode to receive the response
                incrementally. Defaults to False.
            verbose:
                If True, returns a detailed response with additional
                information. Recommended to be False in production environments.
                Defaults to False.
            **kwargs: Additional arguments for customizing the chat interaction.

        Returns:
            The response from the LLM, either complete or streamed, based on the
            `stream` argument.

        Raises:
            InvalidMessageError: If the message format is invalid.
            InvalidEngineError: If the specified engine is not recognized.
        """
        # TODO: Add support for system, function, and tool roles
        message = [msg for msg in message if msg['role'] not in ['system', 'function', 'tool']]
        if not self._verify_message(message):
            raise _errors.InvalidMessageError()

        # Convert iterable objects to list
        msg_list = [typing.cast(typing.Dict[typing.Literal["role", "content"], str], msg) for msg in message]
        conversation_history = _search.ConversationHistory.from_list(msg_list[:-1])
        if engine == 'local':
            if self._logger:
                self._logger.info(f'Local search with message: {msg_list[-1]["content"]}')
            response = await self._local_search_engine.asearch(
                msg_list[-1]['content'],
                conversation_history=conversation_history,
                stream=stream,
                verbose=verbose,
                **kwargs
            )
        elif engine == 'global':
            if self._logger:
                self._logger.info(f'Global search with message: {msg_list[-1]["content"]}')
            response = await self._global_search_engine.asearch(
                msg_list[-1]['content'],
                conversation_history=conversation_history,
                stream=stream,
                verbose=verbose,
                **kwargs
            )
        else:
            raise _errors.InvalidEngineError(engine)

        return response

    @typing_extensions.override
    async def close(self) -> None:
        """
        Asynchronously closes the client and releases any resources held by the
        search engines and language models.
        """
        await self._local_search_engine.aclose()
        await self._global_search_engine.aclose()

    # Support for async context manager
    @typing_extensions.override
    async def __aenter__(self) -> typing.Self:
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
