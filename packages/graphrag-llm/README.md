# GraphRAG LLM

## Basic Completion

This example demonstrates basic usage of the LLM library to interact with Azure OpenAI. It loads environment variables for API configuration, creates a ModelConfig for Azure OpenAI, and sends a simple question to the model. The code handles both streaming and non-streaming responses (streaming responses are printed chunk by chunk in real-time, while non-streaming responses are printed all at once). It also shows how to use the gather_completion_response utility function as a simpler alternative that automatically handles both response types and returns the complete text.

[Open the notebook to explore the basic completion example code](example_notebooks/basic_completion_example.ipynb)


## Basic Embedding

This examples demonstrates how to generate text embeddings using the GraphRAG LLM library with Azure OpenAI's embedding service. It loads API credentials from environment variables, creates a ModelConfig for the Azure embedding model and configures authentication to use either API key or Azure Managed Identity. The script then creates an embedding client and processes a batch of two text strings ("Hello world" and "How are you?") to generate their vector embeddings.

[Open the notebook to explore the basic embeddings example code](example_notebooks/basic_completion_example.ipynb)

View the [notebooks](example_notebooks/README.md) for more examples.