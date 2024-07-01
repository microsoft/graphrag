# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
mock_verbs = {
    "mock_verb": lambda x: x,
    "mock_verb_2": lambda x: x,
}

mock_workflows = {
    "mock_workflow": lambda _x: [
        {
            "verb": "mock_verb",
            "args": {
                "column": "test",
            },
        }
    ],
    "mock_workflow_2": lambda _x: [
        {
            "verb": "mock_verb",
            "args": {
                "column": "test",
            },
        },
        {
            "verb": "mock_verb_2",
            "args": {
                "column": "test",
            },
        },
    ],
}
