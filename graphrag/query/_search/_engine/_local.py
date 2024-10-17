# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import collections
import time
import typing
import warnings

import typing_extensions

from . import _base_engine
from .. import (
    _context,
    _defaults,
    _llm,
    _types,
)
from ... import errors as _errors


class LocalSearchEngine(_base_engine.QueryEngine):
    """
    LocalSearchEngine implements the QueryEngine and is responsible for
    executing local searches in the GraphRAG framework. This engine manages
    local context and performs search operations restricted to a specific scope
    defined by the LocalContextBuilder.

    Attributes:
        _chat_llm:
            The language model used for chat interactions in the search process.
        _embedding:
            The embedding model used for vectorizing query and context data.
        _context_builder:
            A specialized LocalContextBuilder responsible for building context
            specific to local search.
        _logger:
            Optional logger instance for recording internal events and debug
            information.
        _sys_prompt:
            The system prompt template used during the local search to generate
            the final local answer. Must include the placeholder '{context_data}'
            to inject the real context data.
    """
    _chat_llm: _llm.BaseChatLLM
    _embedding: _llm.BaseEmbedding
    _context_builder: _context.LocalContextBuilder
    _logger: typing.Optional[_base_engine.Logger]
    _sys_prompt: str

    @typing_extensions.override
    @property
    def context_builder(self) -> _context.LocalContextBuilder:
        return self._context_builder

    def __init__(
        self,
        *,
        chat_llm: _llm.BaseChatLLM,
        embedding: _llm.BaseEmbedding,

        context_loader: typing.Optional[_context.LocalContextLoader] = None,
        context_builder: typing.Optional[_context.LocalContextBuilder] = None,

        sys_prompt: typing.Optional[str] = None,
        community_level: typing.Optional[int] = None,
        store_coll_name: typing.Optional[str] = None,
        store_uri: typing.Optional[str] = None,
        encoding_model: typing.Optional[str] = None,

        logger: typing.Optional[_base_engine.Logger] = None,

        **kwargs: typing.Any,
    ) -> None:
        if logger:
            logger.debug(f"Creating LocalSearchEngine with context_loader: {context_loader}")
        if not context_builder and not context_loader:
            raise ValueError("Either context_loader or context_builder must be provided")

        if context_loader:
            # If context_loader is provided, load context_builder from it
            context_builder = context_loader.to_context_builder(
                embedder=embedding,
                community_level=community_level or _defaults.DEFAULT__LOCAL_SEARCH__COMMUNITY_LEVEL,
                store_coll_name=store_coll_name or _defaults.DEFAULT__VECTOR_STORE__COLLECTION_NAME,
                store_uri=store_uri or _defaults.DEFAULT__VECTOR_STORE__URI,
                encoding_model=encoding_model or _defaults.DEFAULT__ENCODING_MODEL,
                **kwargs,
            )

        if logger:
            logger.debug(f"Created LocalSearchEngine with context_builder: {context_builder}")
        context_builder = typing.cast(_context.LocalContextBuilder, context_builder)
        super().__init__(
            chat_llm=chat_llm,
            embedding=embedding,
            context_builder=context_builder,
            logger=logger,
        )
        self._sys_prompt = sys_prompt or _defaults.LOCAL_SEARCH__SYS_PROMPT
        if '{context_data}' not in self._sys_prompt:
            warnings.warn('Local Search\'s System Prompt does not contain "{context_data}"', _errors.GraphRAGWarning)
            if self._logger:
                self._logger.warning('Local Search\'s System Prompt does not contain "{context_data}"')

    @typing_extensions.override
    def search(
        self,
        query: str,
        *,
        conversation_history: _types.ConversationHistory_T = None,
        verbose: bool = False,
        stream: bool = False,
        sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> typing.Union[_types.SearchResult_T, _types.StreamSearchResult_T]:
        """
        Executes the local search operation based on the given query.

        The search operates within a restricted local context built by the
        LocalContextBuilder. It uses the system prompt to guide the search and
        retrieve relevant responses.

        Args:
            query: The search query string.
            conversation_history:
                The conversation history, which can be passed in as a list or a
                ConversationHistory object.
            verbose:
                If True, returns detailed results in the form of
                SearchResultVerbose or SearchResultChunkVerbose objects.
                Otherwise, returns basic SearchResult objects.
            stream:
                If True, enables streaming mode and returns an iterator of
                results. If False, returns results after the entire process
                completes.
            sys_prompt:
                A temporary prompt to override the default system prompt for
                this search.
            **kwargs:
                Additional keyword arguments for
                `LocalContextBuilder.build_context` or `ChatLLM.chat`. See
                details in the specific method documentation and source code.

        Returns:
            A search result object or a stream of search result chunks,
            depending on the value of `stream`.
        """
        created = time.time()
        if self._logger:
            self._logger.info(f"Starting search for query: {query} at {created}")

        if conversation_history is None:
            conversation_history = _context.ConversationHistory()
        elif isinstance(conversation_history, list):
            conversation_history = _context.ConversationHistory.from_list(conversation_history)

        context_text, context_records = self._context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **kwargs,
        )
        # TODO: Add Jinja2 template support for sys_prompt (same for GlobalSearchEngine)
        prompt = (sys_prompt or self._sys_prompt).format_map(collections.defaultdict(str, context_data=context_text))
        messages = ([{"role": "system", "content": prompt}] +
                    conversation_history.to_dict() +
                    [{"role": "user", "content": query}])
        if self._logger:
            self._logger.debug(f"Constructed messages: {messages}")

        result = self._chat_llm.chat(msg=typing.cast(_llm.MessageParam_T, messages), stream=stream, **kwargs)

        if self._logger:
            self._logger.info(f"Received result: {result}\nspent time: {time.time() - created} seconds")

        if stream:
            result = typing.cast(_llm.SyncChatStreamResponse_T, result)
            return self._parse_stream_result(
                result,
                verbose=verbose,
                created=created,
                context_data=context_records,
                context_text=context_text
            )
        else:
            result = typing.cast(_llm.ChatResponse_T, result)
            return self._parse_result(
                result,
                verbose=verbose,
                created=created,
                context_data=context_records,
                context_text=context_text
            )

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"\tchat_llm={self._chat_llm}, \n"
            f"\tembedding={self._embedding}, \n"
            f"\tcontext_builder={self._context_builder}, \n"
            f"\tlogger={self._logger} \n"
            f"\tsys_prompt={self._sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._sys_prompt) > 50 else ''} \n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class AsyncLocalSearchEngine(_base_engine.AsyncQueryEngine):
    """
    AsyncLocalSearchEngine implements the QueryEngine and is responsible for
    executing local searches in the GraphRAG framework asynchronously. This
    engine manages local context and performs search operations restricted to a
    specific scope defined by the LocalContextBuilder.

    Attributes:
        _chat_llm:
            The asynchronous language model used for chat interactions in the
            search process.
        _embedding:
            The embedding model used for vectorizing query and context data.
        _context_builder:
            A specialized LocalContextBuilder responsible for building context
            specific to local search.
        _logger:
            Optional logger instance for recording internal events and debug
            information.
        _sys_prompt:
            The system prompt template used during the local search to generate
            the final local answer. Must include the placeholder '{context_data}'
            to inject the real context data.
    """
    _chat_llm: _llm.BaseAsyncChatLLM
    _embedding: _llm.BaseEmbedding
    _context_builder: _context.LocalContextBuilder
    _logger: typing.Optional[_base_engine.Logger]
    _sys_prompt: str

    @typing_extensions.override
    @property
    def context_builder(self) -> _context.LocalContextBuilder:
        return self._context_builder

    def __init__(
        self,
        *,
        chat_llm: _llm.BaseAsyncChatLLM,
        embedding: _llm.BaseEmbedding,

        context_loader: typing.Optional[_context.LocalContextLoader] = None,
        context_builder: typing.Optional[_context.LocalContextBuilder] = None,

        sys_prompt: typing.Optional[str] = None,
        community_level: typing.Optional[int] = None,
        store_coll_name: typing.Optional[str] = None,
        store_uri: typing.Optional[str] = None,
        encoding_model: typing.Optional[str] = None,

        logger: typing.Optional[_base_engine.Logger] = None,

        **kwargs: typing.Any,
    ) -> None:
        if logger:
            logger.debug(f"Creating AsyncLocalSearchEngine with context_loader: {context_loader}")
        if context_loader is None and context_builder is None:
            raise ValueError("Either context_loader or context_builder must be provided")

        if context_loader:
            context_builder = context_loader.to_context_builder(
                embedder=embedding,
                community_level=community_level or _defaults.DEFAULT__LOCAL_SEARCH__COMMUNITY_LEVEL,
                store_coll_name=store_coll_name or _defaults.DEFAULT__VECTOR_STORE__COLLECTION_NAME,
                store_uri=store_uri or _defaults.DEFAULT__VECTOR_STORE__URI,
                encoding_model=encoding_model or _defaults.DEFAULT__ENCODING_MODEL,
                **kwargs,
            )

        if logger:
            logger.debug(f"Created AsyncLocalSearchEngine with context_builder: {context_builder}")
        context_builder = typing.cast(_context.LocalContextBuilder, context_builder)
        super().__init__(
            chat_llm=chat_llm,
            embedding=embedding,
            context_builder=context_builder,
            logger=logger,
        )
        self._sys_prompt = sys_prompt or _defaults.LOCAL_SEARCH__SYS_PROMPT
        if '{context_data}' not in self._sys_prompt:
            warnings.warn('Local Search\'s System Prompt does not contain "{context_data}"', _errors.GraphRAGWarning)
            if self._logger:
                self._logger.warning('Local Search\'s System Prompt does not contain "{context_data}"')

    @typing_extensions.override
    async def asearch(
        self,
        query: str,
        *,
        conversation_history: _types.ConversationHistory_T,
        verbose: bool = False,
        stream: bool = False,
        sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> typing.Union[_types.SearchResult_T, _types.AsyncStreamSearchResult_T]:
        """
        Executes the local search operation based on the given query
        asynchronously.

        The search operates within a restricted local context built by the
        LocalContextBuilder. It uses the system prompt to guide the search and
        retrieve relevant responses.

        Args:
            query: The search query string.
            conversation_history:
                The conversation history, which can be passed in as a list or a
                ConversationHistory object.
            verbose:
                If True, returns detailed results in the form of
                SearchResultVerbose or SearchResultChunkVerbose objects.
                Otherwise, returns basic SearchResult objects.
            stream:
                If True, enables streaming mode and returns an iterator of
                results. If False, returns results after the entire process
                completes.
            sys_prompt:
                A temporary prompt to override the default system prompt for
                this search.
            **kwargs:
                Additional keyword arguments for
                `LocalContextBuilder.build_context` or `ChatLLM.chat`. See
                details in the specific method documentation and source code.

        Returns:
            A search result object or a stream of search result chunks,
            depending on the value of `stream`.
        """

        created = time.time()
        if self._logger:
            self._logger.info(f"Starting search for query: {query} at {created}")

        # Convert conversation_history to ConversationHistory object
        if conversation_history is None:
            conversation_history = _context.ConversationHistory()
        elif isinstance(conversation_history, list):
            conversation_history = _context.ConversationHistory.from_list(conversation_history)

        context_text, context_records = self._context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **kwargs,
        )
        prompt = (sys_prompt or self._sys_prompt).format_map(collections.defaultdict(str, context_data=context_text))
        messages = ([{"role": "system", "content": prompt}] +
                    conversation_history.to_dict() +
                    [{"role": "user", "content": query}])
        if self._logger:
            self._logger.debug(f"Constructed messages: {messages}")

        result = await self._chat_llm.achat(msg=typing.cast(_llm.MessageParam_T, messages), stream=stream, **kwargs)

        if self._logger:
            self._logger.info(f"Received result: {result}\nspent time: {time.time() - created} seconds")

        if stream:
            result = typing.cast(_llm.AsyncChatStreamResponse_T, result)
            return self._parse_stream_result(
                result,
                verbose=verbose,
                created=created,
                context_data=context_records,
                context_text=context_text
            )
        else:
            result = typing.cast(_llm.ChatResponse_T, result)
            return self._parse_result(
                result,
                verbose=verbose,
                created=created,
                context_data=context_records,
                context_text=context_text
            )

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"\tchat_llm={self._chat_llm}, \n"
            f"\tembedding={self._embedding}, \n"
            f"\tcontext_builder={self._context_builder}, \n"
            f"\tlogger={self._logger} \n"
            f"\tsys_prompt={self._sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._sys_prompt) > 50 else ''} \n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()
