---
title: chunk
navtitle: chunk
layout: page
tags: [post, verb]
---
Chunk a piece of text into smaller pieces.

## Usage
```yaml
verb: text_chunk
args:
    column: <column name> # The name of the column containing the text to chunk, this can either be a column with text, or a column with a list[tuple[doc_id, str]]
    to: <column name> # The name of the column to output the chunks to
    strategy: <strategy config> # The strategy to use to chunk the text, see below for more details
```

## Strategies
The text chunk verb uses a strategy to chunk the text. The strategy is an object which defines the strategy to use. The following strategies are available:

### langchain
This strategy uses the [langchain] library to chunk a piece of text. The strategy config is as follows:

> Note: In the future, this will likely be renamed to something more generic, like "openai_tokens".

```yaml
strategy:
    type: langchain
    chunk_size: 1000 # Optional, The chunk size to use, default: 1000
    chunk_overlap: 300 # Optional, The chunk overlap to use, default: 300
```

### sentence
This strategy uses the nltk library to chunk a piece of text into sentences. The strategy config is as follows:

```yaml
strategy:
    type: sentence
```

## Code
[text_chunk.py](https://dev.azure.com/msresearch/Resilience/_git/ire-indexing?path=/python/graphrag/graphrag/indexing/verbs/text/chunk/text_chunk.py)