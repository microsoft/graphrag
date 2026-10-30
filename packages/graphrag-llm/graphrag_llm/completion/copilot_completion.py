# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Text completions through the optional GitHub Copilot SDK."""

import asyncio
import json
import math
import time
from collections.abc import AsyncGenerator, AsyncIterator, Iterator
from contextlib import aclosing, contextmanager, suppress
from typing import TYPE_CHECKING, Any, Unpack
from uuid import uuid4

from openai import pydantic_function_tool

from graphrag_llm.completion.completion import LLMCompletion
from graphrag_llm.config.types import AuthMethod
from graphrag_llm.middleware import with_middleware_pipeline
from graphrag_llm.types import (
    LLMChoice,
    LLMChoiceChunk,
    LLMChoiceDelta,
    LLMCompletionChunk,
    LLMCompletionMessage,
    LLMCompletionResponse,
    LLMCompletionUsage,
)
from graphrag_llm.utils import structure_completion_response

try:
    from copilot import CopilotClient, RuntimeConnection
    from copilot.generated.rpc import PermissionDecisionDeniedInteractivelyByUser
    from copilot.session_events import (
        AssistantMessageData,
        AssistantMessageDeltaData,
        AssistantUsageData,
        SessionEvent,
    )
except ModuleNotFoundError as exc:
    if exc.name != "copilot":
        raise
    msg = (
        "The Copilot provider requires Python 3.11+ and the optional SDK. "
        "Install it with: pip install 'graphrag-llm[copilot]'"
    )
    raise ImportError(msg) from exc

if TYPE_CHECKING:
    from graphrag_cache import Cache, CacheKeyCreator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor, MetricsStore
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.retry import Retry
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        LLMCompletionArgs,
        LLMCompletionMessagesParam,
        Metrics,
        ResponseFormat,
    )


def _deny_permission(*_args: Any) -> PermissionDecisionDeniedInteractivelyByUser:
    return PermissionDecisionDeniedInteractivelyByUser(
        feedback="Tools are disabled for GraphRAG LLM completions."
    )


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list) and all(
        isinstance(part, dict)
        and part.get("type") == "text"
        and isinstance(part.get("text"), str)
        for part in content
    ):
        return "\n".join(part["text"] for part in content)
    msg = "The Copilot provider supports text message content only."
    raise ValueError(msg)


def _messages(messages: "LLMCompletionMessagesParam") -> tuple[str, str]:
    if isinstance(messages, str):
        return "You are a helpful assistant.", messages
    system: list[str] = []
    turns: list[dict[str, str]] = []
    for message in messages:
        role = message.get("role")
        if (
            role not in {"system", "developer", "user", "assistant"}
            or message.get("tool_calls")
            or message.get("function_call")
        ):
            msg = "The Copilot provider supports system, developer, user and assistant text messages, without tool calls."
            raise ValueError(msg)
        content = _text(message.get("content"))
        if role in {"system", "developer"}:
            system.append(content)
        else:
            turns.append({"role": role, "content": content})
    if not turns:
        msg = "At least one user or assistant message is required."
        raise ValueError(msg)
    prompt = turns[0]["content"]
    if len(turns) != 1 or turns[0]["role"] != "user":
        # The SDK accepts a prompt, not an OpenAI messages array.
        prompt = (
            "Continue this conversation. Return only the next assistant message.\n"
            f"Conversation (JSON):\n{json.dumps(turns)}"
        )
    return "\n\n".join(system) or "You are a helpful assistant.", prompt


def _check_sync_context() -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        msg = "Use completion_async inside a running event loop."
        raise RuntimeError(msg)


@contextmanager
def _sync_loop() -> Iterator[asyncio.AbstractEventLoop]:
    _check_sync_context()
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            loop.close()


class CopilotCompletion(LLMCompletion):
    """Copilot text completion with request-scoped clients and tool-free sessions."""

    def __init__(
        self,
        *,
        model_id: str,
        model_config: "ModelConfig",
        tokenizer: "Tokenizer",
        metrics_store: "MetricsStore",
        cache_key_creator: "CacheKeyCreator",
        metrics_processor: "MetricsProcessor | None" = None,
        rate_limiter: "RateLimiter | None" = None,
        retrier: "Retry | None" = None,
        cache: "Cache | None" = None,
        cli_path: str | None = None,
        github_token: str | None = None,
        timeout: float = 600,
        **kwargs: Any,
    ) -> None:
        """Initialize the provider; CLI processes start only on a cache miss."""
        if kwargs:
            msg = f"Unsupported Copilot configuration: {', '.join(sorted(kwargs))}"
            raise ValueError(msg)
        if (
            model_config.api_key
            or model_config.api_base
            or model_config.api_version
            or model_config.azure_deployment_name
            or model_config.auth_method != AuthMethod.ApiKey
        ):
            msg = "Copilot uses CLI authentication or github_token, not API endpoint settings."
            raise ValueError(msg)
        self._model = model_config.model
        self._tokenizer = tokenizer
        self._metrics_store = metrics_store
        self._track_metrics = metrics_processor is not None
        self._call_args = model_config.call_args
        self._cli_path = cli_path
        self._github_token = github_token
        self._timeout = timeout
        self._completion, self._completion_async = with_middleware_pipeline(
            model_config=model_config,
            model_fn=self._base_completion,
            async_model_fn=self._base_completion_async,
            request_type="chat",
            cache=cache,
            cache_key_creator=cache_key_creator,
            tokenizer=tokenizer,
            metrics_processor=metrics_processor,
            rate_limiter=rate_limiter,
            retrier=retrier,
        )

    def _prepare(
        self, kwargs: dict[str, Any]
    ) -> tuple[dict[str, Any], "Metrics | None"]:
        args = {**self._call_args, **kwargs}
        metrics = args.pop("metrics", None)
        metrics = (
            (metrics if metrics is not None else {}) if self._track_metrics else None
        )
        supported = {
            "messages",
            "stream",
            "response_format",
            "response_format_json_object",
            "timeout",
            "reasoning_effort",
            "stream_options",
            "n",
        }
        unsupported = [
            key
            for key, value in args.items()
            if key not in supported and value is not None
        ]
        if unsupported or args.get("n") not in (None, 1):
            msg = f"Unsupported Copilot completion parameters: {', '.join(sorted(unsupported or ['n']))}"
            raise ValueError(msg)
        args = {key: value for key, value in args.items() if key in supported}
        args.pop("n", None)
        if args.get("stream") and args.get("response_format") is not None:
            msg = "response_format is not supported for streaming completions."
            raise ValueError(msg)
        options = args.get("stream_options") or {}
        if options.keys() - {"include_usage"}:
            msg = "Copilot stream_options only supports include_usage."
            raise ValueError(msg)
        timeout = args.get("timeout")
        args["timeout"] = self._timeout if timeout is None else timeout
        if not math.isfinite(args["timeout"]) or args["timeout"] <= 0:
            msg = "Copilot timeout must be a positive, finite number."
            raise ValueError(msg)
        # Validate before cache lookup, retries, or starting a runtime.
        _messages(args["messages"])
        args["model"] = f"copilot/{self._model}"
        return args, metrics

    def completion(
        self, /, **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"]
    ) -> "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]":
        """Complete synchronously, including streaming and structured responses."""
        _check_sync_context()
        args, metrics = self._prepare(dict(kwargs))
        try:
            response = self._completion(metrics=metrics, **args)
            if isinstance(response, LLMCompletionResponse) and args.get(
                "response_format"
            ):
                response.formatted_response = structure_completion_response(
                    response.content, args["response_format"]
                )
            return response
        finally:
            if metrics is not None:
                self._metrics_store.update_metrics(metrics=metrics)

    async def completion_async(
        self, /, **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"]
    ) -> "LLMCompletionResponse[ResponseFormat] | AsyncIterator[LLMCompletionChunk]":
        """Complete asynchronously, including streaming and structured responses."""
        args, metrics = self._prepare(dict(kwargs))
        try:
            response = await self._completion_async(metrics=metrics, **args)
            if isinstance(response, LLMCompletionResponse) and args.get(
                "response_format"
            ):
                response.formatted_response = structure_completion_response(
                    response.content, args["response_format"]
                )
            return response
        finally:
            if metrics is not None:
                self._metrics_store.update_metrics(metrics=metrics)

    def _base_completion(
        self, **kwargs: Any
    ) -> LLMCompletionResponse | Iterator[LLMCompletionChunk]:
        if kwargs.get("stream"):
            return self._sync_stream(kwargs)
        with _sync_loop() as loop:
            return loop.run_until_complete(self._response(kwargs))

    def _sync_stream(self, args: dict[str, Any]) -> Iterator[LLMCompletionChunk]:
        with _sync_loop() as loop:
            stream = self._stream(args)
            try:
                while True:
                    try:
                        chunk = loop.run_until_complete(anext(stream))
                    except StopAsyncIteration:
                        return
                    yield chunk
            finally:
                loop.run_until_complete(stream.aclose())

    async def _base_completion_async(
        self, **kwargs: Any
    ) -> LLMCompletionResponse | AsyncIterator[LLMCompletionChunk]:
        if kwargs.get("stream"):
            return self._stream(kwargs)
        return await self._response(kwargs)

    async def _events(self, args: dict[str, Any]) -> AsyncGenerator[SessionEvent, None]:
        system, prompt = _messages(args["messages"])
        schema = None
        if args.get("response_format") is not None:
            # The SDK forwards schemas without OpenAI's required strict normalization.
            schema = pydantic_function_tool(args["response_format"])["function"].get(
                "parameters"
            )
            if schema is None:
                msg = "Unable to derive a strict JSON schema from response_format."
                raise ValueError(msg)
        elif args.get("response_format_json_object"):
            system += "\n\nReturn a single valid JSON object, without prose or Markdown fences."
        client = CopilotClient(
            connection=RuntimeConnection.for_stdio(path=self._cli_path),
            github_token=self._github_token,
        )
        try:
            await asyncio.wait_for(client.start(), timeout=args["timeout"])
            models = await asyncio.wait_for(
                client.list_models(), timeout=args["timeout"]
            )
            if self._model not in {model.id for model in models}:
                msg = f"Model '{self._model}' is not available through GitHub Copilot."
                raise ValueError(msg)
            session = await asyncio.wait_for(
                client.create_session(
                    model=self._model,
                    system_message={"mode": "replace", "content": system},
                    available_tools=[],
                    on_permission_request=_deny_permission,
                    skip_custom_instructions=True,
                    enable_config_discovery=False,
                    enable_on_demand_instruction_discovery=False,
                    skip_embedding_retrieval=True,
                    enable_file_hooks=False,
                    enable_skills=False,
                    enable_session_store=False,
                    mcp_servers={},
                    custom_agents=[],
                    memory={"enabled": False},
                    infinite_sessions={"enabled": False},
                    streaming=bool(args.get("stream")),
                    reasoning_effort=args.get("reasoning_effort"),
                ),
                timeout=args["timeout"],
            )
            try:
                queue: asyncio.Queue[SessionEvent | None] = asyncio.Queue()
                unsubscribe = session.on(queue.put_nowait)
                task = asyncio.create_task(
                    session.send_and_wait(
                        prompt, response_schema=schema, timeout=args["timeout"]
                    )
                )
                task.add_done_callback(lambda _: queue.put_nowait(None))
                completed = False
                try:
                    while (event := await queue.get()) is not None:
                        if not event.agent_id and isinstance(
                            event.data, (AssistantMessageDeltaData, AssistantUsageData)
                        ):
                            yield event
                    result = await task
                    if (
                        result is None
                        or not isinstance(result.data, AssistantMessageData)
                        or result.data.tool_requests
                        or not result.data.content
                    ):
                        msg = "Copilot returned no final assistant text response."
                        raise RuntimeError(msg)
                    completed = True
                    yield result
                finally:
                    unsubscribe()
                    if not task.done():
                        task.cancel()
                    try:
                        with suppress(asyncio.CancelledError):
                            await task
                    finally:
                        if not completed:
                            await session.abort()
            finally:
                try:
                    await session.disconnect()
                finally:
                    await client.delete_session(session.session_id)
        finally:
            await client.stop()

    async def _response(self, args: dict[str, Any]) -> LLMCompletionResponse:
        usage: list[AssistantUsageData] = []
        content = ""
        model = self._model
        async with aclosing(self._events(args)) as events:
            async for event in events:
                if isinstance(event.data, AssistantUsageData):
                    usage.append(event.data)
                elif isinstance(event.data, AssistantMessageData):
                    content = event.data.content
                    model = event.data.model or model
        response = LLMCompletionResponse(
            id=f"copilot-{uuid4()}",
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[
                LLMChoice(
                    index=0,
                    finish_reason="stop",
                    message=LLMCompletionMessage(role="assistant", content=content),
                )
            ],
            usage=_usage(usage) if usage else None,
        )
        if args.get("response_format") is not None:
            # Validate before caching; restore the concrete model after cache lookup.
            structure_completion_response(content, args["response_format"])
        elif args.get("response_format_json_object") and not isinstance(
            json.loads(content), dict
        ):
            msg = "Copilot did not return a JSON object."
            raise ValueError(msg)
        return response

    async def _stream(
        self, args: dict[str, Any]
    ) -> AsyncGenerator[LLMCompletionChunk, None]:
        id = f"copilot-{uuid4()}"
        created = int(time.time())
        usage: list[AssistantUsageData] = []
        emitted = False

        def chunk(content: str | None = None, *, final: bool = False):
            return LLMCompletionChunk(
                id=id,
                object="chat.completion.chunk",
                created=created,
                model=self._model,
                choices=[
                    LLMChoiceChunk(
                        index=0,
                        delta=LLMChoiceDelta(content=content, role="assistant"),
                        finish_reason="stop" if final else None,
                    )
                ],
                usage=_usage(usage)
                if final
                and usage
                and (args.get("stream_options") or {}).get("include_usage")
                else None,
            )

        events = self._events(args)
        try:
            async for event in events:
                if isinstance(event.data, AssistantMessageDeltaData):
                    emitted = True
                    yield chunk(event.data.delta_content)
                elif isinstance(event.data, AssistantUsageData):
                    usage.append(event.data)
                elif isinstance(event.data, AssistantMessageData) and not emitted:
                    yield chunk(event.data.content)
        finally:
            await events.aclose()
        yield chunk(final=True)

    @property
    def metrics_store(self) -> "MetricsStore":
        """The metrics store."""
        return self._metrics_store

    @property
    def tokenizer(self) -> "Tokenizer":
        """The tokenizer used for local token estimates."""
        return self._tokenizer


def _usage(records: list[AssistantUsageData]) -> LLMCompletionUsage:
    prompt = sum(record.input_tokens or 0 for record in records)
    completion = sum(record.output_tokens or 0 for record in records)
    return LLMCompletionUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
    )
