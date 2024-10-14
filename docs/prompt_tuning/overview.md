# Prompt Tuning ⚙️

This page provides an overview of the prompt tuning options available for the GraphRAG indexing engine.

## Default Prompts

The default prompts are the simplest way to get started with the GraphRAG system. It is designed to work out-of-the-box with minimal configuration. You can find more detail about these prompts in the following links:

- [Entity/Relationship Extraction](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/graph/prompts.py)
- [Entity/Relationship Description Summarization](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/summarize/prompts.py)
- [Claim Extraction](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/claims/prompts.py)
- [Community Reports](http://github.com/microsoft/graphrag/blob/main/graphrag/index/graph/extractors/community_reports/prompts.py)

## Auto Tuning

Auto Tuning leverages your input data and LLM interactions to create domain adapted prompts for the generation of the knowledge graph. It is highly encouraged to run it as it will yield better results when executing an Index Run. For more details about how to use it, please refer to the [Auto Tuning](auto_prompt_tuning.md) documentation.

## Manual Tuning

Manual tuning is an advanced use-case. Most users will want to use the Auto Tuning feature instead. Details about how to use manual configuration are available in the [Manual Tuning](manual_prompt_tuning.md) documentation.
