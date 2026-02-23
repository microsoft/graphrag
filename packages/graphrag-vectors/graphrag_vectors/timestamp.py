# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Timestamp explosion for vector store indexing.

Converts an ISO 8601 timestamp string into a set of filterable component
fields, enabling temporal queries like "find documents from a Monday" or
"find documents from Q3 2024" using the standard filter expression system.

Built-in timestamps:
- create_date: when the document was first created
- update_date: when the document was last updated

User-defined date fields can also be exploded by declaring them with
type "date" in the fields config.
"""

from datetime import datetime

# Suffixes for the exploded component fields
_SUFFIXES: dict[str, str] = {
    "year": "int",
    "month": "int",
    "month_name": "str",
    "day": "int",
    "day_of_week": "str",
    "hour": "int",
    "quarter": "int",
}


def _timestamp_fields_for(prefix: str) -> dict[str, str]:
    """Return the exploded field definitions for a given prefix."""
    return {f"{prefix}_{suffix}": ftype for suffix, ftype in _SUFFIXES.items()}


# Combined field definitions for both timestamps
TIMESTAMP_FIELDS: dict[str, str] = {
    **_timestamp_fields_for("create_date"),
    **_timestamp_fields_for("update_date"),
}


def explode_timestamp(
    iso_timestamp: str | None, prefix: str = "create_date"
) -> dict[str, str | int]:
    """Explode an ISO 8601 timestamp into filterable component fields.

    Parameters
    ----------
    iso_timestamp : str
        An ISO 8601 formatted datetime string (e.g. "2024-03-15T14:30:00").
    prefix : str
        Field name prefix, typically "create_date" or "update_date".

    Returns
    -------
    dict[str, str | int]
        Dictionary with timestamp component fields, e.g.:
        - {prefix}_year (int): e.g. 2024
        - {prefix}_month (int): 1-12
        - {prefix}_month_name (str): e.g. "March"
        - {prefix}_day (int): 1-31
        - {prefix}_day_of_week (str): e.g. "Monday"
        - {prefix}_hour (int): 0-23
        - {prefix}_quarter (int): 1-4

    Example
    -------
        >>> explode_timestamp(
        ...     "2024-03-15T14:30:00",
        ...     "create_date",
        ... )
        {
            'create_date_year': 2024,
            'create_date_month': 3,
            'create_date_month_name': 'March',
            'create_date_day': 15,
            'create_date_day_of_week': 'Friday',
            'create_date_hour': 14,
            'create_date_quarter': 1,
        }
    """
    if not iso_timestamp:
        return {}
    dt = datetime.fromisoformat(iso_timestamp)
    return {
        f"{prefix}_year": dt.year,
        f"{prefix}_month": dt.month,
        f"{prefix}_month_name": dt.strftime("%B"),
        f"{prefix}_day": dt.day,
        f"{prefix}_day_of_week": dt.strftime("%A"),
        f"{prefix}_hour": dt.hour,
        f"{prefix}_quarter": (dt.month - 1) // 3 + 1,
    }
