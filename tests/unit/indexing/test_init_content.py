# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

import re
from typing import Any, cast

import yaml

from graphrag.config import (
    DefaultConfigParametersModel,
    default_config_parameters,
)
from graphrag.index.init_content import INIT_YAML


def test_init_yaml():
    data = yaml.load(INIT_YAML, Loader=yaml.FullLoader)
    config = default_config_parameters(data)
    DefaultConfigParametersModel.model_validate(config, strict=True)


def test_init_yaml_uncommented():
    lines = INIT_YAML.splitlines()
    lines = [line for line in lines if "##" not in line]

    def uncomment_line(line: str) -> str:
        leading_whitespace = cast(Any, re.search(r"^(\s*)", line)).group(1)
        return re.sub(r"^\s*# ", leading_whitespace, line, count=1)

    content = "\n".join([uncomment_line(line) for line in lines])
    data = yaml.load(content, Loader=yaml.FullLoader)
    config = default_config_parameters(data)
    DefaultConfigParametersModel.model_validate(config, strict=True)
