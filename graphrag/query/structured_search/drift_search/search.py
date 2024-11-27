# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""DRIFT Search implementation."""

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import tiktoken
from tqdm.asyncio import tqdm_asyncio

from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
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
        llm: ChatOpenAI,
        context_builder: DRIFTSearchContextBuilder,
        config: DRIFTSearchConfig | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        query_state: QueryState | None = None,
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
        super().__init__(llm, context_builder, token_encoder)

        self.config = config or DRIFTSearchConfig()
        self.context_builder = context_builder
        self.token_encoder = token_encoder
        self.query_state = query_state or QueryState()
        self.primer = DRIFTPrimer(
            config=self.config, chat_llm=llm, token_encoder=token_encoder
        )
        self.local_search = self.init_local_search()

    def init_local_search(self) -> LocalSearch:
        """
        Initialize the LocalSearch object with parameters based on the DRIFT search configuration.

        Returns
        -------
        LocalSearch: An instance of the LocalSearch class with the configured parameters.
        """
        local_context_params = {
            "text_unit_prop": self.config.local_search_text_unit_prop,
            "community_prop": self.config.local_search_community_prop,
            "top_k_mapped_entities": self.config.local_search_top_k_mapped_entities,
            "top_k_relationships": self.config.local_search_top_k_relationships,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,
            "max_tokens": self.config.local_search_max_data_tokens,
        }

        llm_params = {
            "max_tokens": self.config.local_search_llm_max_gen_tokens,
            "temperature": self.config.local_search_temperature,
            "response_format": {"type": "json_object"},
        }

        return LocalSearch(
            llm=self.llm,
            system_prompt=self.context_builder.local_system_prompt,
            context_builder=self.context_builder.local_mixed_context,
            token_encoder=self.token_encoder,
            llm_params=llm_params,
            context_builder_params=local_context_params,
            response_type="multiple paragraphs",
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

    async def asearch_step(
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
            action.asearch(search_engine=search_engine, global_query=global_query)
            for action in actions
        ]
        return await tqdm_asyncio.gather(*tasks, leave=False)

    async def asearch(
        self,
        query: str,
        conversation_history: Any = None,
        **kwargs,
    ) -> SearchResult:
        """
        Perform an asynchronous DRIFT search.

        Args:
            query (str): The query to search for.
            conversation_history (Any, optional): The conversation history, if any.

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
            primer_context, token_ct = self.context_builder.build_context(query)
            llm_calls["build_context"] = token_ct["llm_calls"]
            prompt_tokens["build_context"] = token_ct["prompt_tokens"]
            output_tokens["build_context"] = token_ct["prompt_tokens"]

            primer_response = await self.primer.asearch(
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
        while epochs < self.config.n:
            actions = self.query_state.rank_incomplete_actions()
            if len(actions) == 0:
                log.info("No more actions to take. Exiting DRIFT loop.")
                break
            actions = actions[: self.config.drift_k_followups]
            llm_call_offset += len(actions) - self.config.drift_k_followups
            # Process actions
            results = await self.asearch_step(
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

        return SearchResult(
            response=response_state,
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

    def search(
        self,
        query: str,
        conversation_history: Any = None,
        **kwargs,
    ) -> SearchResult:
        """
        Perform a synchronous DRIFT search (Not Implemented).

        Args:
            query (str): The query to search for.
            conversation_history (Any, optional): The conversation history.

        Raises
        ------
        NotImplementedError: Synchronous DRIFT is not implemented.
        """
        error_msg = "Synchronous DRIFT is not implemented."
        raise NotImplementedError(error_msg)

    def astream_search(
        self, query: str, conversation_history: ConversationHistory | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Perform a streaming DRIFT search (Not Implemented).

        Args:
            query (str): The query to search for.
            conversation_history (ConversationHistory, optional): The conversation history.

        Raises
        ------
        NotImplementedError: Streaming DRIFT search is not implemented.
        """
        error_msg = "Streaming DRIFT search is not implemented."
        raise NotImplementedError(error_msg)
