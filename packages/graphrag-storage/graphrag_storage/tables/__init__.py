# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Table provider module for GraphRAG storage."""

from .parquet_table_provider import ParquetTableProvider
from .table_provider import TableProvider

__all__ = ["ParquetTableProvider", "TableProvider"]
