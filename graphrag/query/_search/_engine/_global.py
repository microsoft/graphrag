# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import asyncio
import collections
import time
import typing
import warnings

import openai
import tiktoken
import typing_extensions

from . import _base_engine
from .. import (
    _context,
    _defaults,
    _llm,
    _types,
)
from ... import (
    _utils,
    errors as _errors,
)


class GlobalSearchEngine(_base_engine.QueryEngine):
    """
    GlobalSearchEngine implements the QueryEngine and is responsible for
    executing global searches in the GraphRAG framework. It handles both the
    "map" and "reduce" phases of distributed search, applying the context built
    through the GlobalContextBuilder.

    Attributes:
        _chat_llm:
            The language model used for chat interactions in the search process.
        _embedding:
            The embedding model. (This parameter is under consideration for
            deprecation.)
        _context_builder:
            A specialized GlobalContextBuilder for constructing search context.
        _logger:
            Optional logger instance for recording internal events and debug
            information.
        _token_encoder:
            Encoder used to calculate the token count in text, consistent with
            the tokenizer used by the large language model (LLM).
        _map_sys_prompt:
            The prompt used during the map phase of global search. Must include
            the placeholder '{context_data}' for injecting real data.
        _reduce_sys_prompt:
            The prompt used during the reduce phase of global search. Must
            include the placeholder '{report_data}' for injecting real data.
        _allow_general_knowledge:
            A flag indicating whether the model is allowed to use real-world
            knowledge in responses. If True, the general knowledge prompt will
            be added to the reduce phase. (This parameter is under consideration
            for deprecation.)
        _general_knowledge_sys_prompt:
            The prompt that enables real-world knowledge use in the reduce
            phase. (This parameter is under consideration for deprecation.)
        _no_data_answer:
            The fallback response when no meaningful data is retrieved from the
            map phase (i.e., when all map responses have a score of 0).
        _json_mode:
            Indicates whether the LLM returns responses in JSON format during
            the map phase (if supported by the LLM).
        _data_max_tokens:
            The maximum number of tokens allowed for input context during the
            map phase.
    """
    _chat_llm: _llm.BaseChatLLM
    _embedding: _llm.BaseEmbedding
    _context_builder: _context.GlobalContextBuilder
    _logger: typing.Optional[_base_engine.Logger]
    _token_encoder: tiktoken.Encoding
    _map_sys_prompt: str
    _reduce_sys_prompt: str
    _allow_general_knowledge: bool
    _general_knowledge_sys_prompt: str
    _no_data_answer: str
    _json_mode: bool
    _data_max_tokens: int

    @typing_extensions.override
    @property
    def context_builder(self) -> _context.GlobalContextBuilder:
        return self._context_builder

    def __init__(
        self,
        *,
        chat_llm: _llm.BaseChatLLM,
        embedding: _llm.BaseEmbedding,

        context_loader: typing.Optional[_context.GlobalContextLoader] = None,
        context_builder: typing.Optional[_context.GlobalContextBuilder] = None,

        community_level: typing.Optional[int] = None,
        map_sys_prompt: typing.Optional[str] = None,
        reduce_sys_prompt: typing.Optional[str] = None,
        allow_general_knowledge: typing.Optional[bool] = None,
        general_knowledge_sys_prompt: typing.Optional[str] = None,
        no_data_answer: typing.Optional[str] = None,
        json_mode: typing.Optional[bool] = None,
        max_data_tokens: typing.Optional[int] = None,
        encoding_model: typing.Optional[str] = None,

        logger: typing.Optional[_base_engine.Logger] = None,
        **kwargs: typing.Any,
    ) -> None:
        if logger:
            logger.debug(f"Creating GlobalSearchEngine with context_loader: {context_loader}")
        if not context_builder and not context_loader:
            raise ValueError("Either context_builder or context_loader must be provided")

        if context_loader:
            context_builder = context_loader.to_context_builder(
                community_level=community_level or _defaults.DEFAULT__GLOBAL_SEARCH__COMMUNITY_LEVEL,
                encoding_model=encoding_model or _defaults.DEFAULT__ENCODING_MODEL,
                **kwargs,
            )

        if logger:
            logger.debug(f"Created GlobalSearchEngine with context_builder: {context_builder}")
        context_builder = typing.cast(_context.GlobalContextBuilder, context_builder)
        super().__init__(
            chat_llm=chat_llm,
            embedding=embedding,
            context_builder=context_builder,
            logger=logger
        )
        self._token_encoder = tiktoken.get_encoding(encoding_model or _defaults.DEFAULT__ENCODING_MODEL)
        self._map_sys_prompt = map_sys_prompt or _defaults.GLOBAL_SEARCH__MAP__SYS_PROMPT
        if '{context_data}' not in self._map_sys_prompt:
            warnings.warn(
                'Global Search\'s Map System Prompt does not contain "{context_data}"', _errors.GraphRAGWarning
            )
            if self._logger:
                self._logger.warning('Global Search\'s Map System Prompt does not contain "{context_data}"')
        self._reduce_sys_prompt = reduce_sys_prompt or _defaults.GLOBAL_SEARCH__REDUCE__SYS_PROMPT
        if '{report_data}' not in self._reduce_sys_prompt:
            warnings.warn(
                'Global Search\'s Reduce System Prompt does not contain "{report_data}"', _errors.GraphRAGWarning
            )
            if self._logger:
                self._logger.warning('Global Search\'s Reduce System Prompt does not contain "{report_data}"')
        self._allow_general_knowledge = allow_general_knowledge if allow_general_knowledge is not None else True
        self._general_knowledge_sys_prompt = (general_knowledge_sys_prompt or
                                              _defaults.GLOBAL_SEARCH__REDUCE__GENERAL_KNOWLEDGE_INSTRUCTION)
        self._no_data_answer = no_data_answer or _defaults.GLOBAL_SEARCH__REDUCE__NO_DATA_ANSWER
        self._json_mode = json_mode if json_mode is not None else True
        self._data_max_tokens = max_data_tokens or _defaults.DEFAULT__GLOBAL_SEARCH__DATA_MAX_TOKENS

    @typing_extensions.override
    def search(
        self,
        query: str,
        *,
        conversation_history: _types.ConversationHistory_T = None,
        verbose: bool = False,
        stream: bool = False,
        map_sys_prompt: typing.Optional[str] = None,
        reduce_sys_prompt: typing.Optional[str] = None,
        general_knowledge_sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> typing.Union[_types.SearchResult_T, _types.StreamSearchResult_T]:
        """
        Executes a global search based on the given query.

        The search consists of two phases:
        1. Map phase: Each community answers the query using its context.
        2. Reduce phase: The individual community answers are aggregated into a
                         global answer.

        Args:
            query: The query string for the search.
            conversation_history:
                The conversation history, which can be passed in as a list
                or a ConversationHistory object.
            verbose:
                If True, returns detailed results in the form of
                SearchResultVerbose or SearchResultChunkVerbose objects.
                Otherwise, returns basic SearchResult objects.
            stream:
                If True, enables streaming mode and returns an iterator of
                results. If False, returns results after the entire process
                completes.
            map_sys_prompt:
                A temporary prompt to override the default map system prompt for
                this search.
            reduce_sys_prompt:
                A temporary prompt to override the default reduce system prompt
                for this search.
            general_knowledge_sys_prompt:
                A temporary prompt to override the default general knowledge
                system prompt for this search.
            **kwargs:
                Additional keyword arguments, can be prefixed with 'map__' for
                `self._map` or 'reduce__' for `self._reduce` or not prefixed for
                `GlobalContextBuilder.build_context`. See details in the
                specific method documentation and source code.

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

        context_chunks, context_records = self._context_builder.build_context(
            conversation_history=conversation_history,
            **kwargs,
        )
        # TODO: Parallelize the map phase.
        map_result = [self._map(
            query=query,
            context=context,
            verbose=verbose,
            map_sys_prompt=map_sys_prompt,
            json_mode=self._json_mode,
            **kwargs
        ) for context in context_chunks]
        return self._reduce(
            map_results=map_result,
            query=query,
            verbose=verbose,
            stream=stream,
            reduce_sys_prompt=reduce_sys_prompt,
            general_knowledge_sys_prompt=general_knowledge_sys_prompt,
            **kwargs
        )

    def _map(
        self,
        *,
        query: str,
        context: str,
        verbose: bool,
        map_sys_prompt: typing.Optional[str] = None,
        json_mode: bool = True,
        **kwargs: typing.Any
    ) -> _types.SearchResult_T:
        """
        Executes the map phase of the GraphRAG global search.

        In this phase, each community answers the query based on its specific
        context data. The result is then used in the reduce phase to form the
        final answer.

        See https://arxiv.org/abs/2404.16130.

        Args:
            query:
                The query string for the search.
            context:
                The context data specific to a community, used in the map phase.
            verbose:
                If True, returns a detailed SearchResultVerbose object,
                otherwise returns a basic SearchResult object.
            map_sys_prompt:
                A temporary prompt to override the default map system prompt.
            **kwargs:
                Additional keyword arguments. Should be prefixed with 'map__'
                for `ChatLLM.chat` method. See details in the specific method
                documentation and source code.

        Returns:
            A SearchResult or SearchResultVerbose object, depending on the
            verbosity setting.
        """
        created = time.time()
        if self._logger:
            self._logger.info(f"Starting map for query: {query} at {created}")

        prompt = (map_sys_prompt or self._map_sys_prompt).format_map(
            collections.defaultdict(str, context_data=context, query=query)
        )
        msg = [{"role": "system", "content": prompt}, {"role": "user", "content": query}]
        if self._logger:
            self._logger.debug(f"Constructed messages: {msg}")

        response = typing.cast(
            _llm.ChatResponse_T, self._chat_llm.chat(
                msg=typing.cast(_llm.MessageParam_T, msg),
                stream=False,
                response_format={"type": "json_object"} if json_mode else openai.NOT_GIVEN,
                **_utils.filter_kwargs(self._chat_llm.chat, kwargs, prefix='map__')
            )
        )
        result = self._parse_map(response)

        usage = _types.Usage(
            completion_tokens=response.usage.completion_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens,
        ) if response.usage else None

        if verbose:
            return _types.SearchResultVerbose(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=response.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=response.choices[0].finish_reason,
                    message=_types.Message(
                        content=result,
                        refusal=response.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
                context_data=None,
                context_text=context,
                completion_time=time.time() - created,
                llm_calls=1,
            )
        else:
            return _types.SearchResult(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=response.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=response.choices[0].finish_reason,
                    message=_types.Message(
                        content=result,
                        refusal=response.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
            )

    @staticmethod
    def _parse_map(response: _llm.ChatResponse_T) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Converts the response from the map phase into a list of key points.
        """
        default = [{"answer": "", "score": 0}]
        json_ = _utils.deserialize_json(response.choices[0].message.content or "")
        if json_ == {}:
            return default

        points = json_.get("points", [])
        if not isinstance(points, list):
            return default

        return [
            {"answer": point["description"], "score": int(point["score"])}
            for point in points
            if isinstance(point, dict) and "description" in point and "score" in point
        ]

    def _reduce(
        self,
        *,
        map_results: typing.List[_types.SearchResult_T],
        query: str,
        verbose: bool,
        stream: bool,
        reduce_sys_prompt: typing.Optional[str] = None,
        general_knowledge_sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any
    ) -> typing.Union[_types.SearchResult_T, _types.StreamSearchResult_T]:
        """
        Executes the reduce phase of the GraphRAG global search.

        In this phase, the individual results from the map phase are combined
        into a final global answer. Optionally, general knowledge prompts can
        be applied.

        See https://arxiv.org/abs/2404.16130.

        Args:
            map_results: A list of search results from the map phase.
            query: The query string for the search.
            verbose:
                If True, returns detailed results in the form of
                SearchResultVerbose or SearchResultChunkVerbose objects.
                Otherwise, returns basic SearchResult objects.
            stream:
                If True, enables streaming mode and returns an iterator of
                results. If False, returns results after the entire process
                completes.
            reduce_sys_prompt:
                A temporary prompt to override the default reduce system prompt
                for this search.
            general_knowledge_sys_prompt:
                A temporary prompt to override the default general knowledge
                system prompt for this search.
            **kwargs:
                Additional keyword arguments. Should be prefixed with 'reduce__'
                for `ChatLLM.chat` method. See details in the specific method
                documentation and source code.

        Returns:
            A search result object or a stream of search result chunks,
            depending on the value of `stream`.
        """
        created = time.time()
        if self._logger:
            self._logger.info(f"Starting reduce for query: {query} at {created}")

        key_points: typing.List[typing.Dict[str, typing.Any]] = []
        for idx, map_ in enumerate(map_results):
            if not isinstance(map_.choice.message.content, list):
                continue
            for ele in map_.choice.message.content:
                if not isinstance(ele, dict) or "answer" not in ele or "score" not in ele:
                    continue
                key_points.append(
                    {
                        "analyst": idx,
                        "answer":  ele["answer"],
                        "score":   ele["score"]
                    }
                )

        key_points = [kp for kp in key_points if isinstance(kp["score"], (int, float)) and kp["score"] > 0]

        if not key_points.__len__() and not self._allow_general_knowledge:
            warnings.warn("No key points found from the map phase", _errors.GraphRAGWarning)
            if self._logger:
                self._logger.warning("No key points found from the map phase")
            return _types.SearchResult(
                created=created.__int__(),
                model=self._chat_llm.model,
                choice=_types.Choice(
                    finish_reason="stop",
                    message=_types.Message(
                        content=self._no_data_answer,
                    ),
                ),
                usage=None,
            ) if not verbose else _types.SearchResultVerbose(
                created=created.__int__(),
                model=self._chat_llm.model,
                choice=_types.Choice(
                    finish_reason="stop",
                    message=_types.Message(
                        content=self._no_data_answer,
                    ),
                ),
                completion_time=time.time() - created,
                llm_calls=0,
            )

        key_points = sorted(
            key_points,
            key=lambda kp: kp["score"] if isinstance(kp["score"], (int, float)) else 0,
            reverse=True
        )
        if self._logger:
            self._logger.info(f"Key points found: {key_points}")

        data: typing.List[str] = []
        total_tokens = 0
        for kp in key_points:
            formatted_response = '\n'.join(
                [f'----Analyst {kp["analyst"] + 1}----', f'Importance score: {kp["score"]}', kp["answer"]]
            )
            total_tokens += _utils.num_tokens(formatted_response, self._token_encoder)
            if total_tokens > self._data_max_tokens:
                warnings.warn("Data exceeds maximum token limit", _errors.GraphRAGWarning)
                break
            data.append(formatted_response)

        report_data = '\n\n'.join(data)
        prompt = (reduce_sys_prompt or self._reduce_sys_prompt).format_map(
            collections.defaultdict(str, report_data=report_data)
        )
        if self._allow_general_knowledge:
            prompt += f'\n{general_knowledge_sys_prompt or self._general_knowledge_sys_prompt}'
        msg = [{"role": "system", "content": prompt}, {"role": "user", "content": query}]

        if self._logger:
            self._logger.debug(f"Constructed messages: {msg}")
        result = self._chat_llm.chat(
            msg=typing.cast(_llm.MessageParam_T, msg),
            stream=stream,
            **_utils.filter_kwargs(self._chat_llm.chat, kwargs, prefix='reduce__')
        )

        if stream:
            result = typing.cast(_llm.SyncChatStreamResponse_T, result)
            return self._parse_stream_result(
                result,
                verbose=verbose,
                created=created,
                context_data=None,
                context_text=report_data,
                map_result=map_results,
                reduce_context_data=None,
                reduce_context_text=report_data,
            )
        else:
            result = typing.cast(_llm.ChatResponse_T, result)
            return self._parse_result(
                result,
                verbose=verbose,
                created=created,
                context_data=None,
                context_text=report_data,
                map_result=map_results,
                reduce_context_data=None,
                reduce_context_text=report_data,
            )

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"\tchat_llm={self._chat_llm}, \n"
            f"\tembedding={self._embedding}, \n"
            f"\tcontext_builder={self._context_builder}, \n"
            f"\tlogger={self._logger}\n"
            f"\tmap_sys_prompt={self._map_sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._map_sys_prompt) > 50 else ''}, \n"
            f"\treduce_sys_prompt={self._reduce_sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._reduce_sys_prompt) > 50 else ''}, \n"
            f"\tallow_general_knowledge={self._allow_general_knowledge}, \n"
            f"\tgeneral_knowledge_sys_prompt={self._general_knowledge_sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._general_knowledge_sys_prompt) > 50 else ''}, \n"
            f"\tno_data_answer={self._no_data_answer.__repr__()}, \n"
            f"\tjson_mode={self._json_mode}, \n"
            f"\tdata_max_tokens={self._data_max_tokens} \n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()


class AsyncGlobalSearchEngine(_base_engine.AsyncQueryEngine):
    """
    AsyncGlobalSearchEngine implements the AsyncQueryEngine and is responsible
    for executing global searches in the GraphRAG framework. It handles both the
    "map" and "reduce" phases of distributed search, applying the context built
    through the GlobalContextBuilder.

    Attributes:
        _chat_llm:
            The asynchronous language model used for chat interactions in the
            search process.
        _embedding:
            The embedding model. (This parameter is under consideration for
            deprecation.)
        _context_builder:
            A specialized GlobalContextBuilder for constructing search context.
        _logger:
            Optional logger instance for recording internal events and debug
            information.
        _token_encoder:
            Encoder used to calculate the token count in text, consistent with
            the tokenizer used by the large language model (LLM).
        _map_sys_prompt:
            The prompt used during the map phase of global search. Must include
            the placeholder '{context_data}' for injecting real data.
        _reduce_sys_prompt:
            The prompt used during the reduce phase of global search. Must
            include the placeholder '{report_data}' for injecting real data.
        _allow_general_knowledge:
            A flag indicating whether the model is allowed to use real-world
            knowledge in responses. If True, the general knowledge prompt will
            be added to the reduce phase. (This parameter is under consideration
            for deprecation.)
        _general_knowledge_sys_prompt:
            The prompt that enables real-world knowledge use in the reduce
            phase. (This parameter is under consideration for deprecation.)
        _no_data_answer:
            The fallback response when no meaningful data is retrieved from the
            map phase (i.e., when all map responses have a score of 0).
        _json_mode:
            Indicates whether the LLM returns responses in JSON format during
            the map phase (if supported by the LLM).
        _data_max_tokens:
            The maximum number of tokens allowed for input context during the
            map phase.
    """
    _chat_llm: _llm.BaseAsyncChatLLM
    _embedding: _llm.BaseEmbedding
    _context_builder: _context.GlobalContextBuilder
    _logger: typing.Optional[_base_engine.Logger]
    _token_encoder: tiktoken.Encoding
    _map_sys_prompt: str
    _reduce_sys_prompt: str
    _allow_general_knowledge: bool
    _general_knowledge_sys_prompt: str
    _no_data_answer: str
    _json_mode: bool
    _data_max_tokens: int
    _semaphore: asyncio.Semaphore

    @typing_extensions.override
    @property
    def context_builder(self) -> _context.GlobalContextBuilder:
        return self._context_builder

    def __init__(
        self,
        *,
        chat_llm: _llm.BaseAsyncChatLLM,
        embedding: _llm.BaseEmbedding,

        context_builder: typing.Optional[_context.GlobalContextBuilder] = None,
        context_loader: typing.Optional[_context.GlobalContextLoader] = None,

        community_level: typing.Optional[int] = None,
        map_sys_prompt: typing.Optional[str] = None,
        reduce_sys_prompt: typing.Optional[str] = None,
        allow_general_knowledge: typing.Optional[bool] = None,
        general_knowledge_sys_prompt: typing.Optional[str] = None,
        no_data_answer: typing.Optional[str] = None,
        json_mode: typing.Optional[bool] = None,
        max_data_tokens: typing.Optional[int] = None,
        encoding_model: typing.Optional[str] = None,
        concurrent_coroutines: typing.Optional[int] = None,

        logger: typing.Optional[_base_engine.Logger] = None,
        **kwargs: typing.Any,
    ) -> None:
        if logger:
            logger.debug(f"Creating AsyncGlobalSearchEngine with context_loader: {context_loader}")
        if not context_builder and not context_loader:
            raise ValueError("Either context_builder or context_loader must be provided")

        if context_loader:
            context_builder = context_loader.to_context_builder(
                community_level=community_level or _defaults.DEFAULT__GLOBAL_SEARCH__COMMUNITY_LEVEL,
                encoding_model=encoding_model or _defaults.DEFAULT__ENCODING_MODEL,
                **kwargs,
            )

        if logger:
            logger.debug(f"Created AsyncGlobalSearchEngine with context_builder: {context_builder}")
        context_builder = typing.cast(_context.GlobalContextBuilder, context_builder)
        super().__init__(
            chat_llm=chat_llm,
            embedding=embedding,
            context_builder=context_builder,
        )

        self._map_sys_prompt = map_sys_prompt or _defaults.GLOBAL_SEARCH__MAP__SYS_PROMPT
        self._reduce_sys_prompt = reduce_sys_prompt or _defaults.GLOBAL_SEARCH__REDUCE__SYS_PROMPT
        self._allow_general_knowledge = allow_general_knowledge if allow_general_knowledge is not None else True
        self._general_knowledge_sys_prompt = (general_knowledge_sys_prompt or
                                              _defaults.GLOBAL_SEARCH__REDUCE__GENERAL_KNOWLEDGE_INSTRUCTION)
        self._no_data_answer = no_data_answer or _defaults.GLOBAL_SEARCH__REDUCE__NO_DATA_ANSWER
        self._json_mode = json_mode if json_mode is not None else True
        self._data_max_tokens = max_data_tokens or _defaults.DEFAULT__GLOBAL_SEARCH__DATA_MAX_TOKENS
        self._token_encoder = tiktoken.get_encoding(encoding_model or _defaults.DEFAULT__ENCODING_MODEL)
        self._logger = logger
        self._semaphore = asyncio.Semaphore(concurrent_coroutines or _defaults.DEFAULT__CONCURRENT_COROUTINES)

    @typing_extensions.override
    async def asearch(
        self,
        query: str,
        *,
        conversation_history: _types.ConversationHistory_T,
        verbose: bool = False,
        stream: bool = False,
        map_sys_prompt: typing.Optional[str] = None,
        reduce_sys_prompt: typing.Optional[str] = None,
        general_knowledge_sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> typing.Union[_types.SearchResult_T, _types.AsyncStreamSearchResult_T]:
        """
        Executes a global search based on the given query asynchronously.

        The search consists of two phases:
        1. Map phase: Each community answers the query using its context.
        2. Reduce phase: The individual community answers are aggregated into a
                         global answer.

        Args:
            query: The query string for the search.
            conversation_history:
                The conversation history, which can be passed in as a list
                or a ConversationHistory object.
            verbose:
                If True, returns detailed results in the form of
                SearchResultVerbose or SearchResultChunkVerbose objects.
                Otherwise, returns basic SearchResult objects.
            stream:
                If True, enables streaming mode and returns an iterator of
                results. If False, returns results after the entire process
                completes.
            map_sys_prompt:
                A temporary prompt to override the default map system prompt for
                this search.
            reduce_sys_prompt:
                A temporary prompt to override the default reduce system prompt
                for this search.
            general_knowledge_sys_prompt:
                A temporary prompt to override the default general knowledge
                system prompt for this search.
            **kwargs:
                Additional keyword arguments, can be prefixed with 'map__' for
                `self._map` or 'reduce__' for `self._reduce` or not prefixed for
                `GlobalContextBuilder.build_context`. See details in the
                specific method documentation and source code.

        Returns:
            A search result object or a stream of search result chunks,
            depending on the value of `stream`.
        """
        created = time.time()
        self._logger.info(f"Starting search for query: {query} at {created}") if self._logger else None

        if conversation_history is None:
            conversation_history = _context.ConversationHistory()
        elif isinstance(conversation_history, list):
            conversation_history = _context.ConversationHistory.from_list(conversation_history)

        context_chunks, context_records = self._context_builder.build_context(
            conversation_history=conversation_history,
            **kwargs,
        )
        map_results = list(
            await asyncio.gather(
                *[self._map(
                    query=query,
                    context=context,
                    verbose=verbose,
                    map_sys_prompt=map_sys_prompt,
                    **kwargs
                ) for context in context_chunks]
            )
        )
        return await self._reduce(
            map_results=map_results,
            query=query,
            verbose=verbose,
            stream=stream,
            reduce_sys_prompt=reduce_sys_prompt,
            general_knowledge_sys_prompt=general_knowledge_sys_prompt,
            **kwargs
        )

    async def _map(
        self,
        *,
        query: str,
        context: str,
        verbose: bool,
        sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any
    ) -> _types.SearchResult_T:
        """
        Executes the map phase of the GraphRAG global search asynchronously.

        In this phase, each community answers the query based on its specific
        context data. The result is then used in the reduce phase to form the
        final answer.

        See https://arxiv.org/abs/2404.16130.

        Args:
            query:
                The query string for the search.
            context:
                The context data specific to a community, used in the map phase.
            verbose:
                If True, returns a detailed SearchResultVerbose object,
                otherwise returns a basic SearchResult object.
            sys_prompt:
                A temporary prompt to override the default map system prompt.
            **kwargs:
                Additional keyword arguments. Should be prefixed with 'map__'
                for `ChatLLM.chat` method. See details in the specific method
                documentation and source code.

        Returns:
            A SearchResult or SearchResultVerbose object, depending on the
            verbosity setting.
        """
        created = time.time()
        if self._logger:
            self._logger.info(f"Starting map for query: {query} at {created}")

        prompt = (sys_prompt or self._map_sys_prompt).format_map(
            collections.defaultdict(str, context_data=context, query=query)
        )
        msg = [{"role": "system", "content": prompt}, {"role": "user", "content": query}]

        if self._logger:
            self._logger.debug(f"Constructed messages: {msg}")

        async with self._semaphore:
            response = typing.cast(
                _llm.ChatResponse_T, (await self._chat_llm.achat(
                    msg=typing.cast(_llm.MessageParam_T, msg),
                    stream=False,
                    **_utils.filter_kwargs(self._chat_llm.achat, kwargs, prefix='map__')
                ))
            )
        result = self._parse_map(response)

        usage = _types.Usage(
            completion_tokens=response.usage.completion_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens,
        ) if response.usage else None

        if verbose:
            return _types.SearchResultVerbose(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=response.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=response.choices[0].finish_reason,
                    message=_types.Message(
                        content=result,
                        refusal=response.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
                context_data=None,
                context_text=context,
                completion_time=time.time() - created,
                llm_calls=1,
            )
        else:
            return _types.SearchResult(
                created=created.__int__(),
                model=self._chat_llm.model,
                system_fingerprint=response.system_fingerprint,
                choice=_types.Choice(
                    finish_reason=response.choices[0].finish_reason,
                    message=_types.Message(
                        content=result,
                        refusal=response.choices[0].message.refusal,
                    ),
                ),
                usage=usage,
            )

    @staticmethod
    def _parse_map(response: _llm.ChatResponse_T) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Converts the response from the map phase into a list of key points.
        """
        default = [{"answer": "", "score": 0}]
        json_ = _utils.deserialize_json(response.choices[0].message.content or "")
        if json_ == {}:
            return default

        points = json_.get("points", [])
        if not isinstance(points, list):
            return default

        return [
            {"answer": point["description"], "score": int(point["score"])}
            for point in points
            if isinstance(point, dict) and "description" in point and "score" in point
        ]

    async def _reduce(
        self,
        *,
        map_results: typing.List[_types.SearchResult_T],
        query: str,
        verbose: bool,
        stream: bool,
        reduce_sys_prompt: typing.Optional[str] = None,
        general_knowledge_sys_prompt: typing.Optional[str] = None,
        **kwargs: typing.Any
    ) -> typing.Union[_types.SearchResult_T, _types.AsyncStreamSearchResult_T]:
        """
        Executes the reduce phase of the GraphRAG global search asynchronously.

        In this phase, the individual results from the map phase are combined
        into a final global answer. Optionally, general knowledge prompts can
        be applied.

        See https://arxiv.org/abs/2404.16130.

        Args:
            map_results: A list of search results from the map phase.
            query: The query string for the search.
            verbose:
                If True, returns detailed results in the form of
                SearchResultVerbose or SearchResultChunkVerbose objects.
                Otherwise, returns basic SearchResult objects.
            stream:
                If True, enables streaming mode and returns an iterator of
                results. If False, returns results after the entire process
                completes.
            reduce_sys_prompt:
                A temporary prompt to override the default reduce system prompt
                for this search.
            general_knowledge_sys_prompt:
                A temporary prompt to override the default general knowledge
                system prompt for this search.
            **kwargs:
                Additional keyword arguments. Should be prefixed with 'reduce__'
                for `ChatLLM.chat` method. See details in the specific method
                documentation and source code.

        Returns:
            A search result object or a stream of search result chunks,
            depending on the value of `stream`.
        """
        created = time.time()
        if self._logger:
            self._logger.info(f"Starting reduce for query: {query} at {created}")

        key_points: typing.List[typing.Dict[str, typing.Any]] = []
        for idx, map_ in enumerate(map_results):
            if not isinstance(map_.choice.message.content, list):
                continue
            for ele in map_.choice.message.content:
                if not isinstance(ele, dict) or "answer" not in ele or "score" not in ele:
                    continue
                key_points.append(
                    {
                        "analyst": idx,
                        "answer":  ele["answer"],
                        "score":   ele["score"]
                    }
                )

        key_points = [kp for kp in key_points if isinstance(kp["score"], (int, float)) and kp["score"] > 0]

        if not key_points.__len__() and not self._allow_general_knowledge:
            warnings.warn("No key points found from the map phase", _errors.GraphRAGWarning)
            if self._logger:
                self._logger.warning("No key points found from the map phase")
            return _types.SearchResult(
                created=created.__int__(),
                model=self._chat_llm.model,
                choice=_types.Choice(
                    finish_reason="stop",
                    message=_types.Message(
                        content=self._no_data_answer,
                    ),
                ),
                usage=None,
            ) if not verbose else _types.SearchResultVerbose(
                created=created.__int__(),
                model=self._chat_llm.model,
                choice=_types.Choice(
                    finish_reason="stop",
                    message=_types.Message(
                        content=self._no_data_answer,
                    ),
                ),
                completion_time=time.time() - created,
                llm_calls=0,
            )

        key_points = sorted(
            key_points,
            key=lambda kp: kp["score"] if isinstance(kp["score"], (int, float)) else 0,
            reverse=True
        )
        if self._logger:
            self._logger.info(f"Key points found: {key_points}")

        data: typing.List[str] = []
        total_tokens = 0
        for kp in key_points:
            formatted_response = '\n'.join(
                [f'----Analyst {kp["analyst"] + 1}----', f'Importance score: {kp["score"]}', kp["answer"]]
            )
            total_tokens += _utils.num_tokens(formatted_response, self._token_encoder)
            if total_tokens > self._data_max_tokens:
                warnings.warn("Data exceeds maximum token limit", _errors.GraphRAGWarning)
                break
            data.append(formatted_response)

        report_data = '\n\n'.join(data)
        prompt = (reduce_sys_prompt or self._reduce_sys_prompt).format_map(
            collections.defaultdict(str, report_data=report_data)
        )
        if self._allow_general_knowledge:
            prompt += f'\n{general_knowledge_sys_prompt or self._general_knowledge_sys_prompt}'

        msg = [{"role": "system", "content": prompt}, {"role": "user", "content": query}]
        if self._logger:
            self._logger.debug(f"Constructed messages: {msg}")

        async with self._semaphore:
            response = await self._chat_llm.achat(
                msg=typing.cast(_llm.MessageParam_T, msg),
                stream=stream,
                **_utils.filter_kwargs(self._chat_llm.achat, kwargs, prefix='reduce__')
            )

        if stream:
            response = typing.cast(_llm.AsyncChatStreamResponse_T, response)
            return self._parse_stream_result(
                response,
                verbose=verbose,
                created=created,
                context_data=None,
                context_text=report_data,
                map_result=map_results,
                reduce_context_data=None,
                reduce_context_text=report_data,
            )
        else:
            response = typing.cast(_llm.ChatResponse_T, response)
            return self._parse_result(
                response,
                verbose=verbose,
                created=created,
                context_data=None,
                context_text=report_data,
                map_result=map_results,
                reduce_context_data=None,
                reduce_context_text=report_data,
            )

    @typing_extensions.override
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}( \n"
            f"\tchat_llm={self._chat_llm}, \n"
            f"\tembedding={self._embedding}, \n"
            f"\tcontext_builder={self._context_builder}, \n"
            f"\tlogger={self._logger}\n"
            f"\tmap_sys_prompt={self._map_sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._map_sys_prompt) > 50 else ''}, \n"
            f"\treduce_sys_prompt={self._reduce_sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._reduce_sys_prompt) > 50 else ''}, \n"
            f"\tallow_general_knowledge={self._allow_general_knowledge}, \n"
            f"\tgeneral_knowledge_sys_prompt={self._general_knowledge_sys_prompt[:50].__repr__()}"
            f"{'...' if len(self._general_knowledge_sys_prompt) > 50 else ''}, \n"
            f"\tno_data_answer={self._no_data_answer.__repr__()}, \n"
            f"\tjson_mode={self._json_mode}, \n"
            f"\tdata_max_tokens={self._data_max_tokens} \n"
            f")"
        )

    @typing_extensions.override
    def __repr__(self) -> str:
        return self.__str__()
