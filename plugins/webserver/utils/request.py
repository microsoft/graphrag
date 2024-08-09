from typing import Dict

from graphrag.query.structured_search.base import BaseSearch
from plugins.webserver import prompt
from plugins.webserver.service.graphrag.universal import build_search_engine
from plugins.webserver.types import GraphRAGItem


class AsyncSearchEngineContext:
    def __init__(self, search_engine_args: Dict, request: GraphRAGItem):
        self.search_engine_args: dict = search_engine_args
        self.request: GraphRAGItem = request
        self.other_search_kwargs = {}

    async def __aenter__(self):
        if self.request.source == "qa":
            system_prompt = prompt.LOCAL_SEARCH_FOR_QA_SYSTEM_PROMPT
        else:  # chat
            system_prompt = prompt.LOCAL_SEARCH_FOR_CHAT_SYSTEM_PROMPT
            self.other_search_kwargs['add_history_to_search_messages'] = True  # add history to search messages when chat mode

        if self.request.response_max_token:
            llm_params = {
                'max_tokens': self.request.response_max_token
            }
        else:
            llm_params = {}

        if self.request.context_max_token:
            context_builder_params = {
                'max_tokens': self.request.context_max_token
            }
        else:
            context_builder_params = {}

        # update search engine args
        self.search_engine_args.update(
            {
                'system_prompt': system_prompt,
                'llm_params': llm_params,
                'context_builder_params': context_builder_params,
            }
        )

        # instance a search engine
        search_engine: BaseSearch = build_search_engine(
            mode=self.request.method,
            **self.search_engine_args,
        )
        self.search_engine = search_engine

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False
