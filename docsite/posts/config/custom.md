---
title: Custom Configuration Mode
navtitle: Fully Custom Config
layout: page
tags: [post]
date: 2023-01-04
---

The primary configuration sections for Indexing Engine pipelines are described below. Each configuration section can be expressed in Python (for use in Python API mode) as well as YAML, but YAML is show here for brevity.

Using custom configuration is an advanced use-case. Most users will want to use the [Default Configuration](/posts/config/overview) instead.

## Indexing Engine Examples

The [examples](https://github.com/microsoft/graphrag/blob/main/examples/) directory contains several examples of how to use the indexing engine with _custom configuration_.

Most examples include two different forms of running the pipeline, both are contained in the examples `run.py`

1. Using mostly the Python API
2. Using mostly the a pipeline configuration file

To run an example:

- Run `poetry shell` to activate a virtual environment with the required dependencies.
- Run `PYTHONPATH="$(pwd)" python examples/path_to_example/run.py` from the `root` directory.

For example to run the single_verb example, you would run the following commands:

```bash
poetry shell
```

```sh
PYTHONPATH="$(pwd)" python examples/single_verb/run.py
```

# Configuration Sections

# > extends

This configuration allows you to extend a base configuration file or files.

```yaml
# single base
extends: ../base_config.yml
```

```yaml
# multiple bases
extends:
  - ../base_config.yml
  - ../base_config2.yml
```

# > root_dir

This configuration allows you to set the root directory for the pipeline. All data inputs and outputs are assumed to be relative to this path.

```yaml
root_dir: /workspace/data_project
```

# > storage

This configuration allows you define the output strategy for the pipeline.

- `type`: The type of storage to use. Options are `file`, `memory`, and `blob`
- `base_dir` (`type: file` only): The base directory to store the data in. This is relative to the config root.
- `connection_string` (`type: blob` only): The connection string to use for blob storage.
- `container_name` (`type: blob` only): The container to use for blob storage.

# > cache

This configuration allows you define the cache strategy for the pipeline.

- `type`: The type of cache to use. Options are `file` and `memory`, and `blob`.
- `base_dir` (`type: file` only): The base directory to store the cache in. This is relative to the config root.
- `connection_string` (`type: blob` only): The connection string to use for blob storage.
- `container_name` (`type: blob` only): The container to use for blob storage.

# > reporting

This configuration allows you define the reporting strategy for the pipeline. Report files are generated artifacts that summarize the performance metrics of the pipeline and emit any error messages.

- `type`: The type of reporting to use. Options are `file`, `memory`, and `blob`
- `base_dir` (`type: file` only): The base directory to store the reports in. This is relative to the config root.
- `connection_string` (`type: blob` only): The connection string to use for blob storage.
- `container_name` (`type: blob` only): The container to use for blob storage.

# > workflows

This configuration section defines the workflow DAG for the pipeline. Here we define an array of workflows and express their inter-dependencies in steps:

- `name`: The name of the workflow. This is used to reference the workflow in other parts of the config.
- `steps`: The DataShaper steps that this workflow comprises. If a step defines an input in the form of `workflow:<workflow_name>`, then it is assumed to have a dependency on the output of that workflow.

```yaml
workflows:
  - name: workflow1
    steps:
      - verb: derive
        args:
          column1: "col1"
          column2: "col2"
  - name: workflow2
    steps:
      - verb: derive
        args:
          column1: "col1"
          column2: "col2"
        input:
          # dependency established here
          source: workflow:workflow1
```

# > input

- `type`: The type of input to use. Options are `file` or `blob`.
- `file_type`: The file type field discriminates between the different input types. Options are `csv` and `text`.
- `base_dir`: The base directory to read the input files from. This is relative to the config file.
- `file_pattern`: A regex to match the input files. The regex must have named groups for each of the fields in the file_filter.
- `post_process`: A DataShaper workflow definition to apply to the input before executing the primary workflow.
- `source_column` (`type: csv` only): The column containing the source/author of the data
- `text_column` (`type: csv` only): The column containing the text of the data
- `timestamp_column` (`type: csv` only): The column containing the timestamp of the data
- `timestamp_format` (`type: csv` only): The format of the timestamp

```yaml
input:
  type: file
  file_type: csv
  base_dir: ../data/csv # the directory containing the CSV files, this is relative to the config file
  file_pattern: '.*[\/](?P<source>[^\/]+)[\/](?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<author>[^_]+)_\d+\.csv$' # a regex to match the CSV files
  # An additional file filter which uses the named groups from the file_pattern to further filter the files
  # file_filter:
  #   # source: (source_filter)
  #   year: (2023)
  #   month: (06)
  #   # day: (22)
  source_column: "author" # the column containing the source/author of the data
  text_column: "message" # the column containing the text of the data
  timestamp_column: "date(yyyyMMddHHmmss)" # optional, the column containing the timestamp of the data
  timestamp_format: "%Y%m%d%H%M%S" # optional,  the format of the timestamp
  post_process: # Optional, set of steps to process the data before going into the workflow
    - verb: filter
      args:
        column: "title",
        value: "My document"
```

```yaml
input:
  type: file
  file_type: csv
  base_dir: ../data/csv # the directory containing the CSV files, this is relative to the config file
  file_pattern: '.*[\/](?P<source>[^\/]+)[\/](?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<author>[^_]+)_\d+\.csv$' # a regex to match the CSV files
  # An additional file filter which uses the named groups from the file_pattern to further filter the files
  # file_filter:
  #   # source: (source_filter)
  #   year: (2023)
  #   month: (06)
  #   # day: (22)
  post_process: # Optional, set of steps to process the data before going into the workflow
    - verb: filter
      args:
        column: "title",
        value: "My document"
```
