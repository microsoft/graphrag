import asyncio
import logging
import os
import time
import uuid
from typing import Generator, Optional

import tiktoken
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.llm.oai import ChatOpenAI, OpenaiApiType, OpenAIEmbedding
from graphrag.query.structured_search.base import SearchResult
from graphrag.query.structured_search.global_search.callbacks import GlobalSearchLLMCallback
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.search import LocalSearch
from webserver.configs import settings
from webserver.globalsearch import build_global_search_engine, build_global_context_builder
from webserver.gtypes import ChatCompletionRequest
from webserver.localsearch import build_local_search_engine, load_local_context
from webserver.utils import get_sorted_subdirs

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    api_key=settings.api_key,
    api_base=settings.api_base,
    model=settings.llm_model,
    api_type=OpenaiApiType.OpenAI,
    max_retries=settings.max_retries,
)

text_embedder = OpenAIEmbedding(
    api_key=settings.api_key,
    api_base=settings.embedding_api_base,
    api_type=OpenaiApiType.OpenAI,
    model=settings.embedding_model,
    max_retries=settings.max_retries,
)

token_encoder = tiktoken.get_encoding("cl100k_base")

local_search: LocalSearch = None
global_search: GlobalSearch = None


class CustomSearchCallback(GlobalSearchLLMCallback):
    stop_sign = '<<STOP>><<停止>>🅿️<<STOP>><<停止>>'

    def __init__(self):
        super().__init__()
        self.token_queue = asyncio.Queue()
        self.usage: Optional[CompletionUsage] = None

    def on_map_response_start(self, map_response_contexts: list[str]):
        super().on_map_response_start(map_response_contexts)
        return map_response_contexts

    def on_map_response_end(self, map_response_outputs: list[SearchResult]):
        super().on_map_response_end(map_response_outputs)
        return map_response_outputs

    def on_llm_new_token(self, token: str):
        """Synchronous method to handle new tokens."""
        super().on_llm_new_token(token)
        asyncio.create_task(self.async_on_llm_new_token(token))  # Schedule async method

    def on_llm_stop(self, usage: CompletionUsage):
        super().on_llm_stop(usage)
        self.usage = usage
        asyncio.create_task(self.async_on_llm_new_token(CustomSearchCallback.stop_sign))  # Schedule async method

    async def async_on_llm_new_token(self, token: str):
        """Asynchronous version to handle new tokens."""
        await self.token_queue.put(token)

    async def generate_tokens(self) -> Generator[str, None, None]:
        while True:
            token = await self.token_queue.get()
            yield token
            if token == CustomSearchCallback.stop_sign:
                break


@app.on_event("startup")
async def startup_event():
    global local_search
    global global_search
    local_search = await build_local_search_engine(llm, token_encoder=token_encoder)
    global_search = await build_global_search_engine(llm, token_encoder=token_encoder)


@app.get("/")
async def index():
    return {"message": "Hello, here is the webserver for graphrag, developed by @kylinmountain"}


async def generate_chunks(callback, request_model):
    async for token in callback.generate_tokens():
        finish_reason = None
        if token == CustomSearchCallback.stop_sign:
            token = ""
            finish_reason = 'stop'
        chunk = ChatCompletionChunk(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request_model,
            object="chat.completion.chunk",
            choices=[
                Choice(
                    index=len(callback.response) - 1,
                    finish_reason=finish_reason,
                    delta=ChoiceDelta(
                        role="assistant",
                        content=token
                    )
                )
            ],
            usage=callback.usage
        )
        yield f"data: {chunk.json()}\n\n"
        if finish_reason:
            yield f"data: [DONE]\n\n"
            break


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not local_search or not global_search:
        logger.error("graphrag search engines is not initialized")
        raise HTTPException(status_code=500, detail="graphrag search engines is not initialized")

    try:
        prompt = request.messages[-1].content
        history = request.messages[:-1]
        message_dicts = [message.dict() for message in history]
        conversation_history = ConversationHistory.from_list(message_dicts)

        if not request.stream:
            if request.model.endswith("global"):
                global_context = await switch_context(model=request.model)
                global_search.context_builder = global_context
                result = await global_search.asearch(prompt, conversation_history=conversation_history)
            else:
                local_context = await switch_context(model=request.model)
                local_search.context_builder = local_context
                result = await local_search.asearch(prompt, conversation_history=conversation_history)

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
                            content=result.response
                        )
                    )
                ],
                usage=CompletionUsage(
                    completion_tokens=-1,
                    prompt_tokens=result.prompt_tokens,
                    total_tokens=-1
                )
            )
            json_compatible = jsonable_encoder(completion)
            return JSONResponse(content=json_compatible)
        else:
            callback = CustomSearchCallback()
            if request.model.endswith("global"):
                global_context = await switch_context(model=request.model)
                global_search.context_builder = global_context
                global_search.callbacks = [callback]
                task = asyncio.create_task(global_search.asearch(prompt, conversation_history))
            else:
                local_context = await switch_context(model=request.model)
                local_search.context_builder = local_context
                local_search.callbacks = [callback]
                task = asyncio.create_task(local_search.asearch(prompt, conversation_history))
            return StreamingResponse(generate_chunks(callback, request.model), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


@app.get("/v1/models")
async def list_models():
    dirs = get_sorted_subdirs(settings.data)
    models = []
    for dir in dirs:
        model_global = {"id": f"{dir}-global", "object": "model", "created": 1644752340, "owned_by": "graphrag"}
        model_local = {"id": f"{dir}-local", "object": "model", "created": 1644752340, "owned_by": "graphrag"}
        models.append(model_global)
        models.append(model_local)

    response = {
        "object": "list",
        "data": models
    }
    return response


async def switch_context(model: str = None):
    if model.endswith("global"):
        input_dir = os.path.join(settings.data, model.removesuffix("-global"), "artifacts")
        context_builder = await build_global_context_builder(input_dir, token_encoder)
    elif model.endswith("local"):
        input_dir = os.path.join(settings.data, model.removesuffix("-local"), "artifacts")
        context_builder = await load_local_context(input_dir, text_embedder, token_encoder)
    else:
        raise NotImplementedError(f"model {model} is not supported")
    return context_builder


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=settings.server_port)
