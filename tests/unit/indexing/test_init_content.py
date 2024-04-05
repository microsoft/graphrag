# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

import re
from typing import Any, cast

import yaml

from graphrag.index.default_config.parameters.default_config_parameters_model import (
    DefaultConfigParametersModel,
)
from graphrag.index.init_content import INIT_YAML


def test_init_yaml():
    data = yaml.load(INIT_YAML, Loader=yaml.FullLoader)
    DefaultConfigParametersModel.model_validate(data)


def test_init_yaml_uncommented():
    content = (
        INIT_YAML.replace("# llm: override the global llm settings for this task", "")
        .replace(
            "# parallelization: override the global parallelization settings for this task",
            "",
        )
        .replace(
            "# async_mode: override the global async_mode settings for this task", ""
        )
    )
    lines = content.splitlines()

    def uncomment_line(line: str) -> str:
        result = re.sub(r"^(\s*)#", "\\1", line, count=1)
        leading_whitespace = cast(Any, re.search(r"^(\s*)", line)).group(1)
        result = re.sub(r"^\s*#", leading_whitespace, line, count=1)
        if result != line:
            result = result.replace(" ", "", 1)

        if result != line:
            print(f"result\n${line}\n${result}")
        return result

    content = "\n".join([uncomment_line(line) for line in lines])
    data = yaml.load(content, Loader=yaml.FullLoader)
    DefaultConfigParametersModel.model_validate(data)
