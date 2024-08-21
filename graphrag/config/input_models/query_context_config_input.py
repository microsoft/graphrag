from typing_extensions import NotRequired, TypedDict

class QueryContextConfigInput(TypedDict):
    """The default configuration section for Cache."""

    files: NotRequired[str]
    """The root path to run query on."""
