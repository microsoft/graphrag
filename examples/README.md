# Indexing Engine Examples
This directory contains several examples of how to use the indexing engine.

Most examples include two different forms of running the pipeline, both are contained in the examples `run.py`
1. Using mostly the Python API
2. Using mostly the a pipeline configuration file

# Running an Example
First run `poetry shell` to activate a virtual environment with the required dependencies.

Then run `PYTHONPATH="$(pwd)" python examples/path_to_example/run.py` from the `python/graphrag` directory.

For example to run the single_verb example, you would run the following commands:

```bash
cd python/graphrag
poetry shell
PYTHONPATH="$(pwd)" python examples/single_verb/run.py
```