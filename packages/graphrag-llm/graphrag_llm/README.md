# GraphRAG LLM

View the [notebooks](notebooks) for detailed examples.

## Basic Completion

```python
import os
from collections.abc import AsyncIterator, Iterator

from graphrag_llm.completion import LLMCompletion, create_completion
from graphrag_llm.config import ModelConfig
from graphrag_llm.types import LLMCompletionChunk, LLMCompletionResponse
from graphrag_llm.utils import (
    gather_completion_response,
)

api_key = os.getenv("GRAPHRAG_API_KEY")
model_config = ModelConfig(
    model_provider="azure",
    model=os.getenv("GRAPHRAG_MODEL"),
    azure_deployment_name=os.getenv("GRAPHRAG_MODEL"),
    api_base=os.getenv("GRAPHRAG_API_BASE"),
    api_version=os.getenv("GRAPHRAG_API_VERSION"),
    api_key=api_key,
    azure_managed_identity=not api_key,
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
import os
from collections.abc import AsyncIterator, Iterator

from graphrag_llm.embedding import LLMEmbedding, create_embedding
from graphrag_llm.config import ModelConfig
from graphrag_llm.types import LLMEmbeddingResponse
from graphrag_llm.utils import (
    gather_completion_response,
)

api_key = os.getenv("GRAPHRAG_API_KEY")
embedding_config = ModelConfig(
    model_provider="azure",
    model=os.getenv("GRAPHRAG_EMBEDDING_MODEL"),  # type: ignore
    azure_deployment_name=os.getenv("GRAPHRAG_EMBEDDING_MODEL"),
    api_base=os.getenv("GRAPHRAG_API_BASE"),
    api_version=os.getenv("GRAPHRAG_API_VERSION"),
    api_key=api_key,
    azure_managed_identity=not api_key,
)

llm_embedding: LLMEmbedding = create_embedding(embedding_config)

embeddings: LLMEmbeddingResponse = llm_embedding.embedding(
    input=["Hello world", "How are you?"]
)
for data in embeddings.data:
    print(data.embedding[0:3])
```