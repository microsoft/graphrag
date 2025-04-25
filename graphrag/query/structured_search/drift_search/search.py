# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""DRIFT Search implementation."""

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import tiktoken
from tqdm.asyncio import tqdm_asyncio

from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.language_model.protocol.base import ChatModel
from graphrag.language_model.providers.fnllm.utils import (
    get_openai_model_parameters_from_dict,
)
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.llm.text_utils import num_tokens
from graphrag.query.structured_search.base import BaseSearch, SearchResult
from graphrag.query.structured_search.drift_search.action import DriftAction
from graphrag.query.structured_search.drift_search.drift_context import (
    DRIFTSearchContextBuilder,
)
from graphrag.query.structured_search.drift_search.primer import DRIFTPrimer
from graphrag.query.structured_search.drift_search.state import QueryState
from graphrag.query.structured_search.local_search.search import LocalSearch

log = logging.getLogger(__name__)


class DRIFTSearch(BaseSearch[DRIFTSearchContextBuilder]):
    """Class representing a DRIFT Search."""

    def __init__(
        self,
        model: ChatModel,
        context_builder: DRIFTSearchContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        query_state: QueryState | None = None,
        callbacks: list[QueryCallbacks] | None = None,
    ):
        """
        Initialize the DRIFTSearch class.

        Args:
            llm (ChatOpenAI): The language model used for searching.
            context_builder (DRIFTSearchContextBuilder): Builder for search context.
            config (DRIFTSearchConfig, optional): Configuration settings for DRIFTSearch.
            token_encoder (tiktoken.Encoding, optional): Token encoder for managing tokens.
            query_state (QueryState, optional): State of the current search query.
        """
        super().__init__(model, context_builder, token_encoder)

        self.context_builder = context_builder
        self.token_encoder = token_encoder
        self.query_state = query_state or QueryState()
        self.primer = DRIFTPrimer(
            config=self.context_builder.config,
            chat_model=model,
            token_encoder=token_encoder,
        )
        self.callbacks = callbacks or []
        self.local_search = self.init_local_search()

    def init_local_search(self) -> LocalSearch:
        """
        Initialize the LocalSearch object with parameters based on the DRIFT search configuration.

        Returns
        -------
        LocalSearch: An instance of the LocalSearch class with the configured parameters.
        """
        local_context_params = {
            "text_unit_prop": self.context_builder.config.local_search_text_unit_prop,
            "community_prop": self.context_builder.config.local_search_community_prop,
            "top_k_mapped_entities": self.context_builder.config.local_search_top_k_mapped_entities,
            "top_k_relationships": self.context_builder.config.local_search_top_k_relationships,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,
            "max_context_tokens": self.context_builder.config.local_search_max_data_tokens,
        }

        model_params = get_openai_model_parameters_from_dict({
            "model": self.model.config.model,
            "max_tokens": self.context_builder.config.local_search_llm_max_gen_tokens,
            "temperature": self.context_builder.config.local_search_temperature,
            "n": self.context_builder.config.local_search_n,
            "top_p": self.context_builder.config.local_search_top_p,
            "max_completion_tokens": self.context_builder.config.local_search_llm_max_gen_completion_tokens,
            "response_format": {"type": "json_object"},
        })

        return LocalSearch(
            model=self.model,
            system_prompt=self.context_builder.local_system_prompt,
            context_builder=self.context_builder.local_mixed_context,
            token_encoder=self.token_encoder,
            model_params=model_params,
            context_builder_params=local_context_params,
            response_type="multiple paragraphs",
            callbacks=self.callbacks,
        )

    def _process_primer_results(
        self, query: str, search_results: SearchResult
    ) -> DriftAction:
        """
        Process the results from the primer search to extract intermediate answers and follow-up queries.

        Args:
            query (str): The original search query.
            search_results (SearchResult): The results from the primer search.

        Returns
        -------
        DriftAction: Action generated from the primer response.

        Raises
        ------
        RuntimeError: If no intermediate answers or follow-up queries are found in the primer response.
        """
        response = search_results.response
        if isinstance(response, list) and isinstance(response[0], dict):
            intermediate_answers = [
                i["intermediate_answer"] for i in response if "intermediate_answer" in i
            ]

            if not intermediate_answers:
                error_msg = "No intermediate answers found in primer response. Ensure that the primer response includes intermediate answers."
                raise RuntimeError(error_msg)

            intermediate_answer = "\n\n".join([
                i["intermediate_answer"] for i in response if "intermediate_answer" in i
            ])

            follow_ups = [fu for i in response for fu in i.get("follow_up_queries", [])]

            if not follow_ups:
                error_msg = "No follow-up queries found in primer response. Ensure that the primer response includes follow-up queries."
                raise RuntimeError(error_msg)

            score = sum(i.get("score", float("-inf")) for i in response) / len(response)
            response_data = {
                "intermediate_answer": intermediate_answer,
                "follow_up_queries": follow_ups,
                "score": score,
            }
            return DriftAction.from_primer_response(query, response_data)
        error_msg = "Response must be a list of dictionaries."
        raise ValueError(error_msg)

    async def _search_step(
        self, global_query: str, search_engine: LocalSearch, actions: list[DriftAction]
    ) -> list[DriftAction]:
        """
        Perform an asynchronous search step by executing each DriftAction asynchronously.

        Args:
            global_query (str): The global query for the search.
            search_engine (LocalSearch): The local search engine instance.
            actions (list[DriftAction]): A list of actions to perform.

        Returns
        -------
        list[DriftAction]: The results from executing the search actions asynchronously.
        """
        tasks = [
            action.search(search_engine=search_engine, global_query=global_query)
            for action in actions
        ]
        return await tqdm_asyncio.gather(*tasks, leave=False)

    async def search(
        self,
        query: str,
        conversation_history: Any = None,
        reduce: bool = True,
        **kwargs,
    ) -> SearchResult:
        """
        Perform an asynchronous DRIFT search.

        Args:
            query (str): The query to search for.
            conversation_history (Any, optional): The conversation history, if any.
            reduce (bool, optional): Whether to reduce the response to a single comprehensive response.

        Returns
        -------
        SearchResult: The search result containing the response and context data.

        Raises
        ------
        ValueError: If the query is empty.
        """
        if query == "":
            error_msg = "DRIFT Search query cannot be empty."
            raise ValueError(error_msg)

        llm_calls, prompt_tokens, output_tokens = {}, {}, {}

        start_time = time.perf_counter()

        # Check if query state is empty
        if not self.query_state.graph:
            # Prime the search with the primer
            primer_context, token_ct = await self.context_builder.build_context(query)
            llm_calls["build_context"] = token_ct["llm_calls"]
            prompt_tokens["build_context"] = token_ct["prompt_tokens"]
            output_tokens["build_context"] = token_ct["output_tokens"]

            primer_response = await self.primer.search(
                query=query, top_k_reports=primer_context
            )
            llm_calls["primer"] = primer_response.llm_calls
            prompt_tokens["primer"] = primer_response.prompt_tokens
            output_tokens["primer"] = primer_response.output_tokens

            # Package response into DriftAction
            init_action = self._process_primer_results(query, primer_response)
            self.query_state.add_action(init_action)
            self.query_state.add_all_follow_ups(init_action, init_action.follow_ups)

        # Main loop
        epochs = 0
        llm_call_offset = 0
        while epochs < self.context_builder.config.n_depth:
            actions = self.query_state.rank_incomplete_actions()
            if len(actions) == 0:
                log.info("No more actions to take. Exiting DRIFT loop.")
                break
            actions = actions[: self.context_builder.config.drift_k_followups]
            llm_call_offset += (
                len(actions) - self.context_builder.config.drift_k_followups
            )
            # Process actions
            results = await self._search_step(
                global_query=query, search_engine=self.local_search, actions=actions
            )

            # Update query state
            for action in results:
                self.query_state.add_action(action)
                self.query_state.add_all_follow_ups(action, action.follow_ups)
            epochs += 1

        t_elapsed = time.perf_counter() - start_time

        # Calculate token usage
        token_ct = self.query_state.action_token_ct()
        llm_calls["action"] = token_ct["llm_calls"]
        prompt_tokens["action"] = token_ct["prompt_tokens"]
        output_tokens["action"] = token_ct["output_tokens"]

        # Package up context data
        response_state, context_data, context_text = self.query_state.serialize(
            include_context=True
        )

        reduced_response = response_state
        if reduce:
            # Reduce response_state to a single comprehensive response
            for callback in self.callbacks:
                callback.on_reduce_response_start(response_state)

            model_params = get_openai_model_parameters_from_dict({
                "model": self.model.config.model,
                "max_tokens": self.context_builder.config.reduce_max_tokens,
                "temperature": self.context_builder.config.reduce_temperature,
                "max_completion_tokens": self.context_builder.config.reduce_max_completion_tokens,
            })

            reduced_response = await self._reduce_response(
                responses=response_state,
                query=query,
                llm_calls=llm_calls,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
                model_params=model_params,
            )

            for callback in self.callbacks:
                callback.on_reduce_response_end(reduced_response)
        return SearchResult(
            response=reduced_response,
            context_data=context_data,
            context_text=context_text,
            completion_time=t_elapsed,
            llm_calls=sum(llm_calls.values()),
            prompt_tokens=sum(prompt_tokens.values()),
            output_tokens=sum(output_tokens.values()),
            llm_calls_categories=llm_calls,
            prompt_tokens_categories=prompt_tokens,
            output_tokens_categories=output_tokens,
        )

    async def stream_search(
        self, query: str, conversation_history: ConversationHistory | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Perform a streaming DRIFT search asynchronously.

        Args:
            query (str): The query to search for.
            conversation_history (ConversationHistory, optional): The conversation history.
        """
        result = await self.search(
            query=query, conversation_history=conversation_history, reduce=False
        )

        if isinstance(result.response, list):
            result.response = result.response[0]

        for callback in self.callbacks:
            callback.on_reduce_response_start(result.response)

        model_params = get_openai_model_parameters_from_dict({
            "model": self.model.config.model,
            "max_tokens": self.context_builder.config.reduce_max_tokens,
            "temperature": self.context_builder.config.reduce_temperature,
            "max_completion_tokens": self.context_builder.config.reduce_max_completion_tokens,
        })

        full_response = ""
        async for resp in self._reduce_response_streaming(
            responses=result.response,
            query=query,
            model_params=model_params,
        ):
            full_response += resp
            yield resp

        for callback in self.callbacks:
            callback.on_reduce_response_end(full_response)

    async def _reduce_response(
        self,
        responses: str | dict[str, Any],
        query: str,
        llm_calls: dict[str, int],
        prompt_tokens: dict[str, int],
        output_tokens: dict[str, int],
        **llm_kwargs,
    ) -> str:
        """Reduce the response to a single comprehensive response.

        Parameters
        ----------
        responses : str|dict[str, Any]
            The responses to reduce.
        query : str
            The original query.
        llm_kwargs : dict[str, Any]
            Additional keyword arguments to pass to the LLM.

        Returns
        -------
        str
            The reduced response.
        """
        reduce_responses = []

        if isinstance(responses, str):
            reduce_responses = [responses]
        else:
            reduce_responses = [
                response["answer"]
                for response in responses.get("nodes", [])
                if response.get("answer")
            ]

        search_prompt = self.context_builder.reduce_system_prompt.format(
            context_data=reduce_responses,
            response_type=self.context_builder.response_type,
        )
        search_messages = [
            {"role": "system", "content": search_prompt},
        ]

        model_response = await self.model.achat(
            prompt=query,
            history=search_messages,
            model_parameters=llm_kwargs,
        )

        reduced_response = model_response.output.content

        llm_calls["reduce"] = 1
        prompt_tokens["reduce"] = num_tokens(
            search_prompt, self.token_encoder
        ) + num_tokens(query, self.token_encoder)
        output_tokens["reduce"] = num_tokens(reduced_response, self.token_encoder)

        return reduced_response

    async def _reduce_response_streaming(
        self,
        responses: str | dict[str, Any],
        query: str,
        model_params: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Reduce the response to a single comprehensive response.

        Parameters
        ----------
        responses : str|dict[str, Any]
            The responses to reduce.
        query : str
            The original query.

        Returns
        -------
        str
            The reduced response.
        """
        reduce_responses = []

        if isinstance(responses, str):
            reduce_responses = [responses]
        else:
            reduce_responses = [
                response["answer"]
                for response in responses.get("nodes", [])
                if response.get("answer")
            ]

        search_prompt = self.context_builder.reduce_system_prompt.format(
            context_data=reduce_responses,
            response_type=self.context_builder.response_type,
        )
        search_messages = [
            {"role": "system", "content": search_prompt},
        ]

        async for response in self.model.achat_stream(
            prompt=query,
            history=search_messages,
            model_parameters=model_params,
        ):
            for callback in self.callbacks:
                callback.on_llm_new_token(response)
            yield response
