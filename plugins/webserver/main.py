import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException

from graphrag.query.context_builder.conversation_history import ConversationHistory
from plugins.webserver import utils
from plugins.webserver.types import DomainEnum, SearchModeEnum, GraphRAGItem, SourceEnum, GraphRAGResponseItem

from plugins.webserver.service import graphrag as graphrag_service
from plugins.webserver.service import openai as openai_service
from plugins.webserver.utils.request import AsyncSearchEngineContext

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# global variable
all_search_engine_args: Dict[DomainEnum, Dict[SearchModeEnum, Dict]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global all_search_engine_args
    all_search_engine_args = graphrag_service.init_env()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/graphrag")
async def run(request: GraphRAGItem):
    if not all_search_engine_args:
        logger.error("Failed initializing search engines")
        raise HTTPException(status_code=500, detail="graphrag search engines is not initialized")

    try:
        # history
        conversation_history = ConversationHistory.from_list([dict(message) for message in request.messages[:-1]])

        # handle model
        domain, search_mode = request.domain.value, request.method.value

        # get search engine
        search_engine_args = all_search_engine_args[DomainEnum(domain)][SearchModeEnum(search_mode)]

        # del last search engine variable if exists
        [search_engine_args.pop(arg, None) for arg in ['system_prompt', 'llm_params', 'context_builder_params']]

        async with AsyncSearchEngineContext(search_engine_args, request) as current_search_engine:
            search_engine = current_search_engine.search_engine
            match request.source:
                case SourceEnum.qa:
                    try:
                        question_list = await utils.context_to_question(request.messages, search_engine.llm)
                    except:
                        return GraphRAGResponseItem(code=204, message="refuse answer", reference={}, question=[], data={})

                    # filter question by bm25
                    filtered_question_list, context_document_ids = utils.filter_question_by_bm25(question_list, search_engine.context_builder)
                    # get reference
                    reference = await utils.get_reference(search_engine.context_builder, context_document_ids, filtered_question_list, search_engine.llm)
                case SourceEnum.chat:
                    filtered_question_list = [request.messages[-1].content]
                    reference = {}
                case _:
                    raise HTTPException(status_code=400, detail="Invalid source")

            if not request.stream:
                result = await openai_service.handle_sync_response(filtered_question_list, reference, search_engine, conversation_history,
                                                                   current_search_engine.other_search_kwargs)
            else:
                result = await openai_service.handle_stream_response(filtered_question_list, reference, search_engine, conversation_history,
                                                                     current_search_engine.other_search_kwargs)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
