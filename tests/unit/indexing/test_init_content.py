# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

import re
from typing import Any, cast

import yaml

from graphrag.index.default_config.parameters.models.default_config_parameters_model import (
    DefaultConfigParametersModel,
)
from graphrag.index.init_content import INIT_YAML


def test_init_yaml():
    data = yaml.load(INIT_YAML, Loader=yaml.FullLoader)
    DefaultConfigParametersModel.model_validate(data)


def test_init_yaml_uncommented():
    lines = INIT_YAML.splitlines()
    lines = [line for line in lines if "##" not in line]

    def uncomment_line(line: str) -> str:
        leading_whitespace = cast(Any, re.search(r"^(\s*)", line)).group(1)
        return re.sub(r"^\s*# ", leading_whitespace, line, count=1)

    content = "\n".join([uncomment_line(line) for line in lines])
    data = yaml.load(content, Loader=yaml.FullLoader)
    DefaultConfigParametersModel.model_validate(data)
