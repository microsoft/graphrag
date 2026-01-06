# GraphRAG Chunking

This package contains a collection of text chunkers, a core config model, and a factory for acquiring instances.

## Examples

Basic sentence chunking with nltk
```python
chunker = SentenceChunker()
chunks = chunker.chunk("This is a test. Another sentence.")
print(chunks) # ["This is a test.", "Another sentence."]
```

Token chunking
```python
tokenizer = tiktoken.get_encoding("o200k_base")
chunker = TokenChunker(size=3, overlap=0, encode=tokenizer.encode, decode=tokenizer.decode)
chunks = chunker.chunk("This is a random test fragment of some text")
print(chunks) # ["This is a", " random test fragment", " of some text"]
```

Using the factory via helper util
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