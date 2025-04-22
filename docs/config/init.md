# Configuring GraphRAG Indexing

To start using GraphRAG, you must generate a configuration file. The `init` command is the easiest way to get started. It will create a `.env` and `settings.yaml` files in the specified directory with the necessary configuration settings. It will also output the default LLM prompts used by GraphRAG.

## Usage

```sh
graphrag init [--root PATH] [--force, --no-force]
```

## Options

- `--root PATH` - The project root directory to initialize graphrag at. Default is the current directory.
- `--force`, `--no-force` - Optional, default is --no-force. Overwrite existing configuration and prompt files if they exist.

## Example

```sh
graphrag init --root ./ragtest
```

## Output

The `init` command will create the following files in the specified directory:

- `settings.yaml` - The configuration settings file. This file contains the configuration settings for GraphRAG.
- `.env` - The environment variables file. These are referenced in the `settings.yaml` file.
- `prompts/` - The LLM prompts folder. This contains the default prompts used by GraphRAG, you can modify them or run the [Auto Prompt Tuning](../prompt_tuning/auto_prompt_tuning.md) command to generate new prompts adapted to your data.

## Next Steps

After initializing your workspace, you can either run the [Prompt Tuning](../prompt_tuning/auto_prompt_tuning.md) command to adapt the prompts to your data or even start running the [Indexing Pipeline](../index/overview.md) to index your data. For more information on configuration options available, see the [YAML details page](yaml.md).
