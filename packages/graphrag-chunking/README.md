# GraphRAG Chunking

This package contains a collection of text chunkers, a core config model, and a factory for acquiring instances.

## Examples

### Basic sentence chunking with nltk

The SentenceChunker class splits text into individual sentences by identifying sentence boundaries. It takes input text and returns a list where each element is a separate sentence, making it easy to process text at the sentence level.

[Open the notebook to explore the basic sentence example code](example_notebooks/basic_sentence_example.ipynb)

### Token chunking

The TokenChunker splits text into fixed-size chunks based on token count rather than sentence boundaries. It uses a tokenizer to encode text into tokens, then creates chunks of a specified size with configurable overlap between chunks.

[Open the notebook to explore the token chunking example code](example_notebooks/token_chunking_example.ipynb)


### Using the factory via helper util

The create_chunker factory function provides a configuration-driven approach to instantiate chunkers by accepting a ChunkingConfig object that specifies the chunking strategy and parameters. This allows for more flexible and maintainable code by separating chunker configuration from direct instantiation.

[Open the notebook to explore the factory helper util example code](example_notebooks/factory_helper_util_example.ipynb)
