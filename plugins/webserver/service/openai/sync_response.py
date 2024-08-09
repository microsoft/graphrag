from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.structured_search.base import BaseSearch
from plugins.webserver import utils
from plugins.webserver.types import GraphRAGResponseItem


async def handle_sync_response(question_list: list, reference: dict, search: BaseSearch, conversation_history: ConversationHistory,
                               search_other_kwargs: dict = None):
    result = await search.asearch(str(question_list), conversation_history=conversation_history, **search_other_kwargs)
    response = result.response
    # delete reference in origin response
    cleaned_response = utils.delete_reference(response)

    graphrag_response = GraphRAGResponseItem(
        code=200,
        message="success",
        reference=reference,
        data=cleaned_response,
        question=question_list,
        other={
            "origin_response": response,
            "prompt_token": result.prompt_tokens
        }
    )

    return JSONResponse(content=jsonable_encoder(graphrag_response))
