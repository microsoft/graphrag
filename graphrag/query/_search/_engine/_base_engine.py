# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import abc
import time
import typing

import pandas as pd
import typing_extensions

from .. import (
    _context,
    _llm,
    _types,
)


class Logger(typing.Protocol):
    """
    A protocol for defining basic logging behavior for a logger object.

    This protocol specifies the logging methods required to log messages at
    different severity levels, making it compatible with mainstream logging
    systems, such as Python's built-in `logging` module. It is designed to be
    used for collecting logs of internal processes in GraphRAG.
    """

    def error(self, msg: str, *args, **kwargs: typing.Any) -> None: ...

    def warning(self, msg: str, *args, **kwargs: typing.Any) -> None: ...

    def info(self, msg: str, *args, **kwargs: typing.Any) -> None: ...

    def debug(self, msg: str, *args, **kwargs: typing.Any) -> None: ...


class QueryEngine(abc.ABC):
    """
    Base class for GraphRAG query engines.

    This class defines the structure and behavior for executing queries in
    GraphRAG. It manages components such as a chat language model, embeddings,
    and a context builder, while providing methods to execute and handle query
    results. It supports both streaming and non-streaming search results.

    Attributes:
        _chat_llm: The chat language model instance.
        _embedding: The embedding model instance for text vectorization.
        _context_builder: The context builder that manages search context.
        _logger: Optional logger for logging internal engine events.
    """
    _chat_llm: _llm.BaseChatLLM
    _embedding: _llm.BaseEmbedding
    _context_builder: _context.BaseContextBuilder
    _logger: typing.Optional[Logger]

    @property
    @abc.abstractmethod
    def context_builder(self) -> _context.BaseContextBuilder:
        """
        Retrieves the context builder instance for the engine.

        The context builder is used to manage the search context and can be
        shared across multiple engines to avoid costly reinitialization.

        Returns:
            The context builder instance.
        """
        ...

    def __init__(
        self,
        *,
        chat_llm: _llm.BaseChatLLM,
        embedding: _llm.BaseEmbedding,
        context_builder: _context.BaseContextBuilder,
        logger: typing.Optional[Logger] = None,
    ):
        self._chat_llm = chat_llm
        self._embedding = embedding
        self._context_builder = context_builder
        self._logger = logger

    @abc.abstractmethod
    def search(
        self,
        query: str,
        *,
        conversation_history: _types.ConversationHistory_T = None,
        verbose: bool = True,
        stream: bool = False,
        **kwargs: typing.Any,
    ) -> typing.Union[_types.SearchResult_T, _types.StreamSearchResult_T]:
        """
        Executes a search query using the engine.

        Args:
            query: The search query string.
            conversation_history:
                A conversation history object or list of dictionaries containing
                prior user and assistant messages.
            verbose:
                If True, returns detailed search results (`SearchResultVerbose`
                or `SearchResultChunkVerbose` (if `steam` is Ture)). Otherwise,
                returns basic results (`SearchResult` or `SearchResultChunk`).
            stream:
                If True, enables streaming mode and returns an iterator of
                search results chunk by chunk. If False, returns the result once
                the query is complete.
            **kwargs: Additional parameters for the search engine.

        Returns:
            A search result object or a stream of result chunks, depending on
            the mode.
        """
        ...

    def _parse_result(
        self,
        result: _llm.ChatResponse_T,
        *,
        verbose: bool,
        created: float,
        context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
        map_result: typing.Optional[typing.List[_types.SearchResult]] = None,
        reduce_context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        reduce_context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
    ) -> _types.SearchResult_T:
        """
        Parses the non-streaming search result from the language model response.

        Converts the LLM response into either a `SearchResult` or a
        `SearchResultVerbose` object, depending on the verbosity level.

        Args:
            result: The chat response from the LLM.
            verbose:
                Whether to return a detailed (`SearchResultVerbose`) or basic
                (`SearchResult`) result.
            created: The timestamp when the search was initiated.
            context_data:
                Optional additional context data in DataFrame format. Only used
                in verbose mode.
            context_text:
                Optional additional context text, as a string or list of
                strings. Only used in verbose mode.
            map_result:
                Optional results from the map phase of a global search. Only
                used in verbose mode.
            reduce_context_data:
                Optional context data for the reduce phase of a global search.
                Only used in verbose mode.
            reduce_context_text:
                Optional context text for the reduce phase of a global search.
                Only used in verbose mode.

        Returns:
            A search result object.
        """
        usage = _types.Usage(
            completion_tokens=result.usage.completion_tokens,
            prompt_tokens=result.usage.prompt_tokens,
            total_tokens=result.usage.total_tokens,
        ) if result.usage else None
        if not verbose:
            return _types.SearchResult(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=result.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=result.choices[0].finish_reason,
                    message=_types.Message(
                        content=result.choices[0].message.content,
                        refusal=result.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
            )
        else:
            return _types.SearchResultVerbose(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=result.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=result.choices[0].finish_reason,
                    message=_types.Message(
                        content=result.choices[0].message.content,
                        refusal=result.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
                context_data=context_data,
                context_text=context_text,
                completion_time=time.time() - created,
                llm_calls=1,
                map_result=map_result,
                reduce_context_data=reduce_context_data,
                reduce_context_text=reduce_context_text,
            )

    def _parse_stream_result(
        self,
        result: _llm.SyncChatStreamResponse_T,
        *,
        verbose: bool,
        created: float,
        context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
        map_result: typing.Optional[typing.List[_types.SearchResult]] = None,
        reduce_context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        reduce_context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
    ) -> _types.StreamSearchResult_T:
        """
        Parses the streaming search result from the language model response.

        Converts the LLM response into a generator that yields either
        `SearchResultChunk` or `SearchResultChunkVerbose` objects depending on
        the verbosity level.

        Args:
            result: The chat response from the LLM.
            verbose:
                Whether to return a detailed (`SearchResultVerbose`) or basic
                (`SearchResult`) result.
            created: The timestamp when the search was initiated.
            context_data:
                Optional additional context data in DataFrame format. Only used
                in verbose mode.
            context_text:
                Optional additional context text, as a string or list of
                strings. Only used in verbose mode.
            map_result:
                Optional results from the map phase of a global search. Only
                used in verbose mode.
            reduce_context_data:
                Optional context data for the reduce phase of a global search.
                Only used in verbose mode.
            reduce_context_text:
                Optional context text for the reduce phase of a global search.
                Only used in verbose mode.

        Yields:
            A search result chunk object.
        """
        for chunk in result:
            usage = _types.Usage(
                completion_tokens=chunk.usage.completion_tokens,
                prompt_tokens=chunk.usage.prompt_tokens,
                total_tokens=chunk.usage.total_tokens,
            ) if chunk.usage else None
            if not verbose:
                yield _types.SearchResultChunk(
                    created=created.__int__(),
                    model=self._chat_llm.model,
                    system_fingerprint=chunk.system_fingerprint,
                    choice=_types.ChunkChoice(
                        finish_reason=chunk.choices[0].finish_reason,
                        delta=_types.Delta(
                            content=chunk.choices[0].delta.content,
                            refusal=chunk.choices[0].delta.refusal,
                        ),
                    ),
                    usage=usage,
                )
            else:
                if chunk.choices[0].finish_reason == "stop":
                    context_data_ = context_data
                    context_text_ = context_text
                    completion_time = time.time() - created
                    llm_calls = 1
                else:
                    context_data_ = None
                    context_text_ = None
                    completion_time = None
                    llm_calls = None
                yield _types.SearchResultChunkVerbose(
                    created=created.__int__(),
                    model=self._chat_llm.model,
                    system_fingerprint=chunk.system_fingerprint,
                    choice=_types.ChunkChoice(
                        finish_reason=chunk.choices[0].finish_reason,
                        delta=_types.Delta(
                            content=chunk.choices[0].delta.content,
                            refusal=chunk.choices[0].delta.refusal,
                        ),
                    ),
                    usage=usage,
                    context_data=context_data_,
                    context_text=context_text_,
                    completion_time=completion_time,
                    llm_calls=llm_calls,
                    map_result=map_result,
                    reduce_context_data=reduce_context_data,
                    reduce_context_text=reduce_context_text,
                )

    def close(self) -> None:
        """
        Closes the resources used by the engine, including the language model
        and embedding components.
        """
        self._chat_llm.close()
        self._embedding.close()

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"\tchat_llm={self._chat_llm},\n"
            f"\tembedding={self._embedding},\n"
            f"\tcontext_builder={self._context_builder},\n"
            f"\tlogger={self._logger}\n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class AsyncQueryEngine(abc.ABC):
    """
    Base class for asynchronous GraphRAG query engines.

    This class defines the structure and behavior for executing asynchronous queries
    in GraphRAG. It manages components such as an asynchronous chat language model,
    embeddings, and a context builder, while providing methods to execute and handle
    query results. It supports both streaming and non-streaming search results.

    Attributes:
        _chat_llm: The asynchronous chat language model instance.
        _embedding: The embedding model instance for text vectorization.
        _context_builder: The context builder that manages search context.
        _logger: Optional logger for logging internal engine events.
    """
    _chat_llm: _llm.BaseAsyncChatLLM
    _embedding: _llm.BaseEmbedding
    _context_builder: _context.BaseContextBuilder
    _logger: typing.Optional[Logger]

    @property
    @abc.abstractmethod
    def context_builder(self) -> _context.BaseContextBuilder:
        """
        Retrieves the context builder instance for the engine.

        The context builder is used to manage the search context and can be
        shared across multiple engines to avoid costly reinitialization.

        Returns:
            The context builder instance.
        """
        ...

    def __init__(
        self,
        *,
        chat_llm: _llm.BaseAsyncChatLLM,
        embedding: _llm.BaseEmbedding,
        context_builder: _context.BaseContextBuilder,
        logger: typing.Optional[Logger] = None,
    ):
        self._chat_llm = chat_llm
        self._embedding = embedding
        self._context_builder = context_builder
        self._logger = logger

    @abc.abstractmethod
    async def asearch(
        self,
        query: str,
        *,
        conversation_history: _types.ConversationHistory_T,
        verbose: bool = True,
        stream: bool = False,
        **kwargs: typing.Any,
    ) -> typing.Union[_types.SearchResult_T, _types.AsyncStreamSearchResult_T]:
        """
        Asynchronously executes a search query using the engine.

        Args:
            query: The search query string.
            conversation_history:
                A conversation history object or list of dictionaries containing
                prior user and assistant messages.
            verbose:
                If True, returns detailed search results (`SearchResultVerbose`
                or `SearchResultChunkVerbose` (if `steam` is Ture)). Otherwise,
                returns basic results (`SearchResult` or `SearchResultChunk`).
            stream:
                If True, enables streaming mode and returns an async iterator of
                search results chunk by chunk. If False, returns the result once
                the query is complete.
            **kwargs: Additional parameters for the search engine.

        Returns:
            A search result object or a stream of result chunks, depending on
            the mode.
        """
        ...

    def _parse_result(
        self,
        result: _llm.ChatResponse_T,
        *,
        verbose: bool,
        created: float,
        context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
        map_result: typing.Optional[typing.List[_types.SearchResult]] = None,
        reduce_context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        reduce_context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
    ) -> _types.SearchResult_T:
        """
        Parses the non-streaming search result from the language model response.

        Converts the LLM response into either a `SearchResult` or a
        `SearchResultVerbose` object, depending on the verbosity level.

        Args:
            result: The chat response from the LLM.
            verbose:
                Whether to return a detailed (`SearchResultVerbose`) or basic
                (`SearchResult`) result.
            created: The timestamp when the search was initiated.
            context_data:
                Optional additional context data in DataFrame format. Only used
                in verbose mode.
            context_text:
                Optional additional context text, as a string or list of
                strings. Only used in verbose mode.
            map_result:
                Optional results from the map phase of a global search. Only
                used in verbose mode.
            reduce_context_data:
                Optional context data for the reduce phase of a global search.
                Only used in verbose mode.
            reduce_context_text:
                Optional context text for the reduce phase of a global search.
                Only used in verbose mode.

        Returns:
            A search result object.
        """
        usage = _types.Usage(
            completion_tokens=result.usage.completion_tokens,
            prompt_tokens=result.usage.prompt_tokens,
            total_tokens=result.usage.total_tokens,
        ) if result.usage else None
        if not verbose:
            return _types.SearchResult(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=result.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=result.choices[0].finish_reason,
                    message=_types.Message(
                        content=result.choices[0].message.content,
                        refusal=result.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
            )
        else:
            return _types.SearchResultVerbose(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=result.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=result.choices[0].finish_reason,
                    message=_types.Message(
                        content=result.choices[0].message.content,
                        refusal=result.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
                context_data=context_data,
                context_text=context_text,
                completion_time=time.time() - created,
                llm_calls=1,
                map_result=map_result,
                reduce_context_data=reduce_context_data,
                reduce_context_text=reduce_context_text,
            )

    async def _parse_stream_result(
        self,
        result: _llm.AsyncChatStreamResponse_T,
        *,
        verbose: bool,
        created: float,
        context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
        map_result: typing.Optional[typing.List[_types.SearchResult]] = None,
        reduce_context_data: typing.Optional[typing.Dict[str, pd.DataFrame]] = None,
        reduce_context_text: typing.Optional[typing.Union[str, typing.List[str]]] = None,
    ) -> _types.AsyncStreamSearchResult_T:
        """
        Parses the streaming search result from the language model response.

        Converts the LLM response into an async generator that yields either
        `SearchResultChunk` or `SearchResultChunkVerbose` objects depending on
        the verbosity level.

        Args:
            result: The chat response from the LLM.
            verbose:
                Whether to return a detailed (`SearchResultVerbose`) or basic
                (`SearchResult`) result.
            created: The timestamp when the search was initiated.
            context_data:
                Optional additional context data in DataFrame format. Only used
                in verbose mode.
            context_text:
                Optional additional context text, as a string or list of
                strings. Only used in verbose mode.
            map_result:
                Optional results from the map phase of a global search. Only
                used in verbose mode.
            reduce_context_data:
                Optional context data for the reduce phase of a global search.
                Only used in verbose mode.
            reduce_context_text:
                Optional context text for the reduce phase of a global search.
                Only used in verbose mode.

        Yields:
            A search result chunk object.
        """
        async for chunk in result:
            usage = _types.Usage(
                completion_tokens=chunk.usage.completion_tokens,
                prompt_tokens=chunk.usage.prompt_tokens,
                total_tokens=chunk.usage.total_tokens,
            ) if chunk.usage else None
            if not verbose:
                yield _types.SearchResultChunk(
                    created=created.__int__(),
                    model=self._chat_llm.model,
                    system_fingerprint=chunk.system_fingerprint,
                    choice=_types.ChunkChoice(
                        finish_reason=chunk.choices[0].finish_reason,
                        delta=_types.Delta(
                            content=chunk.choices[0].delta.content,
                            refusal=chunk.choices[0].delta.refusal,
                        ),
                    ),
                    usage=usage,
                )
            else:
                if chunk.choices[0].finish_reason == "stop":
                    context_data_ = context_data
                    context_text_ = context_text
                    completion_time = time.time() - created
                    llm_calls = 1
                else:
                    context_data_ = None
                    context_text_ = None
                    completion_time = None
                    llm_calls = None
                yield _types.SearchResultChunkVerbose(
                    created=created.__int__(),
                    model=self._chat_llm.model,
                    system_fingerprint=chunk.system_fingerprint,
                    choice=_types.ChunkChoice(
                        finish_reason=chunk.choices[0].finish_reason,
                        delta=_types.Delta(
                            content=chunk.choices[0].delta.content,
                            refusal=chunk.choices[0].delta.refusal,
                        ),
                    ),
                    usage=usage,
                    context_data=context_data_,
                    context_text=context_text_,
                    completion_time=completion_time,
                    llm_calls=llm_calls,
                    map_result=map_result,
                    reduce_context_data=reduce_context_data,
                    reduce_context_text=reduce_context_text,
                )

    async def aclose(self) -> None:
        await self._chat_llm.aclose()
        self._embedding.close()

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(\n"
            f"\tchat_llm={self._chat_llm},\n"
            f"\tembedding={self._embedding},\n"
            f"\tcontext_builder={self._context_builder},\n"
            f"\tlogger={self._logger}\n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()
