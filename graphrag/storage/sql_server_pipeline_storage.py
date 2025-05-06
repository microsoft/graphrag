# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure SQL Server implementation of PipelineStorage."""

import json
import logging
import re
import struct
from collections.abc import Iterator
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import pyodbc
from azure.identity import DefaultAzureCredential
from pyodbc import Connection

from graphrag.logger.base import ProgressLogger
from graphrag.logger.progress import Progress
from graphrag.storage.pipeline_storage import (
    PipelineStorage,
    get_timestamp_formatted_with_local_tz,
)

log = logging.getLogger(__name__)


class SQLServerPipelineStorage(PipelineStorage):
    """Azure SQL Server implementation of PipelineStorage."""

    _database_name: str
    _database_server_name: str
    _local_connection_string: str
    _autogenerate_tables: bool
    _connection: Connection

    def __init__(
        self,
        database_name: str,
        database_server_name: str,
        autogenerate_tables: bool = True,
        client_id: str | None = None,
    ):
        """Initialize connection to Azure SQL Server."""
        # Currently, the SQL Server storage requires that the database and tables are created before indexing
        # This initialization establishes a connection using the pyodbc SQL driver
        self._database_name = database_name
        self._database_server_name = database_server_name
        self._autogenerate_tables = autogenerate_tables

        # Use password-less authentication for the db server
        self._local_connection_string = f"Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{database_server_name}.database.windows.net,1433;Database={database_name};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;LongAsMax=yes"
        credential = DefaultAzureCredential()

        # These connection options are recommended by Microsoft
        token_bytes = credential.get_token(
            "https://database.windows.net/.default"
        ).token.encode("UTF-16-LE")
        token_struct = struct.pack(
            f"<I{len(token_bytes)}s", len(token_bytes), token_bytes
        )
        sql_copt_ss_access_token = 1256

        # Create initial connection to database
        connection = pyodbc.connect(
            self._local_connection_string,
            attrs_before={sql_copt_ss_access_token: token_struct},
        )
        self._connection = connection
        log.info(
            "Creating connection to SQL Server database e%s on server %s",
            database_name,
            database_server_name,
        )

        if not self._autogenerate_tables:
            self.create_tables()

    def create_tables(self) -> None:
        """Create tables in SQL Server.

        If autogenerate_tables is not enabled, this method will manually create tables for all parquet outputs using a predefined schema.
        """
        # TODO: Currently, most parquet outputs are written to storage and updated multiple times throughout the indexing pipeline, making it difficult to start with a predefined schema.
        # In a future PR, figure out how to use the SQL Server storage with a predefined table schema.
        msg = "SQL Server storage does not yet support manually predefined table creation."
        raise NotImplementedError(msg)

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressLogger | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find tables in SQL Server matching a file pattern.

        This method lists available tables that match the pattern (table names in SQL Server).

        Args:
            file_pattern: The regex pattern to match against table names
            base_dir: Not used for SQL Server
            progress: Optional progress logger
            file_filter: Optional filter dictionary
            max_count: Maximum number of results to return

        Returns
        -------
            Iterator of tuples with table name and match groups
        """
        log.info(
            "Searching SQL Server database %s for tables matching %s",
            self._database_name,
            file_pattern.pattern,
        )

        def item_filter(item: dict[str, Any]) -> bool:
            if file_filter is None:
                return True
            return all(
                re.search(value, item.get(key, ""))
                for key, value in file_filter.items()
            )

        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
            )

            tables = [row[0] for row in cursor.fetchall()]
            num_total = len(tables)
            num_loaded = 0
            num_filtered = 0

            if num_total == 0:
                return

            for table_name in tables:
                match = file_pattern.search(table_name)
                if match:
                    group = match.groupdict()
                    if item_filter(group):
                        yield (table_name, group)
                        num_loaded += 1
                        if max_count > 0 and num_loaded >= max_count:
                            break
                    else:
                        num_filtered += 1
                else:
                    num_filtered += 1

                if progress is not None:
                    progress(
                        _create_progress_status(num_loaded, num_filtered, num_total)
                    )

        except Exception:
            log.exception("An error occurred while searching for tables in SQL Server")

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get data from SQL Server.

        For parquet files, this will query all rows from the table corresponding to the key.

        Args:
            key: The name of the table/file to retrieve
            as_bytes: If True, returns parquet bytes for DataFrame data
            encoding: Not used for SQL Server

        Returns
        -------
            Parquet bytes or JSON string representation of the data
        """
        # Only retrieve table contents for parquet files
        if key.endswith(".parquet") and as_bytes:
            try:
                table_name = key.split(".")[0]
                query = f"SELECT * FROM [{table_name}]"  # noqa: S608

                cursor = self._connection.cursor()
                cursor.execute(query)

                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

                # Construct a dataframe from the query results
                data = []
                for row in rows:
                    processed_row = []
                    for val in row:
                        if val is None:
                            processed_row.append(val)
                        elif isinstance(val, bytearray):
                            processed_row.append(bytes(val))
                        elif (
                            isinstance(val, str)
                            and val.startswith("[")
                            and val.endswith("]")
                        ):
                            # Parse strings that are fetched as serialized lists
                            import ast

                            try:
                                parsed_val = ast.literal_eval(val)
                                if isinstance(parsed_val, list):
                                    processed_row.append(parsed_val)
                                else:
                                    processed_row.append(val)
                            except (SyntaxError, ValueError):
                                processed_row.append(val)
                        else:
                            processed_row.append(val)
                    data.append(processed_row)

                # Create DataFrame from processed data
                data_frame = pd.DataFrame(data, columns=np.array(columns))
                buffer = BytesIO()
                data_frame.to_parquet(buffer)
                buffer.seek(0)

                log.info(
                    "Successfully fetched table contents for %s from SQL Server", key
                )
                return buffer.read()
            except Exception:
                log.exception("Error reading data %s", key)
                return None
        else:
            log.warning(
                "Attempted to call get() on SQL Server storage with non-parquet key %s. Skipping...",
                key,
            )
            return None
        
    def _get_embeddings_dimension(self, df: pd.DataFrame) -> int:
        """Get the dimension of the embeddings column in the DataFrame.

        Args:
            df: The DataFrame containing the embeddings column

        Returns
        -------
            The dimension of the embeddings column
        """
        if "embedding" in df.columns:
            embedding_column = df["embedding"].iloc[0]
            if isinstance(embedding_column, list):
                return len(embedding_column)
            if isinstance(embedding_column, np.ndarray):
                return embedding_column.shape[0]
        return 0

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set data in SQL Server.

        For parquet files, this creates or replaces a table with the DataFrame data.

        Args:
            key: The table/file name
            value: Either bytes (parquet) or string (JSON) (only parquet files are written to SQL Server)
            encoding: Not used for SQL Server
        """
        try:
            # Only store parquet file data
            if isinstance(value, bytes) and key.endswith(".parquet"):
                table_name = key.split(".")[0]
                data_frame = pd.read_parquet(BytesIO(value))

                # Automatically build CREATE TABLE statement based on DataFrame columns
                if self._autogenerate_tables:
                    cursor = self._connection.cursor()
                    columns = []
                    for col_name, dtype in zip(
                        data_frame.columns, data_frame.dtypes, strict=False
                    ):
                        sql_type = "NVARCHAR(MAX)"  # Default type

                        # Map pandas dtypes to SQL Server types
                        if col_name == "embedding":
                            # If we are writing the vector embeddings dataframe, set the embedding column to VECTOR
                            dim = self._get_embeddings_dimension(data_frame)
                            sql_type = f"VECTOR({dim})" if dim != 0 else "VECTOR(1536)"  # GraphRAG default embedding dimension
                        elif pd.api.types.is_integer_dtype(dtype):
                            sql_type = "BIGINT"
                        elif pd.api.types.is_float_dtype(dtype):
                            sql_type = "FLOAT"
                        elif pd.api.types.is_bool_dtype(dtype):
                            sql_type = "BIT"
                        elif pd.api.types.is_datetime64_dtype(dtype):
                            sql_type = "DATETIME2"

                        columns.append(f"[{col_name}] {sql_type}")

                    cursor.execute(
                        f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE [{table_name}]"
                    )
                    create_table_sql = (
                        f"CREATE TABLE [{table_name}] ({', '.join(columns)})"
                    )
                    log.info(
                        "Automatically generated table: %s with columns: %s",
                        table_name,
                        columns,
                    )
                    cursor.execute(create_table_sql)
                    self._connection.commit()

                # Insert parquet data into SQL server
                num_rows = len(data_frame)
                placeholders = ", ".join([
                    "?" for _ in range(len(data_frame.columns))
                ])
                column_names = ", ".join([
                    f"[{col}]" for col in data_frame.columns
                ])
                insert_sql = f"INSERT INTO [{table_name}] ({column_names}) VALUES ({placeholders})"  # noqa: S608
                log.info(
                    "Inserting %s rows into table %s", num_rows, table_name
                )

                # Use a row-wise cursor loop for small tables
                if num_rows < 1000:
                    cursor = self._connection.cursor()
                    for _, row in data_frame.iterrows():
                        try:
                            # Handle various value types, converting complex types to strings
                            values = []
                            for val in row:
                                if isinstance(val, np.ndarray):
                                    values.append(json.dumps(val.tolist()))
                                elif isinstance(val, list):
                                    values.append(json.dumps(val))
                                elif pd.isna(val):
                                    values.append(None)
                                else:
                                    values.append(val)
                            cursor.execute(insert_sql, values)
                        except Exception:  # noqa: BLE001
                            log.info(
                                "Error inserting row %s into table: %s, skipping...",
                                row.to_dict(),
                                table_name,
                            )
                            continue
                # For large tables, use a bulk insert strategy
                else:
                    cursor = self._connection.cursor()
                    cursor.fast_executemany = True
                    bulk_values = []
                    for row in data_frame.itertuples(index=False):
                        # Handle various value types, converting complex types to strings
                        values = []
                        for val in row:
                            if isinstance(val, np.ndarray):
                                values.append(json.dumps(val.tolist()))
                            elif isinstance(val, list):
                                values.append(json.dumps(val))
                            elif pd.isna(val):
                                values.append(None)
                            else:
                                values.append(val)
                        bulk_values.append(values)
                    cursor.executemany(insert_sql, bulk_values)
                self._connection.commit()
                log.info("Successfully stored %s in SQL Server", key)
            else:
                log.warning(
                    "Attempted to call set() on SQL Server storage with non-parquet key %s. Skipping...",
                    key,
                )
        except Exception:
            self._connection.commit()
            log.exception("Error writing data %s: %s.", key)

    async def has(self, key: str) -> bool:
        """Check if a table/file exists in SQL Server.

        Args:
            key: The table/file name to check

        Returns
        -------
            True if the table or metadata entry exists
        """
        try:
            # Only check existence for parquet files, otherwise return False
            if key.endswith(".parquet"):
                cursor = self._connection.cursor()
                table_name = key.split(".")[0]
                cursor.execute(
                    "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?",
                    table_name,
                )
                return cursor.fetchone() is not None
        except Exception:
            log.exception("Error checking existence of %s: %s", key)
            return False
        else:
            log.warning(
                "Attempted to call has() on SQL Server storage with non-parquet key %s",
                key,
            )
            return False

    async def delete(self, key: str) -> None:
        """Delete a table/file from SQL Server.

        Args:
            key: The table/file name to delete
        """
        # Only delete parquet files
        if key.endswith(".parquet"):
            try:
                table_name = key.split(".")[0]
                cursor = self._connection.cursor()
                cursor.execute(
                    f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE [{table_name}]"
                )
                self._connection.commit()
                log.info("Successfully deleted %s from SQL Server", key)
            except Exception:
                self._connection.rollback()
                log.exception("Error deleting %s: %s", key)
        else:
            log.warning(
                "Attempted to call delete() on SQL Server storage with non-parquet key %s. Skipping...",
                key,
            )

    async def clear(self) -> None:
        """Clear the pipeline storage."""
        msg = "SQL Server storage does not yet support the clear operation."
        raise NotImplementedError(msg)

    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child pipeline storage."""
        return self

    def keys(self) -> list[str]:
        """List all keys in the storage."""
        msg = "SQL Server storage does not yet support listing keys."
        raise NotImplementedError(msg)

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for a table or metadata entry.

        Args:
            key: The table/file name

        Returns
        -------
            Formatted timestamp of creation date or empty string
        """
        try:
            # Only get creation date for parquet files
            if key.endswith(".parquet"):
                cursor = self._connection.cursor()
                table_name = key.split(".")[0]
                cursor.execute(
                    """
                    SELECT create_date
                    FROM sys.tables t
                    JOIN sys.objects o ON t.object_id = o.object_id
                    WHERE t.name = ?
                """,
                    table_name,
                )
                row = cursor.fetchone()
                if row:
                    log.info("Successfully retrieved creation date for %s", key)
                    return get_timestamp_formatted_with_local_tz(row[0])
                return ""
        except Exception:
            log.exception("Error getting creation date for %s: %s", key)
            return ""
        else:
            log.warning(
                "Attempted to call get_creation_date() on SQL Server storage with non-parquet key %s",
                key,
            )
            return ""


def create_sql_server_storage(**kwargs: Any) -> PipelineStorage:
    """Create a SQLServer storage instance."""
    log.info("Creating SQL Server storage")
    database_name = kwargs.get("database_name")
    database_server_name = kwargs.get("database_server_name")
    autogenerate_tables = kwargs.get("autogenerate_tables", True)
    connection_string = kwargs.get("connection_string")
    client_id = kwargs.get("client_id")
    if connection_string:
        msg = "SQL Server storage does not support connection string authentication. Use managed-identities instead."
        raise ValueError(msg)
    if not database_name or not database_server_name:
        msg = "Both 'database_name' and 'database_server_name' must be provided."
        raise ValueError(msg)
    return SQLServerPipelineStorage(
        database_name=database_name,
        database_server_name=database_server_name,
        autogenerate_tables=autogenerate_tables,
        client_id=client_id,
    )


def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
