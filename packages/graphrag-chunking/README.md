# GraphRAG Chunking

This package contains a collection of text chunkers, a core config model, and a factory for acquiring instances.

## Examples

### Basic sentence chunking with nltk

The SentenceChunker class splits text into individual sentences by identifying sentence boundaries. It takes input text and returns a list where each element is a separate sentence, making it easy to process text at the sentence level.

```python
chunker = SentenceChunker()
chunks = chunker.chunk("This is a test. Another sentence.")
print(chunks) # ["This is a test.", "Another sentence."]
```

### Token chunking

The TokenChunker splits text into fixed-size chunks based on token count rather than sentence boundaries. It uses a tokenizer to encode text into tokens, then creates chunks of a specified size with configurable overlap between chunks.

```python
tokenizer = tiktoken.get_encoding("o200k_base")
chunker = TokenChunker(size=3, overlap=0, encode=tokenizer.encode, decode=tokenizer.decode)
chunks = chunker.chunk("This is a random test fragment of some text")
print(chunks) # ["This is a", " random test fragment", " of some text"]
```

### Using the factory via helper util

The create_chunker factory function provides a configuration-driven approach to instantiate chunkers by accepting a ChunkingConfig object that specifies the chunking strategy and parameters. This allows for more flexible and maintainable code by separating chunker configuration from direct instantiation.

```python
tokenizer = tiktoken.get_encoding("o200k_base")
config = ChunkingConfig(
    strategy="tokens",
    size=3,
    overlap=0
)
chunker = create_chunker(config, tokenizer.encode, tokenizer.decode)
...
```