from collections.abc import AsyncGenerator
import logging
from typing import Any, List
import tiktoken
from tqdm.asyncio import tqdm_asyncio

from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.structured_search.base import BaseSearch, SearchResult
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.query.structured_search.drift_search.action import DriftAction
from graphrag.query.structured_search.drift_search.state import QueryState
from graphrag.query.structured_search.drift_search.drift_context import DRIFTSearchContextBuilder
from graphrag.query.structured_search.drift_search.primer import DRIFTPrimer
from graphrag.config.models.drift_config import DRIFTSearchConfig


log = logging.getLogger(__name__)


class DRIFTSearch(BaseSearch):
    def __init__(
            self,
            llm: ChatOpenAI,
            context_builder: DRIFTSearchContextBuilder,
            config: DRIFTSearchConfig | None = None,
            token_encoder: tiktoken.Encoding | None = None, # TODO: implement token counting
            query_state: QueryState | None = None,
    ):
        super().__init__(llm, context_builder, token_encoder)

        self.config = config or DRIFTSearchConfig()
        self.context_builder = context_builder
        self.token_encoder = token_encoder
        self.query_state = query_state or QueryState()
        self.primer = DRIFTPrimer(config=self.config, chat_llm=llm, token_encoder=token_encoder)
        self.local_search = self.init_local_search()


    def init_local_search(self):

        local_context_params = {
            "text_unit_prop": self.config.local_search_text_unit_prop,
            "community_prop": self.config.local_search_community_prop,
            "top_k_mapped_entities": self.config.local_search_top_k_mapped_entities,
            "top_k_relationships": self.config.local_search_top_k_relationships,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
            "max_tokens": self.config.local_search_max_data_tokens, 
        }

        llm_params = {
            "max_tokens": self.config.local_search_llm_max_gen_tokens,
            "temperature": self.config.local_search_temperature,
            "response_format": {"type": "json_object"} 
        }


        return LocalSearch(
            llm=self.llm,
            system_prompt=self.context_builder.local_system_prompt,
            context_builder=self.context_builder.local_mixed_context,
            token_encoder=self.token_encoder,
            llm_params=llm_params,
            context_builder_params=local_context_params,
            response_type="multiple paragraphs" # this has no bearing on the obj returned by OAI, only the format of the response within the obj returned by OAI.
        )


    def _process_primer_results(self, query:str, search_results: SearchResult) -> DriftAction:
        response = search_results.response
        if isinstance(response, list) and isinstance(response[0], dict):
            intermediate_answer = "\n\n".join([i['intermediate_answer'] for i in response])
            follow_ups = [fu for i in response for fu in i['follow_up_queries']]
            score = sum([i['score'] for i in response]) / len(response)
            response = {'intermediate_answer': intermediate_answer, 'follow_up_queries': follow_ups, 'score': score}
            return DriftAction.from_primer_response(query, response)
        else:
            raise ValueError(f'Response must be a list of dictionaries. Found: {type(response)}')


    # hard coded to use local search, but will be updated to use a general meta search engine
    async def asearch_step(self, global_query:str, search_engine: LocalSearch, actions: List[DriftAction]) -> List[DriftAction]:
        tasks = [action.asearch(search_engine=search_engine, global_query=global_query) for action in actions]
        results = await tqdm_asyncio.gather(*tasks)
        return results

    async def asearch(
            self,
            query: str,
            conversation_history: Any = None,
            **kwargs,
    ) -> SearchResult:


        ## Check if query state is empty. Are there follow-up actions?
        if not self.query_state.graph:
            # Prime the search with the primer
            primer_context = self.context_builder.build_primer_context(query) # pd.DataFrame
            primer_response = await self.primer.asearch(query=query, top_k_reports=primer_context)
            ## Package response into DriftAction
            init_action = self._process_primer_results(query, primer_response)
            self.query_state.add_action(init_action)
            self.query_state.add_all_follow_ups(init_action, init_action.follow_ups)

        ## Main loop ##

        steps = 0

        while steps < self.config.n:
            ## Rank actions
            actions = self.query_state.rank_incomplete_actions()
            if not actions:
                log.info("No more actions to take. Exiting DRIFT loop..")
                break
            ## Take the top k actions
            actions = actions[:self.config.search_primer_k]
            ## Process actions
            results = await self.asearch_step(global_query=query, search_engine=self.local_search, actions=actions) # currently harcoded to local search, but will be updated to use a more general search engine

            ## Update query state
            for action in results:
                self.query_state.add_action(action)
                self.query_state.add_all_follow_ups(action, action.follow_ups)
            steps += 1

        return SearchResult(
            response=self.query_state.serialize(),
            context_data='test',
            context_text='testing_only',
            completion_time=0,
            llm_calls=0,
            prompt_tokens=0
        )

    def search(
            self,
            query: str,
            conversation_history: Any = None,
            **kwargs,) -> SearchResult:

        raise NotImplementedError("Synchronous DRIFT is not implemented.")

    def astream_search(self, query: str, conversation_history: ConversationHistory | None = None) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Streaming DRIFT search is not implemented.")
