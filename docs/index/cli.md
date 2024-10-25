# Indexer CLI

The GraphRAG indexer CLI allows for no-code usage of the GraphRAG Indexer.

```bash
graphrag index --verbose --root </workspace/project/root> \
--config <custom_config.yml> --resume <timestamp> \
--reporter <rich|print|none> --emit json,csv,parquet \
--no-cache
```

## CLI Arguments

- `--verbose` - Adds extra logging information during the run.
- `--root <data-project-dir>` - the data root directory. This should contain an `input` directory with the input data, and an `.env` file with environment variables. These are described below.
- `--resume <output-timestamp>` - if specified, the pipeline will attempt to resume a prior run. The parquet files from the prior run will be loaded into the system as inputs, and the workflows that generated those files will be skipped. The input value should be the timestamped output folder, e.g. "20240105-143721".
- `--config <config_file.yml>` - This will opt-out of the Default Configuration mode and execute a custom configuration. If this is used, then none of the environment-variables below will apply.
- `--reporter <reporter>` - This will specify the progress reporter to use. The default is `rich`. Valid values are `rich`, `print`, and `none`.
- `--dry-run` - Runs the indexing pipeline without executing any steps in order to inspect and validate the configuration file.
- `--emit <types>` - This specifies the table output formats the pipeline should emit. The default is `parquet`. Valid values are `parquet`, `csv`, and `json`, comma-separated.
- `--no-cache` - This will disable the caching mechanism. This is useful for debugging and development, but should not be used in production.
- `--output <directory>` - Specify the output directory for pipeline artifacts.
- `--reports <directory>` - Specify the output directory for reporting.
