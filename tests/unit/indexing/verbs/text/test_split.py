# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import unittest

import pandas as pd
import pytest

from graphrag.index.verbs.text.split import text_split_df


class TestTextSplit(unittest.TestCase):
    def test_empty_string(self):
        input = pd.DataFrame([{"in": ""}])
        result = text_split_df(input, "in", "out", ",").to_dict(orient="records")

        assert len(result) == 1
        assert result[0]["out"] == []

    def test_string_without_seperator(self):
        input = pd.DataFrame([{"in": "test_string_without_seperator"}])
        result = text_split_df(input, "in", "out", ",").to_dict(orient="records")

        assert len(result) == 1
        assert result[0]["out"] == ["test_string_without_seperator"]

    def test_string_with_seperator(self):
        input = pd.DataFrame([{"in": "test_1,test_2"}])
        result = text_split_df(input, "in", "out", ",").to_dict(orient="records")

        assert len(result) == 1
        assert result[0]["out"] == ["test_1", "test_2"]

    def test_row_with_list_as_column(self):
        input = pd.DataFrame([{"in": ["test_1", "test_2"]}])
        result = text_split_df(input, "in", "out", ",").to_dict(orient="records")

        assert len(result) == 1
        assert result[0]["out"] == ["test_1", "test_2"]

    def test_non_string_column_throws_error(self):
        input = pd.DataFrame([{"in": 5}])
        with pytest.raises(TypeError):
            text_split_df(input, "in", "out", ",").to_dict(orient="records")

    def test_more_than_one_row_returns_correctly(self):
        input = pd.DataFrame([{"in": "row_1_1,row_1_2"}, {"in": "row_2_1,row_2_2"}])
        result = text_split_df(input, "in", "out", ",").to_dict(orient="records")

        assert len(result) == 2
        assert result[0]["out"] == ["row_1_1", "row_1_2"]
        assert result[1]["out"] == ["row_2_1", "row_2_2"]
