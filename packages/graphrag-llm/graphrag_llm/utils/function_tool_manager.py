# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Function tool manager."""

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from openai import pydantic_function_tool
from pydantic import BaseModel
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from graphrag_llm.types import LLMCompletionFunctionToolParam, LLMCompletionResponse

FunctionArgumentModel = TypeVar(
    "FunctionArgumentModel", bound=BaseModel, covariant=True
)


class FunctionDefinition(TypedDict, Generic[FunctionArgumentModel]):
    """Function definition."""

    name: str
    description: str
    input_model: type[FunctionArgumentModel]
    function: Callable[[FunctionArgumentModel], str]


class ToolMessage(TypedDict):
    """Function tool response message to be added to message history."""

    content: str
    tool_call_id: str


class FunctionToolManager:
    """Function tool manager."""

    _tools: dict[str, FunctionDefinition[Any]]

    def __init__(self) -> None:
        """Initialize FunctionToolManager."""
        self._tools = {}

    def register_function_tool(
        self,
        *,
        name: str,
        description: str,
        input_model: type[FunctionArgumentModel],
        function: Callable[[FunctionArgumentModel], str],
    ) -> None:
        """Register function tool.

        Args
        ----
            name: str
                The name of the function tool.
            description: str
                The description of the function tool.
            input_model: type[T]
                The pydantic model type for the function tool input.
            function: Callable[[T], str]
                The function to call for the function tool.
        """
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_model": input_model,
            "function": function,
        }

    def definitions(self) -> list["LLMCompletionFunctionToolParam"]:
        """Get function tool definitions.

        Returns
        -------
            list[LLMCompletionFunctionToolParam]
                List of function tool definitions.
        """
        return [
            pydantic_function_tool(
                tool_def["input_model"],
                name=tool_def["name"],
                description=tool_def["description"],
            )
            for tool_def in self._tools.values()
        ]

    def call_functions(self, response: "LLMCompletionResponse") -> list[ToolMessage]:
        """Call functions based on the response.

        Args
        ----
            response: LLMCompletionResponse
                The LLM completion response.

        Returns
        -------
            list[ToolMessage]
                The list of tool response messages to be added to the message history.
        """
        if not response.choices[0].message.tool_calls:
            return []

        tool_messages: list[ToolMessage] = []

        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.type != "function":
                continue
            tool_id = tool_call.id
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments

            if function_name not in self._tools:
                msg = f"Function '{function_name}' not registered."
                raise ValueError(msg)

            tool_def = self._tools[function_name]
            input_model = tool_def["input_model"]
            function = tool_def["function"]

            try:
                parsed_args_dict = json.loads(function_args)
                input_model_instance = input_model(**parsed_args_dict)
            except Exception as e:
                msg = f"Failed to parse arguments for function '{function_name}': {e}"
                raise ValueError(msg) from e

            result = function(input_model_instance)
            tool_messages.append({
                "content": result,
                "tool_call_id": tool_id,
            })

        return tool_messages
