# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import logging
import os
import unittest

from graphrag.index.run import run_pipeline_with_config
from graphrag.index.typing import PipelineRunResult

log = logging.getLogger(__name__)


class TestRun(unittest.IsolatedAsyncioTestCase):
    async def test_megapipeline(self):
        pipeline_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "./megapipeline.yml",
        )
        pipeline_result = [gen async for gen in run_pipeline_with_config(pipeline_path)]

        errors = []
        for result in pipeline_result:
            if result.errors is not None and len(result.errors) > 0:
                errors.extend(result.errors)

        if len(errors) > 0:
            print("Errors: ", errors)
        assert len(errors) == 0, "received errors\n!" + "\n".join(errors)

        self._assert_text_units_and_entities_reference_each_other(pipeline_result)

    def _assert_text_units_and_entities_reference_each_other(
        self, pipeline_result: list[PipelineRunResult]
    ):
        text_unit_df = next(
            filter(lambda x: x.workflow == "create_final_text_units", pipeline_result)
        ).result
        entity_df = next(
            filter(lambda x: x.workflow == "create_final_entities", pipeline_result)
        ).result

        assert text_unit_df is not None, "Text unit dataframe should not be None"
        assert entity_df is not None, "Entity dataframe should not be None"

        # Get around typing issues
        if text_unit_df is None or entity_df is None:
            return

        assert len(text_unit_df) > 0, "Text unit dataframe should not be empty"
        assert len(entity_df) > 0, "Entity dataframe should not be empty"

        text_unit_entity_map = {}
        log.info("text_unit_df %s", text_unit_df.columns)

        for _, row in text_unit_df.iterrows():
            values = row.get("entity_ids", [])
            text_unit_entity_map[row["id"]] = set([] if values is None else values)

        entity_text_unit_map = {}
        for _, row in entity_df.iterrows():
            # ALL entities should have text units
            values = row.get("text_unit_ids", [])
            entity_text_unit_map[row["id"]] = set([] if values is None else values)

        text_unit_ids = set(text_unit_entity_map.keys())
        entity_ids = set(entity_text_unit_map.keys())

        for text_unit_id, text_unit_entities in text_unit_entity_map.items():
            assert text_unit_entities.issubset(
                entity_ids
            ), f"Text unit {text_unit_id} has entities {text_unit_entities} that are not in the entity set"
        for entity_id, entity_text_units in entity_text_unit_map.items():
            assert entity_text_units.issubset(
                text_unit_ids
            ), f"Entity {entity_id} has text units {entity_text_units} that are not in the text unit set"
