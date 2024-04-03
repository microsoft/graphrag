---
title: Developing GraphRAG
navtitle: Developing
layout: page
tags: [post]
---

# Requirements

| Name | Installation | Purpose
--- | --- | ---
Python 3.10 or 3.11 | [Download](https://www.python.org/downloads/) | Our library is python-based, so Python is necessary!
Poetry | [Instructions](https://python-poetry.org/docs/#installation) | Poetry is used for package management and virtualenv management in Python codebases

# Getting Started
```sh
# Install Python dependencies.
poetry install

# Execute the Indexing Engine
poetry run poe index --root=<data_project_directory> # default config mode
poetry run poe index --config=<config_file_path> # custom config mode
```

# Azurite
Some unit and smoke tests use Azurite to emulate Azure resources. This can be started by running `./scripts/start-azurite.sh`.


# Lifecycle Scripts
Our Python package utilizes Poetry to manage dependencies and [poethepoet](https://pypi.org/project/poethepoet/) to manage build scripts.

Available scripts are:

* `poetry run poe index` - Run the Indexing CLI
* `poetry run poe query` - Run the Query CLI
* `poetry build` - This invokes `poetry build`, which will build a wheel file and other distributable artifacts.
* `poetry run poe test` - This will execute all tests.
* `poetry run poe test_unit` - This will execute unit tests.
* `poetry run poe test_integration` - This will execute integration tests.
* `poetry run poe test_smoke` - This will execute smoke tests.
* `poetry run poe check` - This will perform a suite of static checks across the package, including:
  * formatting
  * documentation formatting
  * linting
  * security patterns
  * type-checking
* `poetry run poe fix` - This will apply any available auto-fixes to the package. Usually this is just formatting fixes.
* `poetry run poe fix_unsafe` - This will apply any available auto-fixes to the package, including those that may be unsafe.
* `poetry run poe format` - Explicitly run the formatter across the package.
* `poetry run poe build_docs` - Build dynamic docsite content.

## Troubleshooting
### "RuntimeError: llvm-config failed executing, please point LLVM_CONFIG to the path for llvm-config" when running poetry install
Make sure llvm-9 and llvm-9-dev are installed:

`sudo apt-get install llvm-9 llvm-9-dev`

and then in your bashrc, add

`export LLVM_CONFIG=/usr/bin/llvm-config-9`

### "numba/_pymodule.h:6:10: fatal error: Python.h: No such file or directory" when running poetry install

Make sure you have python3.10-dev installed or more generally `python<version>-dev`

`sudo apt-get install python3.10-dev`