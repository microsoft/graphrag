---
title: Prompt Tuning ⚙️
navtitle: Overview
layout: page
tags: [post, tuning]
date: 2024-06-13
---

This page provides an overview of the prompt tuning options available for the GraphRAG indexing engine.

## Default Prompts

The default prompts are the simplest way to get started with the GraphRAG system. It is designed to work out-of-the-box with minimal configuration. You can find more detail about these prompts in the following links:

- [Entity/Relationship Extraction](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/graph/prompts.py)
- [Entity/Relationship Description Summarization](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/summarize/prompts.py)
- [Claim Extraction](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/claims/prompts.py)
- [Community Reports](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/community_reports/prompts.py)

## Auto Templating

Auto Templating leverages your input data and LLM interactions to create domain adaptive templates for the generation of the knowledge graph. It is highly encouraged to run it as it will yield better results when executing an Index Run. For more details about how to use it, please refer to the [Auto Templating](/posts/prompt_tuning/auto_prompt_tuning) documentation.

## Manual Configuration

Manual configuration is an advanced use-case. Most users will want to use the Auto Templating feature instead. Details about how to use manual configuration are available in the [Manual Prompt Configuration](/posts/prompt_tuning/manual_prompt_tuning) documentation.
