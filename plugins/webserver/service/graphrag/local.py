import tiktoken

from graphrag.query.context_builder.builders import LocalContextBuilder
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.llm.base import BaseLLM
from graphrag.query.structured_search.local_search.search import LocalSearch
from plugins.webserver import prompt
from plugins.webserver.config.final_config import FinalConfig


def build_local_search_engine(llm: BaseLLM,
                              config: FinalConfig,
                              token_encoder: tiktoken.Encoding,
                              context_builder: LocalContextBuilder = None,
                              **kwargs) -> LocalSearch:
    ls_config = config.local_search

    llm_params = {
        "max_tokens": ls_config.llm_max_tokens,
        # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
        "temperature": ls_config.temperature,
        "top_p": ls_config.top_p,
        "n": ls_config.n,
    }
    context_builder_params = {
        "text_unit_prop": ls_config.text_unit_prop,
        "community_prop": ls_config.community_prop,
        "conversation_history_max_turns": ls_config.conversation_history_max_turns,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": ls_config.top_k_entities,
        "top_k_relationships": ls_config.top_k_relationships,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": ls_config.max_tokens,
        # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
    }

    context_builder_params.update(kwargs.get('context_builder_params', {}))

    llm_params.update(kwargs.get('llm_params', {}))

    return LocalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        system_prompt=kwargs.get('system_prompt', None) or prompt.LOCAL_SEARCH_FOR_QA_SYSTEM_PROMPT,
        llm_params=llm_params,
        context_builder_params=context_builder_params,
        response_type=kwargs.get('response_type', None) or config.query.response_type,
    )
