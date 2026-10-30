# GraphRAG LLM

> [!WARNING]
> GraphRAG is a research project that explores the functional use of graphs to form a targeted context for question answering. Since our first release in July 2024 the capabilities of frontier models have changed dramatically, and our portfolio of research projects has diversified to match. This project is largely in maintenance mode, and won't be accepting new PRs or implementing new features. We'll perform bug fixes and dependency updates as appropriate, particularly to address CVEs as they arise.

## Basic Completion

This example demonstrates basic usage of the LLM library to interact with Azure OpenAI. It loads environment variables for API configuration, creates a ModelConfig for Azure OpenAI, and sends a simple question to the model. The code handles both streaming and non-streaming responses (streaming responses are printed chunk by chunk in real-time, while non-streaming responses are printed all at once). It also shows how to use the gather_completion_response utility function as a simpler alternative that automatically handles both response types and returns the complete text.

[Open the notebook to explore the basic completion example code](example_notebooks/basic_completion_example.ipynb)

## Basic Embedding

This examples demonstrates how to generate text embeddings using the GraphRAG LLM library with Azure OpenAI's embedding service. It loads API credentials from environment variables, creates a ModelConfig for the Azure embedding model and configures authentication to use either API key or Azure Managed Identity. The script then creates an embedding client and processes a batch of two text strings ("Hello world" and "How are you?") to generate their vector embeddings.

[Open the notebook to explore the basic embeddings example code](example_notebooks/basic_embedding_example.ipynb)

View the [notebooks](notebooks/README.md) for more examples.

## GitHub Copilot completion provider

The built-in `copilot` completion type uses the official
[GitHub Copilot SDK](https://github.com/github/copilot-sdk). It is available
independently of GraphRAG and requires Python 3.11 or later:

```shell
pip install "graphrag-llm[copilot]"
```

Authenticate with the Copilot CLI before using the provider, or supply a GitHub
token through the SDK's environment-based authentication. You need Copilot access
to the requested model. No OpenAI/Azure API endpoint or API key is required.
Other providers do not require the Copilot extra.

```python
from graphrag_llm.completion import create_completion
from graphrag_llm.config import ModelConfig
from graphrag_llm.utils import gather_completion_response

completion = create_completion(
    ModelConfig(
        type="copilot",
        model_provider="copilot",
        model="gpt-6.1-sol",  # Use an exact model ID available to your Copilot account.
        timeout=120,
    )
)

response = completion.completion(messages="What is retrieval-augmented generation?")
print(gather_completion_response(response))

stream = completion.completion(messages="Explain graph-based retrieval.", stream=True)
print(gather_completion_response(stream))
```

Use `await completion.completion_async(...)` in asynchronous code; this returns
an async iterator when `stream=True`. Do not call the synchronous API inside a
running event loop. Fully consume streams, or explicitly call `close()` on a
synchronous stream / `await aclose()` on an asynchronous stream when stopping
early, so the request's resources are released immediately.

Structured responses use the SDK's native per-request schema and the library's
normal Pydantic validation:

```python
from pydantic import BaseModel


class Answer(BaseModel):
    explanation: str


response = completion.completion(
    messages="Explain graph-based retrieval in one sentence.",
    response_format=Answer,
)
print(response.formatted_response)
```

Malformed output raises a parsing/validation error rather than being repaired or
reported as a successful structured completion. As with the LiteLLM provider,
`response_format` cannot be combined with streaming. The
`response_format_json_object=True` call option uses a JSON-only instruction and
validates the returned JSON object for non-streaming requests. Unlike typed
`response_format`, it is not native strict-schema enforcement.

Provider-specific `ModelConfig` fields are `cli_path` (optional compatible CLI
executable), `github_token` (optional explicit token; prefer environment-based
authentication to storing credentials in configuration), and `timeout` (positive
seconds, default 600). `call_args` supports `timeout` and `reasoning_effort` on
models that support it; per-call values override these defaults.

### Capabilities and limitations

- Both APIs support text, streaming, caching, retries, rate limiting, and metrics
  through the existing middleware. SDK-reported token usage is returned when
  available; it is not an estimate of Copilot billing or premium requests.
  Streaming usage is available on the final chunk with
  `stream_options={"include_usage": True}`. As with other providers, streams
  bypass the cache, middleware metrics describe stream creation rather than
  completion, and errors during consumption are not retried automatically.
- Each uncached request starts a client and a fresh session. The provider checks
  model availability, disables tools, repository instruction/config discovery,
  file hooks, skills, memory and cross-session storage, and replaces the system prompt.
  It disconnects and deletes its own session, then stops the client on success,
  failure, cancellation, or explicit stream closure. This avoids persistent
  background runtimes but adds startup overhead, especially for large batches.
- System/developer messages form the session system prompt. A single user
  message is sent verbatim; multiple user/assistant turns are serialized as a
  role-labelled JSON transcript in the prompt. This preserves supplied history
  text but is not native OpenAI role-separated history or resumable SDK sessions.
  No conversation state is shared between calls.
- Image/audio inputs, tool calling, embeddings, multiple choices (`n != 1`),
  sampling parameters (`temperature`, `top_p`, `seed`, etc.) and token-limit
  parameters are unsupported and raise errors rather than being silently
  ignored. Configure a separate embedding provider. Local tokenization uses the
  standard library tokenizer and is only an estimate for Copilot models.
  GraphRAG's DRIFT search currently injects unsupported sampling parameters
  internally and therefore requires another completion provider.
- Copilot model availability, quotas and schema support depend on your
  subscription, selected model and compatible CLI runtime. The optional SDK
  extra does not extend the Copilot provider to Python 3.10. Typed structured
  responses use OpenAI-compatible strict schemas (including required properties
  and closed objects); schemas unsupported by the selected model raise errors.

**SDK runtime compatibility:** validation with SDK 1.0.26 and its default runtime
1.0.103 encountered an upstream event-decoding `AssertionError` for
`session.indexed_search` with `disabledReason=server_limit`, although the
completion succeeded. A compatible installed CLI selected with `cli_path`
completed structured and streaming checks without this callback error. The
provider does not suppress SDK callback errors or patch SDK internals.
