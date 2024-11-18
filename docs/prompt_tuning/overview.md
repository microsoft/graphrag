# Prompt Tuning ⚙️

This page provides an overview of the prompt tuning options available for the GraphRAG indexing engine.

## Default Prompts

The default prompts are the simplest way to get started with the GraphRAG system. It is designed to work out-of-the-box with minimal configuration. More details about each of the default prompts for indexing and query can be found on the [manual tuning](./manual_prompt_tuning.md) page.

## Auto Tuning

Auto Tuning leverages your input data and LLM interactions to create domain adapted prompts for the generation of the knowledge graph. It is highly encouraged to run it as it will yield better results when executing an Index Run. For more details about how to use it, please refer to the [Auto Tuning](auto_prompt_tuning.md) documentation.

## Manual Tuning

Manual tuning is an advanced use-case. Most users will want to use the Auto Tuning feature instead. Details about how to use manual configuration are available in the [manual tuning](manual_prompt_tuning.md) documentation.
