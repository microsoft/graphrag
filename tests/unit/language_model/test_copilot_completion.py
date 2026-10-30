# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Copilot provider contract tests using the real SDK's types and signatures."""

import asyncio
import builtins
import importlib
import json
from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import create_autospec
from uuid import uuid4

import pytest
from copilot import CopilotClient
from copilot.session import CopilotSession
from copilot.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    AssistantUsageData,
    SessionEvent,
    SessionEventType,
)
from graphrag_cache.memory_cache import MemoryCache
from graphrag_llm.completion import copilot_completion as provider
from graphrag_llm.completion import create_completion, register_completion
from graphrag_llm.config import ModelConfig
from graphrag_llm.config.retry_config import RetryConfig
from graphrag_llm.types import LLMCompletionResponse
from graphrag_llm.utils import (
    gather_completion_response,
    gather_completion_response_async,
)
from pydantic import BaseModel, ValidationError


def event(data: Any, event_type: str, *, agent_id: str | None = None) -> SessionEvent:
    return SessionEvent(
        data=data,
        type=SessionEventType(event_type),
        id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        agent_id=agent_id,
    )


@pytest.fixture
def sdk(monkeypatch: pytest.MonkeyPatch):
    constructor = create_autospec(CopilotClient)
    client = constructor.return_value
    session = create_autospec(CopilotSession, instance=True)
    session.session_id = "isolated-session"
    client.create_session.return_value = session
    client.list_models.return_value = [type("Model", (), {"id": "test-model"})()]
    state: dict[str, Any] = {
        "content": "Hello world",
        "deltas": ["Hello", " world"],
        "error": None,
        "wait": False,
        "no_response": False,
    }

    def subscribe(callback):
        state["callback"] = callback
        return state.setdefault("unsubscribe", create_autospec(lambda: None))

    session.on.side_effect = subscribe

    async def send(prompt, *, response_schema=None, timeout=60):
        callback = state["callback"]
        callback(
            event(
                AssistantUsageData(
                    model="test-model",
                    input_tokens=999,
                    output_tokens=999,
                ),
                "assistant.usage",
                agent_id="sub-agent",
            )
        )
        for delta in state["deltas"]:
            callback(
                event(
                    AssistantMessageDeltaData(
                        delta_content=delta,
                        message_id="response",
                    ),
                    "assistant.message_delta",
                )
            )
            await asyncio.sleep(0)
        if state["wait"]:
            await asyncio.Event().wait()
        if state["error"]:
            raise state["error"]
        callback(
            event(
                AssistantUsageData(
                    model="test-model",
                    input_tokens=10,
                    output_tokens=3,
                ),
                "assistant.usage",
            )
        )
        if state["no_response"]:
            return None
        return event(
            AssistantMessageData(
                content=state["content"],
                message_id="response",
                model="test-model",
            ),
            "assistant.message",
        )

    session.send_and_wait.side_effect = send
    monkeypatch.setattr(provider, "CopilotClient", constructor)
    return constructor, client, session, state


def model(**kwargs: Any):
    return create_completion(
        ModelConfig(
            type="copilot",
            model_provider="copilot",
            model="test-model",
            **kwargs,
        )
    )


def assert_cleaned(sdk):
    _, client, session, state = sdk
    session.disconnect.assert_awaited_once()
    client.delete_session.assert_awaited_once_with("isolated-session")
    client.stop.assert_awaited_once()
    state["unsubscribe"].assert_called_once()


def test_factory_sync_and_usage(sdk):
    completion = model()
    assert isinstance(completion, provider.CopilotCompletion)
    response = completion.completion(messages="Hi")
    assert isinstance(response, LLMCompletionResponse)
    assert response.content == "Hello world"
    assert response.model == "test-model"
    assert response.usage
    assert response.usage.total_tokens == 13
    assert completion.metrics_store.get_metrics()["total_tokens"] == 13
    assert completion.tokenizer.encode("hello")
    _, client, session, _ = sdk
    config = client.create_session.call_args.kwargs
    assert config["available_tools"] == []
    assert config["skip_custom_instructions"]
    assert not config["enable_config_discovery"]
    assert not config["enable_on_demand_instruction_discovery"]
    assert config["skip_embedding_retrieval"]
    assert config["memory"] == {"enabled": False}
    assert not config["enable_file_hooks"]
    assert not config["enable_skills"]
    assert not config["enable_session_store"]
    assert config["infinite_sessions"] == {"enabled": False}
    assert config["on_permission_request"](None, None).kind != "approved"
    session.send_and_wait.assert_awaited_once_with(
        "Hi",
        response_schema=None,
        timeout=600,
    )
    assert_cleaned(sdk)


async def test_async_completion_and_conversation(sdk):
    messages = [
        {"role": "system", "content": "Be concise"},
        {"role": "developer", "content": [{"type": "text", "text": "No tools"}]},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Continue"},
    ]
    completion = model(call_args={"reasoning_effort": "low", "timeout": 12})
    response = await completion.completion_async(messages=messages, timeout=4)
    assert isinstance(response, LLMCompletionResponse)
    _, client, session, _ = sdk
    assert client.create_session.call_args.kwargs["system_message"] == {
        "mode": "replace",
        "content": "Be concise\n\nNo tools",
    }
    assert client.create_session.call_args.kwargs["reasoning_effort"] == "low"
    prompt = session.send_and_wait.call_args.args[0]
    assert json.loads(prompt.split("Conversation (JSON):\n")[1]) == messages[2:]
    assert session.send_and_wait.call_args.kwargs["timeout"] == 4
    assert_cleaned(sdk)


class Answer(BaseModel):
    answer: int


async def test_nested_schema_uses_strict_objects_and_required_defaults(sdk):
    class NestedAnswer(BaseModel):
        answer: Answer
        explanation: str | None = None

    sdk[3]["content"] = '{"answer":{"answer":42},"explanation":null}'
    response = await model().completion_async(
        messages="Answer", response_format=NestedAnswer
    )
    assert isinstance(response, LLMCompletionResponse)
    assert response.formatted_response == NestedAnswer(answer=Answer(answer=42))
    schema = sdk[2].send_and_wait.call_args.kwargs["response_schema"]
    assert schema["required"] == ["answer", "explanation"]
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["Answer"]["additionalProperties"] is False


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_structured_response(sdk, asynchronous):
    sdk[3]["content"] = '{"answer":42}'
    completion = model()
    if asynchronous:
        response = await completion.completion_async(
            messages="Answer", response_format=Answer
        )
    else:
        response = await asyncio.to_thread(
            completion.completion,
            messages="Answer",
            response_format=Answer,
        )
    assert isinstance(response, LLMCompletionResponse)
    assert response.formatted_response == Answer(answer=42)
    schema = sdk[2].send_and_wait.call_args.kwargs["response_schema"]
    assert schema["properties"]["answer"]["type"] == "integer"
    assert schema["required"] == ["answer"]
    assert schema["additionalProperties"] is False
    assert_cleaned(sdk)


@pytest.mark.parametrize("content", ['{"answer":"not a number"}', "not JSON"])
async def test_invalid_structured_output_is_not_success(sdk, content):
    sdk[3]["content"] = content
    with pytest.raises((ValidationError, json.JSONDecodeError)):
        await model().completion_async(messages="Answer", response_format=Answer)
    assert_cleaned(sdk)


async def test_json_object(sdk):
    sdk[3]["content"] = '{"answer":42}'
    response = await model().completion_async(
        messages="Answer", response_format_json_object=True
    )
    assert isinstance(response, LLMCompletionResponse)
    assert json.loads(response.content) == {"answer": 42}
    assert sdk[2].send_and_wait.call_args.kwargs["response_schema"] is None
    assert (
        "JSON object"
        in sdk[1].create_session.call_args.kwargs["system_message"]["content"]
    )


@pytest.mark.parametrize("content", ["[]", "not JSON"])
async def test_invalid_json_object_is_rejected(sdk, content):
    sdk[3]["content"] = content
    with pytest.raises((json.JSONDecodeError, ValueError), match=r"JSON|Expecting"):
        await model().completion_async(
            messages="Answer", response_format_json_object=True
        )
    assert_cleaned(sdk)


def test_client_options_are_forwarded(sdk):
    model(cli_path="custom-copilot", github_token="test-token").completion(
        messages="Hi"
    )
    assert sdk[0].call_args.kwargs["github_token"] == "test-token"
    assert sdk[0].call_args.kwargs["connection"].path == "custom-copilot"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unsupported_option": True},
        {"api_key": "test-key"},
        {"api_base": "https://example.com"},
        {"azure_deployment_name": "deployment"},
        {"auth_method": "azure_managed_identity"},
    ],
)
def test_invalid_configuration_rejected(sdk, kwargs):
    with pytest.raises(ValueError, match=r"Unsupported|CLI authentication"):
        model(**kwargs)
    sdk[0].assert_not_called()


def test_sync_call_preserves_caller_event_loop(sdk):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        model().completion(messages="Hi")
        assert asyncio.get_event_loop() is loop
        assert not loop.is_closed()
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def test_sync_streaming(sdk):
    stream = model().completion(
        messages="Hi", stream=True, stream_options={"include_usage": True}
    )
    assert isinstance(stream, Iterator)
    chunks = list(stream)
    assert gather_completion_response(iter(chunks)) == "Hello world"
    assert chunks[-1].choices[0].finish_reason == "stop"
    assert chunks[-1].usage
    assert chunks[-1].usage.total_tokens == 13
    assert len({chunk.id for chunk in chunks}) == 1
    assert_cleaned(sdk)


async def test_async_streaming(sdk):
    stream = await model().completion_async(messages="Hi", stream=True)
    assert isinstance(stream, AsyncIterator)
    assert await gather_completion_response_async(stream) == "Hello world"
    assert_cleaned(sdk)


async def test_async_stream_closed_early(sdk):
    sdk[3]["wait"] = True
    stream = await model().completion_async(messages="Hi", stream=True)
    assert isinstance(stream, AsyncGenerator)
    assert (await anext(stream)).choices[0].delta.content == "Hello"
    await stream.aclose()
    sdk[2].abort.assert_awaited_once()
    assert_cleaned(sdk)


def test_sync_stream_closed_early(sdk):
    sdk[3]["wait"] = True
    stream = model().completion(messages="Hi", stream=True)
    assert isinstance(stream, Generator)
    assert next(stream).choices[0].delta.content == "Hello"
    stream.close()
    sdk[2].abort.assert_awaited_once()
    assert_cleaned(sdk)


async def test_cancellation_cleans_up(sdk):
    sdk[3]["wait"] = True
    request = asyncio.create_task(model().completion_async(messages="Hi"))
    while not sdk[2].send_and_wait.called:
        await asyncio.sleep(0)
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request
    sdk[2].abort.assert_awaited_once()
    assert_cleaned(sdk)


@pytest.mark.parametrize("streaming", [False, True])
async def test_errors_propagate(sdk, streaming):
    sdk[3]["error"] = TimeoutError("request timed out")

    async def consume():
        response = await model().completion_async(messages="Hi", stream=streaming)
        if isinstance(response, AsyncIterator):
            async for _ in response:
                pass

    with pytest.raises(TimeoutError, match="request timed out"):
        await consume()
    sdk[2].abort.assert_awaited_once()
    assert_cleaned(sdk)


async def test_no_response_is_error(sdk):
    sdk[3]["no_response"] = True
    with pytest.raises(RuntimeError, match="no final assistant"):
        await model().completion_async(messages="Hi")
    assert_cleaned(sdk)


async def test_unknown_model_does_not_fall_back(sdk):
    sdk[1].list_models.return_value = []
    with pytest.raises(ValueError, match="not available"):
        await model().completion_async(messages="Hi")
    sdk[1].create_session.assert_not_called()
    sdk[1].stop.assert_awaited_once()


@pytest.mark.parametrize("phase", ["start", "create_session"])
async def test_startup_error_stops_client(sdk, phase):
    getattr(sdk[1], phase).side_effect = RuntimeError("failed to start")
    with pytest.raises(RuntimeError, match="failed to start"):
        await model().completion_async(messages="Hi")
    sdk[1].stop.assert_awaited_once()


async def test_disconnect_failure_still_deletes_and_stops(sdk):
    sdk[2].disconnect.side_effect = RuntimeError("disconnect failed")
    with pytest.raises(RuntimeError, match="disconnect failed"):
        await model().completion_async(messages="Hi")
    sdk[1].delete_session.assert_awaited_once()
    sdk[1].stop.assert_awaited_once()


async def test_cache_hit_does_not_start_runtime(sdk):
    completion = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="test-model"),
        cache=MemoryCache(),
    )
    first = await completion.completion_async(messages="Hi")
    second = await completion.completion_async(messages="Hi")
    assert isinstance(first, LLMCompletionResponse)
    assert isinstance(second, LLMCompletionResponse)
    assert first.content == second.content
    sdk[0].assert_called_once()


async def test_cached_structured_response_keeps_pydantic_type(sdk):
    sdk[3]["content"] = '{"answer":42}'
    completion = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="test-model"),
        cache=MemoryCache(),
    )
    await completion.completion_async(messages="Answer", response_format=Answer)
    cached = await completion.completion_async(
        messages="Answer", response_format=Answer
    )
    assert isinstance(cached, LLMCompletionResponse)
    assert cached.formatted_response == Answer(answer=42)
    sdk[0].assert_called_once()


async def test_cache_isolated_by_model(sdk):
    cache = MemoryCache()
    completion = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="test-model"),
        cache=cache,
    )
    await completion.completion_async(messages="Hi")
    other = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="different-model"),
        cache=cache,
    )
    with pytest.raises(ValueError, match="not available"):
        await other.completion_async(messages="Hi")
    assert sdk[0].call_count == 2


async def test_invalid_structured_output_is_not_cached(sdk):
    sdk[3]["content"] = "not JSON"
    completion = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="test-model"),
        cache=MemoryCache(),
    )
    with pytest.raises(json.JSONDecodeError):
        await completion.completion_async(messages="Answer", response_format=Answer)
    sdk[3]["content"] = '{"answer":42}'
    response = await completion.completion_async(
        messages="Answer", response_format=Answer
    )
    assert isinstance(response, LLMCompletionResponse)
    assert response.formatted_response == Answer(answer=42)
    assert sdk[0].call_count == 2


async def test_retry_uses_fresh_client(sdk):
    sdk[1].start.side_effect = [RuntimeError("transient"), None]
    response = await model(
        retry=RetryConfig(type="immediate", max_retries=2)
    ).completion_async(messages="Hi")
    assert isinstance(response, LLMCompletionResponse)
    assert sdk[0].call_count == 2
    assert sdk[1].stop.await_count == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"temperature": 0.1},
        {"tools": []},
        {"n": 2},
        {"stream": True, "response_format": Answer},
        {"timeout": 0},
        {"timeout": float("inf")},
        {"stream_options": {"invalid": True}},
    ],
)
async def test_unsupported_parameters_rejected_before_startup(sdk, kwargs):
    with pytest.raises(
        ValueError, match=r"Unsupported|not supported|timeout|stream_options"
    ):
        await model().completion_async(messages="Hi", **kwargs)
    sdk[0].assert_not_called()


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"role": "system", "content": "Only system"}],
        [{"role": "tool", "content": "tool output", "tool_call_id": "id"}],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image"},
                    }
                ],
            }
        ],
        [{"role": "assistant", "content": "", "tool_calls": [{"id": "tool"}]}],
    ],
)
async def test_unsupported_messages_rejected(sdk, messages):
    with pytest.raises(ValueError, match=r"supports|message is required"):
        await model().completion_async(messages=messages)
    sdk[0].assert_not_called()


async def test_sync_inside_event_loop_is_explicit_error(sdk):
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match="completion_async"):
        model().completion(messages="Hi")
    sdk[0].assert_not_called()


async def test_cached_sync_call_inside_loop_is_explicit_error(sdk):
    completion = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="test-model"),
        cache=MemoryCache(),
    )
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match="completion_async"):
        completion.completion(messages="Hi")
    sdk[0].assert_not_called()


def test_custom_registration_remains_supported(monkeypatch):
    from graphrag_llm.completion.completion_factory import completion_factory

    initializer = create_autospec(provider.CopilotCompletion)
    monkeypatch.setattr(completion_factory, "_service_initializers", {})
    register_completion("copilot", initializer)
    completion = create_completion(
        ModelConfig(type="copilot", model_provider="copilot", model="test-model")
    )
    assert completion is initializer.return_value


def test_missing_optional_dependency_is_actionable(monkeypatch):
    original_import = builtins.__import__

    def missing_copilot(name, *args, **kwargs):
        if name == "copilot":
            msg = "missing copilot"
            raise ModuleNotFoundError(msg, name="copilot")
        return original_import(name, *args, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(builtins, "__import__", missing_copilot)
        with pytest.raises(ImportError, match=r"graphrag-llm\[copilot\]"):
            importlib.reload(provider)
    importlib.reload(provider)
