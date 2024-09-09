---
title: Query CLI
navtitle: CLI
layout: page
tags: [post, orchestration]
date: 2024-27-03
---

The GraphRAG query CLI allows for no-code usage of the GraphRAG Query engine.

```bash
python -m graphrag.query --config <config_file.yml> --data <path-to-data> --community_level <comunit-level> --response_type <response-type> --method <"local"|"global"> <query>
```

## CLI Arguments

- `--config <config_file.yml>` - The configuration yaml file to use when running the query. If this is used, then none of the environment-variables below will apply.
- `--data <path-to-data>` - Folder containing the `.parquet` output files from running the Indexer.
- `--community_level <community-level>` - Community level in the Leiden community hierarchy from which we will load the community reports higher value means we use reports on smaller communities. Default: 2
- `--response_type <response-type>` - Free form text describing the response type and format, can be anything, e.g. `Multiple Paragraphs`, `Single Paragraph`, `Single Sentence`, `List of 3-7 Points`, `Single Page`, `Multi-Page Report`. Default: `Multiple Paragraphs`.
- `--method <"local"|"global">` - Method to use to answer the query, one of local or global. For more information check [Overview](overview.md)
- `--streaming` - Stream back the LLM response

## Env Variables

Required environment variables to execute:
- `GRAPHRAG_API_KEY` - API Key for executing the model, will fallback to `OPENAI_API_KEY` if one is not provided.
- `GRAPHRAG_LLM_MODEL` - Model to use for Chat Completions.
- `GRAPHRAG_EMBEDDING_MODEL` - Model to use for Embeddings.

You can further customize the execution by providing these environment variables:

- `GRAPHRAG_LLM_API_BASE` - The API Base URL. Default: `None`
- `GRAPHRAG_LLM_TYPE` - The LLM operation type. Either `openai_chat` or `azure_openai_chat`. Default: `openai_chat`
- `GRAPHRAG_LLM_MAX_RETRIES` - The maximum number of retries to attempt when a request fails. Default: `20`
- `GRAPHRAG_EMBEDDING_API_BASE` - The API Base URL. Default: `None`
- `GRAPHRAG_EMBEDDING_TYPE` - The embedding client to use. Either `openai_embedding` or `azure_openai_embedding`. Default: `openai_embedding`
- `GRAPHRAG_EMBEDDING_MAX_RETRIES` - The maximum number of retries to attempt when a request fails. Default: `20`
- `GRAPHRAG_LOCAL_SEARCH_TEXT_UNIT_PROP` - Proportion of context window dedicated to related text units. Default: `0.5`
- `GRAPHRAG_LOCAL_SEARCH_COMMUNITY_PROP` - Proportion of context window dedicated to community reports. Default: `0.1`
- `GRAPHRAG_LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS` - Maximum number of turns to include in the conversation history. Default: `5`
- `GRAPHRAG_LOCAL_SEARCH_TOP_K_ENTITIES` - Number of related entities to retrieve from the entity description embedding store. Default: `10`
- `GRAPHRAG_LOCAL_SEARCH_TOP_K_RELATIONSHIPS` - Control the number of out-of-network relationships to pull into the context window. Default: `10`
- `GRAPHRAG_LOCAL_SEARCH_MAX_TOKENS` - Change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000). Default: `12000`
- `GRAPHRAG_LOCAL_SEARCH_LLM_MAX_TOKENS` - Change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500). Default: `2000`
- `GRAPHRAG_GLOBAL_SEARCH_MAX_TOKENS` - Change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000). Default: `12000`
- `GRAPHRAG_GLOBAL_SEARCH_DATA_MAX_TOKENS` - Change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000). Default: `12000`
- `GRAPHRAG_GLOBAL_SEARCH_MAP_MAX_TOKENS` - Default: `500`
- `GRAPHRAG_GLOBAL_SEARCH_REDUCE_MAX_TOKENS` - Change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000-1500). Default: `2000`
- `GRAPHRAG_GLOBAL_SEARCH_CONCURRENCY` - Default: `32`