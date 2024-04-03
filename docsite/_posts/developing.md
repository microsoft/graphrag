---
title: Developing GraphRAG
navtitle: Developing
layout: page
tags: [post]
---

## Requirements

| Name | Installation | Purpose
--- | --- | ---
Python 3.10 or 3.11 | [Download](https://www.python.org/downloads/) | The library is Python-based.
Poetry | [Instructions](https://python-poetry.org/docs/#installation) | Poetry is used for package management and virtualenv management in Python codebases
Node Latest LTS | [Download](https://nodejs.org/en/download/) | Monorepo Orchestration
yarn 1.x | `npm i -g yarn` | Node Dependency Management

## Install Dependencies
```sh
# Install top-level build & orchestration tools.
yarn
```

```sh
# Install Python dependencies.
yarn python_install 
```

```sh
# Execute the Indexing Engine in default config mode
yarn run:index --root=<data_project_directory>
```

or

```sh
# Execute the Indexing Engine in custom config mode
yarn run:index --config=<config_file_path>
```

## Monorepo Orchestration

### Lifecycle Scripts
Our Python packages utilize Poetry to manage their dependencies and [poethepoet](https://pypi.org/project/poethepoet/) internally to manage their build scripts. Because we need top-level monorepo orchestration, some scripts defined in `poethepoet` are executed via [npm scripts](https://docs.npmjs.com/cli/v6/using-npm/scripts) to define our project's lifecycle tasks. These lifecycle tasks include:

* `python_install` - This invokes `poetry install`.
* `build` - This invokes `poetry build`, which will build a wheel file and other distributable artifacts.
* `test` - This will execute any unit and integration tests.
* `check` - This will perform a suite of static checks across the package, including:
  * formatting
  * documentation formatting
  * linting
  * security patterns
  * type-checking
* `fix` - This will apply any available auto-fixes to the package. Usually this is just formatting fixes.
* `format` - Explicitly run the formatter across the package.

### Using Lifecycle Scripts
Lifecycle scripts can be invoked via `yarn <script-name>`. For example, to run the `build` script for every package, you would run `yarn build`. If you need to work within the scope of a single package, you can execute `yarn build` within that package directory, or you can use `poethepoet` directly (e.g. `poetry run poe <script-name>`)

### Caching
The Yarn monorepo uses [Turbo](https://turbo.build/) to orchestrate tasks across packages. Turbo optimizes for task parallelization and caching. When you run a task, Turbo will cache the results of that task. If you run the task again, Turbo will check the cache and if the inputs to the task have not changed, it will use the cached result. This is useful for CI, where we can cache the results of a task and then use those results in subsequent builds. 

However, this can result in subtle errors if the caching artifacts are not well defined in [turbo.json](./turbo.json). If you are running into errors that seem to be related to caching, you can use the `--force` flag to skip cache reads during task execution. For example, `yarn build --force` will force a rebuild of all packages.

### CI Lifecycle Tasks
During CI, our Azure Pipeline will execute the `ci` task across the packages. (See [turbo.json](./turbo.json)). This will execute `build`, `check`, and `test` per-package.


### Troubleshooting
#### "RuntimeError: llvm-config failed executing, please point LLVM_CONFIG to the path for llvm-config" when running poetry install
Make sure llvm-9 and llvm-9-dev are installed:

`sudo apt-get install llvm-9 llvm-9-dev`

and then in your bashrc, add

`export LLVM_CONFIG=/usr/bin/llvm-config-9`

#### "numba/_pymodule.h:6:10: fatal error: Python.h: No such file or directory" when running poetry install

Make sure you have python3.10-dev installed or more generally `python<version>-dev`

`sudo apt-get install python3.10-dev`