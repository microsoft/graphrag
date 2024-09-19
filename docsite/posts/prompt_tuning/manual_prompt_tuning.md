---
title: Prompt Tuning⚙️
navtitle: Manual Tuning
layout: page
tags: [post, tuning]
date: 2023-01-03
---

The GraphRAG indexer, by default, will run with a handful of prompts that are designed to work well in the broad context of knowledge discovery.
However, it is quite common to want to tune the prompts to better suit your specific use case.
We provide a means for you to do this by allowing you to specify a custom prompt file, which will each use a series of token-replacements internally.

Each of these prompts may be overridden by writing a custom prompt file in plaintext. We use token-replacements in the form of `{token_name}`, and the descriptions for the available tokens can be found below.

## Entity/Relationship Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/graph/prompts.py)

### Tokens (values provided by extractor)

- **{input_text}** - The input text to be processed.
- **{entity_types}** - A list of entity types
- **{tuple_delimiter}** - A delimiter for separating values within a tuple. A single tuple is used to represent an individual entity or relationship.
- **{record_delimiter}** - A delimiter for separating tuple instances.
- **{completion_delimiter}** - An indicator for when generation is complete.

## Summarize Entity/Relationship Descriptions

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/summarize/prompts.py)

### Tokens (values provided by extractor)

- **{entity_name}** - The name of the entity or the source/target pair of the relationship.
- **{description_list}** - A list of descriptions for the entity or relationship.

## Claim Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/claims/prompts.py)

### Tokens (values provided by extractor)

- **{input_text}** - The input text to be processed.
- **{tuple_delimiter}** - A delimiter for separating values within a tuple. A single tuple is used to represent an individual entity or relationship.
- **{record_delimiter}** - A delimiter for separating tuple instances.
- **{completion_delimiter}** - An indicator for when generation is complete.

Note: there is additional parameter for the `Claim Description` that is used in claim extraction.
The default value is

`"Any claims or facts that could be relevant to information discovery."`

See the [configuration documentation](/posts/config/overview/) for details on how to change this.

## Generate Community Reports

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/community_reports/prompts.py)

### Tokens (values provided by extractor)

- **{input_text}** - The input text to generate the report with. This will contain tables of entities and relationships.
