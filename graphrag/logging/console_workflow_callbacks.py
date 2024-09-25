# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Console-based reporter for the workflow engine."""

from datashaper import NoopWorkflowCallbacks


class ConsoleWorkflowCallbacks(NoopWorkflowCallbacks):
    """A reporter that writes to a console."""

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ):
        """Handle when an error occurs."""
        print(message, str(cause), stack, details)  # noqa T201

    def on_warning(self, message: str, details: dict | None = None):
        """Handle when a warning occurs."""
        _print_warning(message)

    def on_log(self, message: str, details: dict | None = None):
        """Handle when a log message is produced."""
        print(message, details)  # noqa T201


def _print_warning(skk):
    print("\033[93m {}\033[00m".format(skk))  # noqa T201
