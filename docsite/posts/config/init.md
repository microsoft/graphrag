---
title: Configuring GraphRAG Indexing
navtitle: Init Command
tags: [post]
layout: page
date: 2023-01-03
---

To start using GraphRAG, you need to configure the system. The `init` command is the easiest way to get started. It will create a `.env` and `settings.yaml` files in the specified directory with the necessary configuration settings. It will also output the default LLM prompts used by GraphRAG.

## Usage

```sh
python -m graphrag.index [--init] [--root PATH]
```

## Options

- `--init` - Initialize the directory with the necessary configuration files.
- `--root PATH` - The root directory to initialize. Default is the current directory.

## Example

```sh
python -m graphrag.index --init --root ./ragtest
```

## Output

The `init` command will create the following files in the specified directory:

- `settings.yaml` - The configuration settings file. This file contains the configuration settings for GraphRAG.
- `.env` - The environment variables file. These are referenced in the `settings.yaml` file.
- `prompts/` - The LLM prompts folder. This contains the default prompts used by GraphRAG, you can modify them or run the [Auto Prompt Tuning](/posts/prompt_tuning/auto_prompt_tuning) command to generate new prompts adapted to your data.

## Next Steps

After initializing your workspace, you can either run the [Prompt Tuning](/posts/prompt_tuning/auto_prompt_tuning) command to adapt the prompts to your data or even start running the [Indexing Pipeline](/posts/index/overview) to index your data. For more information on configuring GraphRAG, see the [Configuration](/posts/config/overview) documentation.
