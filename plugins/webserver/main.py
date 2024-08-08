import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException

from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.structured_search.base import BaseSearch
from plugins.webserver import utils
from plugins.webserver.types import DomainEnum, SearchModeEnum, GraphRAGItem

from plugins.webserver.service import graphrag as graphrag_service
from plugins.webserver.service import openai as openai_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# global variable
all_search_engine: Dict[DomainEnum, Dict[SearchModeEnum, BaseSearch]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global all_search_engine
    all_search_engine = graphrag_service.init_env()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/graphrag")
async def run(request: GraphRAGItem):
    if not all_search_engine:
        logger.error("Failed initializing search engines")
        raise HTTPException(status_code=500, detail="graphrag search engines is not initialized")

    try:
        # history
        conversation_history = ConversationHistory.from_list([dict(message) for message in request.messages[:-1]])

        # handle model
        domain, search_mode = request.domain.value, request.method.value

        # get search engine
        search_engine = all_search_engine[DomainEnum(domain)][SearchModeEnum(search_mode)]

        # generate question list by user chat context via llm
        question_list = await utils.context_to_question(request.messages, search_engine.llm)

        # filter question by bm25
        filtered_question_list, context_document_ids = utils.filter_question_by_bm25(question_list, search_engine.context_builder)
        # get reference
        reference = await utils.get_reference(search_engine.context_builder, context_document_ids, filtered_question_list, search_engine.llm)

        print(reference)
        if not request.stream:
            return await openai_service.handle_sync_response(filtered_question_list, reference, search_engine, conversation_history)
        else:
            return await openai_service.handle_stream_response(filtered_question_list, reference, search_engine, conversation_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
