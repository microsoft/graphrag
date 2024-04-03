# Indexing Engine Docs
Indexing Engine is a highly flexible, configuration based tool for running data pipelines.

## The Default Mode
To run the default pipeline, which will generate the GraphRAG knowledge model, you can invoke the indexer on a data project with:

```sh
yarn run:index --root=<target_path>
```
or
```sh
poetry run poe cli --root=<target_path>
```
or
```sh
poetry run python -m graphrag.index --root=<target_path>
```

(all of these commands do the same thing)

A more complete set of options and input invariants can be found in [default_configuration.md](./default_configuration.md)

## YAML-Configured Pipelines
Pipelines are generally defined using a YAML configuration file. The configuration file is composed of a few key things:
- The input data: Typically a set of loose text files or csv files. See [input](./input/README.md) for more details.
- A set of workflows: Which are a set of linear transformations (steps/verbs) of a set of data to produce an output. See [workflows](./workflows/README.md) for more details.
- An optional configuration for logging.
- An optional configuration for caching intermediate results.
- An optional configuration for storing the output of the pipeline, which includes the workflow output, as well as statistics about the pipeline run.

## Examples
See [examples](../examples) for examples of how to use Indexing Engine.
See [verbs/README.md](./verbs/README.md) for details on the verbs that are available in Indexing Engine.
See [workflows.md](./workflows.md) for details on the available default workflows in the Indexing Engine.
See [llm_config.md](./llm_config.md) for details on how to configure llm-based verbs.

<!-- TODO: add documentation about built-in workflows. -->