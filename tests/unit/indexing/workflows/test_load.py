# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import unittest

import pytest

from graphrag.index.config import PipelineWorkflowReference
from graphrag.index.errors import UnknownWorkflowError
from graphrag.index.workflows.load import create_workflow, load_workflows

from .helpers import mock_verbs, mock_workflows


class TestCreateWorkflow(unittest.TestCase):
    def test_workflow_with_steps_should_not_fail(self):
        create_workflow(
            "workflow_with_steps",
            [
                {
                    "verb": "mock_verb",
                    "args": {
                        "column": "test",
                    },
                }
            ],
            config=None,
            additional_verbs=mock_verbs,
        )

    def test_non_existent_workflow_without_steps_should_crash(self):
        # since we don't have a workflow named "test", and the user didn't provide any steps, we should crash
        # since we don't know what to do
        with pytest.raises(UnknownWorkflowError):
            create_workflow("test", None, config=None, additional_verbs=mock_verbs)

    def test_existing_workflow_should_not_crash(self):
        create_workflow(
            "mock_workflow",
            None,
            config=None,
            additional_verbs=mock_verbs,
            additional_workflows=mock_workflows,
        )


class TestLoadWorkflows(unittest.TestCase):
    def test_non_existent_workflow_should_crash(self):
        with pytest.raises(UnknownWorkflowError):
            load_workflows(
                [
                    PipelineWorkflowReference(
                        name="some_workflow_that_does_not_exist",
                        config=None,
                    )
                ],
                additional_workflows=mock_workflows,
                additional_verbs=mock_verbs,
            )

    def test_single_workflow_should_not_crash(self):
        load_workflows(
            [
                PipelineWorkflowReference(
                    name="mock_workflow",
                    config=None,
                )
            ],
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )

    def test_multiple_workflows_should_not_crash(self):
        load_workflows(
            [
                PipelineWorkflowReference(
                    name="mock_workflow",
                    config=None,
                ),
                PipelineWorkflowReference(
                    name="mock_workflow_2",
                    config=None,
                ),
            ],
            # the two above are in the "mock_workflows" list
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )

    def test_two_interdependent_workflows_should_provide_correct_order(self):
        ordered_workflows, _deps = load_workflows(
            [
                PipelineWorkflowReference(
                    name="interdependent_workflow_1",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                            "input": {
                                "source": "workflow:interdependent_workflow_2"
                            },  # This one is dependent on the second one, so when it comes out of load_workflows, it should be first
                        }
                    ],
                ),
                PipelineWorkflowReference(
                    name="interdependent_workflow_2",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                        }
                    ],
                ),
            ],
            # the two above are in the "mock_workflows" list
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )

        # two should only come out
        assert len(ordered_workflows) == 2
        assert ordered_workflows[0].workflow.name == "interdependent_workflow_2"
        assert ordered_workflows[1].workflow.name == "interdependent_workflow_1"

    def test_three_interdependent_workflows_should_provide_correct_order(self):
        ordered_workflows, _deps = load_workflows(
            [
                PipelineWorkflowReference(
                    name="interdependent_workflow_3",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                        }
                    ],
                ),
                PipelineWorkflowReference(
                    name="interdependent_workflow_1",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                            "input": {"source": "workflow:interdependent_workflow_2"},
                        }
                    ],
                ),
                PipelineWorkflowReference(
                    name="interdependent_workflow_2",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                            "input": {"source": "workflow:interdependent_workflow_3"},
                        }
                    ],
                ),
            ],
            # the two above are in the "mock_workflows" list
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )

        order = [
            "interdependent_workflow_3",
            "interdependent_workflow_2",
            "interdependent_workflow_1",
        ]
        assert [x.workflow.name for x in ordered_workflows] == order

    def test_two_workflows_dependent_on_another_single_workflow_should_provide_correct_order(
        self,
    ):
        ordered_workflows, _deps = load_workflows(
            [
                # Workflows 1 and 2 are dependent on 3, so 3 should come out first
                PipelineWorkflowReference(
                    name="interdependent_workflow_3",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                        }
                    ],
                ),
                PipelineWorkflowReference(
                    name="interdependent_workflow_1",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                            "input": {"source": "workflow:interdependent_workflow_3"},
                        }
                    ],
                ),
                PipelineWorkflowReference(
                    name="interdependent_workflow_2",
                    steps=[
                        {
                            "verb": "mock_verb",
                            "args": {
                                "column": "test",
                            },
                            "input": {"source": "workflow:interdependent_workflow_3"},
                        }
                    ],
                ),
            ],
            # the two above are in the "mock_workflows" list
            additional_workflows=mock_workflows,
            additional_verbs=mock_verbs,
        )

        assert len(ordered_workflows) == 3
        assert ordered_workflows[0].workflow.name == "interdependent_workflow_3"

        # The order of the other two doesn't matter, but they need to be there
        assert ordered_workflows[1].workflow.name in [
            "interdependent_workflow_1",
            "interdependent_workflow_2",
        ]
        assert ordered_workflows[2].workflow.name in [
            "interdependent_workflow_1",
            "interdependent_workflow_2",
        ]
