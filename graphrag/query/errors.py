# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

import typing

import openai
import pydantic
import typing_extensions

__all__ = [
    'GraphRAGError',
    'ClientError',
    'CLIError',
    'InvalidMessageError',
    'InvalidEngineError',
    'InvalidParameterError',
]


class GraphRAGWarning(Warning):
    pass


class GraphRAGError(Exception):
    pass


class ClientError(GraphRAGError):
    pass


class InvalidEngineError(GraphRAGError):
    def __init__(
        self,
        engine: str,
        message: str = "The engine is invalid"
    ):
        self.engine = engine
        self.message = message
        super().__init__(message)

    @typing_extensions.override
    def __str__(self):
        return self.message

    @typing_extensions.override
    def __repr__(self):
        return f"{self.__class__.__name__}(engine={self.engine!r}, message={self.message!r})"


class CLIError(GraphRAGError):
    pass


# Client Errors
class InvalidMessageError(ClientError):
    def __init__(
        self,
        message: str = "The message must be in the format of alternating roles with the last role being 'user'"
    ):
        self.message = message
        super().__init__(message)

    @typing_extensions.override
    def __str__(self):
        return self.message

    @typing_extensions.override
    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r})"


class OpenAIAPIError(ClientError):
    def __init__(
        self,
        error: openai.APIError,
        message: str = "An error occurred while making a request to the OpenAI API",
    ):
        self.message = message + f": {error.message}"
        self.error = error
        super().__init__(self.message)

    @typing_extensions.override
    def __str__(self):
        return self.message

    @typing_extensions.override
    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r})"


# CLI Errors
class InvalidParameterError(CLIError):
    def __init__(
        self,
        *,
        params: typing.List[str],
        reason: typing.List[str],
        message: str = "Invalid parameter(s): \n"
    ) -> None:
        self.params = params
        self.reason = reason
        self.message = message
        for i in range(len(params)):
            self.message += f"  - {params[i]}: {reason[i]}\n"
        super().__init__(self.message)

    @classmethod
    def from_pydantic_validation_error(cls, validation_error: pydantic.ValidationError) -> typing.Self:
        params = []
        reason = []
        for error in validation_error.errors():
            params.append(str(error["loc"][0]))
            reason.append(error["msg"])
        return cls(params=params, reason=reason)

    @typing_extensions.override
    def __str__(self):
        return self.message

    @typing_extensions.override
    def __repr__(self):
        return f"{self.__class__.__name__}(params={self.params!r}, message={self.message!r})"


class MissingPackageError(CLIError):
    def __init__(
        self,
        packages: typing.List[str],
        message: str = "The package is required for this operation: \n"
    ):
        self.packages = packages
        self.message = message
        for package in packages:
            self.message += f"  - {package}\n"
        super().__init__(self.message)

    @typing_extensions.override
    def __str__(self):
        return self.message

    @typing_extensions.override
    def __repr__(self):
        return f"{self.__class__.__name__}(packages={self.packages!r}, message={self.message!r})"
