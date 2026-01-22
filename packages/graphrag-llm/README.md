# GraphRAG LLM

## Basic Completion

```python
import os
from collections.abc import AsyncIterator, Iterator

from dotenv import load_dotenv
from graphrag_llm.completion import LLMCompletion, create_completion
from graphrag_llm.config import AuthMethod, ModelConfig
from graphrag_llm.types import LLMCompletionChunk, LLMCompletionResponse
from graphrag_llm.utils import (
    gather_completion_response,
    gather_completion_response_async,
)

load_dotenv()

api_key = os.getenv("GRAPHRAG_API_KEY")
model_config = ModelConfig(
    model_provider="azure",
    model=os.getenv("GRAPHRAG_MODEL", "gpt-4o"),
    azure_deployment_name=os.getenv("GRAPHRAG_MODEL", "gpt-4o"),
    api_base=os.getenv("GRAPHRAG_API_BASE"),
    api_version=os.getenv("GRAPHRAG_API_VERSION", "2025-04-01-preview"),
    api_key=api_key,
    auth_method=AuthMethod.AzureManagedIdentity if not api_key else AuthMethod.ApiKey,
)
llm_completion: LLMCompletion = create_completion(model_config)

response: LLMCompletionResponse | Iterator[LLMCompletionChunk] = (
    llm_completion.completion(
        messages="What is the capital of France?",
    )
)

if isinstance(response, Iterator):
    # Streaming response
    for chunk in response:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
else:
    # Non-streaming response
    print(response.choices[0].message.content)

# Alternatively, you can use the utility function to gather the full response
# The following is equivalent to the above logic. If all you care about is
# the first choice response then you can use the gather_completion_response
# utility function.
response_text = gather_completion_response(response)
print(response_text)
```

## Basic Embedding

```python
from graphrag_llm.embedding import LLMEmbedding, create_embedding
from graphrag_llm.types import LLMEmbeddingResponse
from graphrag_llm.utils import gather_embeddings

embedding_config = ModelConfig(
    model_provider="azure",
    model=os.getenv("GRAPHRAG_EMBEDDING_MODEL", "text-embedding-3-small"),
    azure_deployment_name=os.getenv(
        "GRAPHRAG_LLM_EMBEDDING_MODEL", "text-embedding-3-small"
    ),
    api_base=os.getenv("GRAPHRAG_API_BASE"),
    api_version=os.getenv("GRAPHRAG_API_VERSION", "2025-04-01-preview"),
    api_key=api_key,
    auth_method=AuthMethod.AzureManagedIdentity if not api_key else AuthMethod.ApiKey,
)

llm_embedding: LLMEmbedding = create_embedding(embedding_config)

embeddings_batch: LLMEmbeddingResponse = llm_embedding.embedding(
    input=["Hello world", "How are you?"]
)
for data in embeddings_batch.data:
    print(data.embedding[0:3])

# OR
batch = gather_embeddings(embeddings_batch)
for embedding in batch:
    print(embedding[0:3])
```

View the [notebooks](notebooks/README.md) for more examples.