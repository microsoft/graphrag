# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Structure response as pydantic base model."""

import json
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel, covariant=True)


def structure_completion_response(response: str, model: type[T]) -> T:
    """Structure completion response as pydantic base model.

    Args
    ----
        response: str
            The completion response as a JSON string.
        model: type[T]
            The pydantic base model type to structure the response into.

    Returns
    -------
        The structured response as a pydantic base model.
    """
    parsed_dict: dict[str, Any] = json.loads(response)
    return model(**parsed_dict)
