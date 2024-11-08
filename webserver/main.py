import logging
import os
import time
import uuid

import tiktoken
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.llm.oai import ChatOpenAI, OpenAIEmbedding
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.base import BaseSearch
from graphrag.query.structured_search.drift_search.search import DRIFTSearch
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.search import LocalSearch
from webserver import gtypes
from webserver import search
from webserver import utils
from webserver.configs import settings
from webserver.search.localsearch import build_drift_search_context
from webserver.utils import consts

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="webserver/static"), name="static")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    api_key=settings.llm.api_key,
    api_base=settings.llm.api_base,
    model=settings.llm.model,
    api_type=settings.get_api_type(),
    max_retries=settings.llm.max_retries,
    azure_ad_token_provider=settings.azure_ad_token_provider(),
    deployment_name=settings.llm.deployment_name,
    api_version=settings.llm.api_version,
    organization=settings.llm.organization,
    request_timeout=settings.llm.request_timeout,
)

text_embedder = OpenAIEmbedding(
    api_key=settings.embeddings.llm.api_key,
    api_base=settings.embeddings.llm.api_base,
    api_type=settings.get_api_type(),
    api_version=settings.embeddings.llm.api_version,
    model=settings.embeddings.llm.model,
    max_retries=settings.embeddings.llm.max_retries,
    max_tokens=settings.embeddings.llm.max_tokens,
    azure_ad_token_provider=settings.azure_ad_token_provider(),
    deployment_name=settings.embeddings.llm.deployment_name,
    organization=settings.embeddings.llm.organization,
    encoding_name=settings.encoding_model,
    request_timeout=settings.embeddings.llm.request_timeout,
)

token_encoder = tiktoken.get_encoding("cl100k_base")

local_search: LocalSearch
global_search: GlobalSearch
question_gen: LocalQuestionGen


@app.on_event("startup")
async def startup_event():
    global local_search
    global global_search
    global question_gen
    local_search = await search.build_local_search_engine(llm, token_encoder=token_encoder)
    global_search = await search.build_global_search_engine(llm, token_encoder=token_encoder)
    question_gen = await search.build_local_question_gen(llm, token_encoder=token_encoder)


@app.get("/")
async def index():
    html_file_path = os.path.join("webserver", "templates", "index.html")
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


async def initialize_search(request: gtypes.ChatCompletionRequest, search: BaseSearch, index: str = None):
    search.context_builder = await switch_context(index=index)
    search.llm_params.update(request.llm_chat_params())
    return search


async def handle_sync_response(request, search, conversation_history, drift_search: bool = False):
    result = await search.asearch(request.messages[-1].content, conversation_history=conversation_history)
    if drift_search:
        response = result.response
        # context_data = _reformat_context_data(result.context_data)  # type: ignore
        response = response["nodes"][0]["answer"]
    else:
        response = result.response

    reference = utils.get_reference(response)
    if reference:
        response += f"\n{utils.generate_ref_links(reference, request.model)}"
    from openai.types.chat.chat_completion import Choice
    completion = ChatCompletion(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=request.model,
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(
                    role="assistant",
                    content=response
                )
            )
        ],
        usage=CompletionUsage(
            completion_tokens=-1,
            prompt_tokens=result.prompt_tokens,
            total_tokens=-1
        )
    )
    return JSONResponse(content=jsonable_encoder(completion))


async def handle_stream_response(request, search, conversation_history):
    async def wrapper_astream_search():
        token_index = 0
        chat_id = f"chatcmpl-{uuid.uuid4().hex}"
        full_response = ""
        async for token in search.astream_search(request.messages[-1].content, conversation_history):  # 调用原始的生成器
            if token_index == 0:
                token_index += 1
                continue

            chunk = ChatCompletionChunk(
                id=chat_id,
                created=int(time.time()),
                model=request.model,
                object="chat.completion.chunk",
                choices=[
                    Choice(
                        index=token_index - 1,
                        finish_reason=None,
                        delta=ChoiceDelta(
                            role="assistant",
                            content=token
                        )
                    )
                ]
            )
            yield f"data: {chunk.json()}\n\n"
            token_index += 1
            full_response += token

        content = ""
        reference = utils.get_reference(full_response)
        if reference:
            content = f"\n{utils.generate_ref_links(reference, request.model)}"
        finish_reason = 'stop'
        chunk = ChatCompletionChunk(
            id=chat_id,
            created=int(time.time()),
            model=request.model,
            object="chat.completion.chunk",
            choices=[
                Choice(
                    index=token_index,
                    finish_reason=finish_reason,
                    delta=ChoiceDelta(
                        role="assistant",
                        # content=result.context_data["entities"].head().to_string()
                        content=content
                    )
                ),
            ],
        )
        yield f"data: {chunk.json()}\n\n"
        yield f"data: [DONE]\n\n"

    return StreamingResponse(wrapper_astream_search(), media_type="text/event-stream")


@app.post("/v1/chat/completions")
async def chat_completions(request: gtypes.ChatCompletionRequest):
    if not local_search or not global_search:
        logger.error("graphrag search engines is not initialized")
        raise HTTPException(status_code=500, detail="graphrag search engines is not initialized")

    try:
        history = request.messages[:-1]
        conversation_history = ConversationHistory.from_list([message.dict() for message in history])

        if request.model == consts.INDEX_GLOBAL:
            search_engine = await initialize_search(request, global_search, request.model)
        elif request.model == consts.INDEX_LOCAL:
            search_engine = await initialize_search(request, local_search, request.model)
        elif request.model == consts.INDEX_DRIFT:
            context_builder = await build_drift_search_context(llm, settings.data, text_embedder)
            drift_search = await search.build_drift_search_engine(llm, context_builder=context_builder, token_encoder=token_encoder)
            search_engine = await initialize_search(request, drift_search, request.model)
            # due to dirt search engine doesn't support streaming search yet.
            return await handle_sync_response(request, search_engine, conversation_history, drift_search=True)
        else:
            raise NotImplementedError(f"model {request.model} is not supported")

        if not request.stream:
            return await handle_sync_response(request, search_engine, conversation_history)
        else:
            return await handle_stream_response(request, search_engine, conversation_history)
    except Exception as e:
        logger.error(msg=f"chat_completions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/advice_questions", response_model=gtypes.QuestionGenResult)
async def get_advice_question(request: gtypes.ChatQuestionGen):
    if request.model == consts.INDEX_LOCAL:
        local_context = await switch_context(index=request.model)
        question_gen.context_builder = local_context
    else:
        raise NotImplementedError(f"model {request.model} is not supported")
    question_history = [message.content for message in request.messages if message.role == "user"]
    candidate_questions = await question_gen.agenerate(
        question_history=question_history, context_data=None, question_count=5
    )
    # the original generated question is "- what about xxx?"
    questions: list[str] = [question.removeprefix("-").strip() for question in candidate_questions.response]
    resp = gtypes.QuestionGenResult(questions=questions,
                                    completion_time=candidate_questions.completion_time,
                                    llm_calls=candidate_questions.llm_calls,
                                    prompt_tokens=candidate_questions.prompt_tokens)
    return resp


@app.get("/v1/models", response_model=gtypes.ModelList)
async def list_models():
    models: list[gtypes.Model] = [
        gtypes.Model(id=consts.INDEX_LOCAL, object="model", created=1644752340, owned_by="graphrag"),
        gtypes.Model(id=consts.INDEX_GLOBAL, object="model", created=1644752340, owned_by="graphrag"),
        gtypes.Model(id=consts.INDEX_DRIFT, object="model", created=1644752340, owned_by="graphrag")]
    return gtypes.ModelList(data=models)


@app.get("/v1/references/{index_id}/{datatype}/{id}", response_class=HTMLResponse)
async def get_reference(index_id: str, datatype: str, id: int):
    if not os.path.exists(settings.data):
        raise HTTPException(status_code=404, detail=f"{index_id} not found")
    if datatype not in ["entities", "claims", "sources", "reports", "relationships"]:
        raise HTTPException(status_code=404, detail=f"{datatype} not found")

    data = await search.get_index_data(settings.data, datatype, id)
    html_file_path = os.path.join("webserver", "templates", f"{datatype}_template.html")
    with open(html_file_path, 'r') as file:
        html_content = file.read()
    template = Template(html_content)
    html_content = template.render(data=data)
    return HTMLResponse(content=html_content)


async def switch_context(index: str):
    if index == consts.INDEX_GLOBAL:
        context_builder = await search.load_global_context(settings.data, token_encoder)
    elif index == consts.INDEX_LOCAL:
        context_builder = await search.load_local_context(settings.data, text_embedder, token_encoder)
    elif index == consts.INDEX_DRIFT:
        context_builder = await build_drift_search_context(llm, settings.data, text_embedder)
    else:
        raise NotImplementedError(f"{index} is not supported")
    return context_builder


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=settings.server_port)
