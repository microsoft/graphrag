# GraphRAG
GraphRAG Indexing is a sub-package that includes a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using the power of LLMs.

GraphRAG indexing pipelines are configurable. They are composed of workflows, standard and custom steps, LM templates, and input/output adapters. Our standard pipeline is designed to:

* extract entities, relationships and claims from raw text
* perform entity resolution
* perform community detection in entities
* generate community summaries and reports at multiple levels of granularity
* embed entities into a graph vector space
* embed text chunks into a textual vector space

The outputs of the pipeline can be stored in a variety of formats, including JSON and Parquet - or they can be handled manually via the Python API.


## Getting Started
### Requirements
See the [Requirements](../../DEVELOPING.md#requirements) section in [DEVELOPING.md](../../DEVELOPING.md) for details on setting up a development environment.

The first step in using the Indexing Engine is to create a config file for your pipeline.  See [Configuring a Pipeline](#configuring-a-pipeline) for more details.
After you have a config file you can run the pipeline using the CLI (see [CLI](#cli)) or the Python API (WIP).

## Usage
### CLI

* Via Poetry
```sh
# Via Poetry
pip install graphrag

# Via Node
python -m graphrag.index --config your_pipeline.yml
```

### Python API
```python
from graphrag.index import run_pipeline, PipelineWorkflowReference

workflows: list[PipelineWorkflowReference] = [
    PipelineWorkflowReference(
        steps=[
            {
                # built-in verb
                "verb": "derive",  # https://github.com/microsoft/datashaper/blob/main/python/datashaper/datashaper/engine/verbs/derive.py
                "args": {
                    "column1": "col1",  # from above
                    "column2": "col2",  # from above
                    "to": "col_multiplied",  # new column name
                    "operator": "*",  # multiply the two columns
                },
                # Since we're trying to act on the default input, we don't need explicitly to specify an input
            }
        ]
    ),
]

dataset = pd.DataFrame([{"col1": 2, "col2": 4}, {"col1": 5, "col2": 10}])
outputs = []
async for output in await run_pipeline(dataset=dataset, workflows=workflows):
    outputs.append(output
pipeline_result = outputs[-1]
print(pipeline_result)
```

## Further Reading
* To start developing within *GraphRAG* project, see [../../DEVELOPING.md](../../DEVELOPING.md)
* To understand the underlying concepts and execution model of the indexing library, see [./ARCHITECTURE.md](./ARCHITECTURE.md)
* To get running with a series of examples, see [./examples/README.md](./examples/README.md)
* To read more about configuring the indexing engine, see [./docs/README.md](./docs/README.md)

<!-- todo: show execution -->
<!-- todo: show configuration -->
<!-- todo: show inputs -->