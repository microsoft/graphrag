# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import datetime
import string
import sys
import typing

import typing_extensions

from .. import (
    errors as _errors,
    types as _types,
)


class ANSIFormatter:
    """
    Provides methods and attributes for ANSI color and style formatting in
    console output.
    """
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    REVERSED = '\033[7m'

    @classmethod
    def format(cls, text: str, *styles: str) -> str:
        """
        Formats the given text with the specified ANSI styles.

        If the text already contains the reset code, the styles are reapplied
        after each reset.

        Args:
            text: The text to format.
            *styles: One or more ANSI style codes to apply.

        Returns:
            str: The formatted text with ANSI styles applied.
        """
        if cls.RESET in text:
            text = text.replace(cls.RESET, f"{cls.RESET}{''.join(styles)}")
        return f"{''.join(styles)}{text}{cls.RESET}"


class SafeFormatter(string.Formatter):
    """
    A safe string formatter that handles missing keys and indices gracefully.

    This formatter overrides the default behavior to avoid KeyError or
    IndexError exceptions when formatting strings with missing fields. Instead,
    it leaves placeholders in the output.
    """

    @typing_extensions.override
    def format(self, format_string: str, /, *args: typing.Any, **kwargs: typing.Any) -> str:
        """
        Formats a string safely, handling missing fields without raising
        exceptions.

        Args:
            format_string: The format string containing placeholders.
            *args: Positional arguments to be formatted into the string.
            **kwargs: Keyword arguments to be formatted into the string.

        Returns:
            The formatted string with placeholders replaced by provided
            arguments.
        """
        result = ''
        arg_index = 0

        try:
            for literal_text, field_name, format_spec, conversion in self.parse(format_string):
                # Append the literal text
                result += literal_text

                # If there's a field, process it
                if field_name is not None:
                    # Numeric field
                    if field_name.isdigit():
                        if int(field_name) < len(args):
                            # Get the value
                            obj = args[int(field_name)]
                            # Convert and format the field
                            obj = self.convert_field(obj, conversion)
                            formatted = self.format_field(obj, format_spec or '')
                            result += formatted
                        else:
                            result += '{' + field_name + '}'
                    # Positional argument
                    elif field_name == '':
                        # Get the value
                        if arg_index < len(args):
                            obj = args[arg_index]
                            arg_index += 1
                            # Convert and format the field
                            obj = self.convert_field(obj, conversion)
                            formatted = self.format_field(obj, format_spec or '')
                            result += formatted
                        else:
                            result += '{}'
                    # Keyword argument
                    else:
                        try:
                            # Get the value
                            obj = self.get_value(field_name, args, kwargs)
                            # Convert and format the field
                            obj = self.convert_field(obj, conversion)
                            formatted = self.format_field(obj, format_spec or '')
                            result += formatted
                        except (KeyError, IndexError):
                            # Reconstruct the placeholder and leave it as is
                            placeholder = '{' + field_name
                            if conversion:
                                placeholder += '!' + conversion
                            if format_spec:
                                placeholder += ':' + format_spec
                            placeholder += '}'
                            result += placeholder
        except ValueError:
            result = format_string
        return result

    @typing_extensions.override
    def get_value(
        self,
        key: typing.Union[int, str],
        args: typing.Sequence[typing.Any],
        kwargs: typing.Mapping[str, typing.Any]
    ) -> typing.Any:
        if isinstance(key, int):
            if key < len(args):
                return args[key]
            else:
                raise IndexError(key)
        else:
            return kwargs[key]

    @typing_extensions.override
    def format_field(self, value: typing.Any, format_spec: str) -> str:
        try:
            return super().format_field(value, format_spec)
        except (KeyError, ValueError):
            return str(value)


class CLILogger(_types.Logger):
    """
    A simple logger for CLI applications.
    """

    @staticmethod
    def _safe_format(msg: str, *args: typing.Any, **kwargs: typing.Any) -> str:
        """
        Safely formats a message string using `SafeFormatter`.

        Args:
            msg: The message format string.
            *args: Positional arguments for formatting.
            **kwargs: Keyword arguments for formatting.

        Returns:
            The formatted message string.
        """
        return SafeFormatter().format(msg, *args, **kwargs)

    def _log(self, level: str, color: str, msg: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        """
        Internal method to format and output a log message.

        Args:
            level: The log level name (e.g., 'ERROR', 'INFO').
            color: The ANSI color code to apply to the message.
            msg: The message format string.
            *args: Positional arguments for formatting.
            **kwargs: Keyword arguments for formatting.

        Outputs the formatted message to stdout with timestamp and level.
        """
        timestamp = ANSIFormatter.format(str(datetime.datetime.now()), ANSIFormatter.GREEN)
        level_str = ANSIFormatter.format(f"|{level.ljust(8)}|", color)
        formatted_msg = ANSIFormatter.format(self._safe_format(msg, *args, **kwargs), color, ANSIFormatter.BOLD)
        sys.stdout.write(f"{timestamp} {level_str} {formatted_msg}\n")
        sys.stdout.flush()

    def error(self, msg: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._log("ERROR", ANSIFormatter.RED, msg, *args, **kwargs)

    def warning(self, msg: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._log("WARNING", ANSIFormatter.YELLOW, msg, *args, **kwargs)

    def info(self, msg: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._log("INFO", ANSIFormatter.BLUE, msg, *args, **kwargs)

    def debug(self, msg: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._log("DEBUG", ANSIFormatter.CYAN, msg, *args, **kwargs)


def parse_cli_err(err: _errors.CLIError) -> str:
    if isinstance(err, _errors.InvalidParameterError) or isinstance(err, _errors.MissingPackageError):
        return err.message
    return "An error occurred. Please try again later."
