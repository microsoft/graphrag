# Development Guide

# Requirements

| Name                | Installation                                                 | Purpose                                                                             |
| ------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Python 3.10-3.12    | [Download](https://www.python.org/downloads/)                | The library is Python-based.                                                        |
| uv                  | [Instructions](https://docs.astral.sh/uv/)                   | uv is used for package management and virtualenv management in Python codebases     |

# Getting Started

## Install Dependencies

```sh
# install python dependencies
uv sync
```

## Execute the Indexing Engine

```sh
uv run poe index <...args>
```

## Executing Queries

```sh
uv run poe query <...args>
```

# Azurite

Some unit and smoke tests use Azurite to emulate Azure resources. This can be started by running:

```sh
./scripts/start-azurite.sh
```

or by simply running `azurite` in the terminal if already installed globally. See the [Azurite documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite) for more information about how to install and use Azurite.

# Lifecycle Scripts

Our Python package utilize uv to manage dependencies and [poethepoet](https://pypi.org/project/poethepoet/) to manage build scripts.

Available scripts are:

- `uv run poe index` - Run the Indexing CLI
- `uv run poe query` - Run the Query CLI
- `uv build` - This will build a wheel file and other distributable artifacts.
- `uv run poe test` - This will execute all tests.
- `uv run poe test_unit` - This will execute unit tests.
- `uv run poe test_integration` - This will execute integration tests.
- `uv run poe test_smoke` - This will execute smoke tests.
- `uv run poe test_verbs` - This will execute tests of the basic workflows.
- `uv run poe check` - This will perform a suite of static checks across the package, including:
  - formatting
  - documentation formatting
  - linting
  - security patterns
  - type-checking
- `uv run poe fix` - This will apply any available auto-fixes to the package. Usually this is just formatting fixes.
- `uv run poe fix_unsafe` - This will apply any available auto-fixes to the package, including those that may be unsafe.
- `uv run poe format` - Explicitly run the formatter across the package.

## Troubleshooting

### "RuntimeError: llvm-config failed executing, please point LLVM_CONFIG to the path for llvm-config" when running uv install

Make sure llvm-9 and llvm-9-dev are installed:

`sudo apt-get install llvm-9 llvm-9-dev`

and then in your bashrc, add

`export LLVM_CONFIG=/usr/bin/llvm-config-9`
