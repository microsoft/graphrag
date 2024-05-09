# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from graphrag.index.workflows import WorkflowDefinitions

# Sets up the list of custom workflows that can be used in a pipeline
# The idea being that you can have a pool of workflows that can be used in any number of
# your pipelines
custom_workflows: WorkflowDefinitions = {
    "my_workflow": lambda config: [
        {
            "verb": "derive",
            "args": {
                "column1": "col1",  # looks for col1 in the dataset
                "column2": "col2",  # looks for col2 in the dataset
                "to": config.get(
                    # Allow the user to specify the output column name,
                    # otherwise default to "output_column"
                    "derive_output_column",
                    "output_column",
                ),  # new column name,
                "operator": "*",
            },
        }
    ],
    "my_unused_workflow": lambda _config: [
        {
            "verb": "derive",
            "args": {
                "column1": "col1",  # looks for col1 in the dataset
                "column2": "col2",  # looks for col2 in the dataset
                "to": "unused_output_column",
                "operator": "*",
            },
        }
    ],
}
