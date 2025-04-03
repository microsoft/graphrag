# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure SQL Server implementation of PipelineStorage."""

import json
import logging
import re
import struct
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any
from io import BytesIO

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
    _connection: Connection

    def __init__(
        self,
        database_name: str,
        database_server_name: str,
    ):
        """Initialize connection to Azure SQL Server."""
        # Currently, the SQL Server storage requires that the database and tables are created before indexing
        # This initialization establishes a connection using the pyodbc SQL driver
        self._database_name = database_name
        self._database_server_name = database_server_name

        # Use password-less authentication for the db server
        self._local_connection_string = f"Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{database_server_name}.database.windows.net,1433;Database={database_name};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
        credential = DefaultAzureCredential()

        # These connection options are recommended by Microsoft
        token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        sql_copt_ss_access_token = 1256

        # Create initial connection to database
        connection = pyodbc.connect(self._local_connection_string, attrs_before={sql_copt_ss_access_token: token_struct})
        self._connection = connection

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
            
        Returns:
            Iterator of tuples with table name and match groups
        """
        log.info(
            "searching SQL Server database %s for tables matching %s",
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
            # Query SQL Server for all table names in the current database
            cursor = self._connection.cursor()
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            
            # Get all tables
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
                    progress(_create_progress_status(num_loaded, num_filtered, num_total))
        
        except Exception:
            log.exception("An error occurred while searching for tables in SQL Server")
            
    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get data from SQL Server.
        
        For parquet files, this will query all rows from the table corresponding to the key.
        For other files, this will look for a special metadata table.
        
        Args:
            key: The name of the table/file to retrieve
            as_bytes: If True, returns parquet bytes for DataFrame data
            encoding: Not used for SQL Server
            
        Returns:
            Parquet bytes or JSON string representation of the data
        """
        try:
            # If this is a parquet file request, return the table contents as parquet
            if as_bytes and key.endswith('.parquet'):
                table_name = key.split('.')[0]
                
                # Query all data from the table
                query = f"SELECT * FROM [{table_name}]"
                df = pd.read_sql(query, self._connection)
                
                # Convert to parquet bytes
                return df.to_parquet()
            else:
                # For other types of data, assume it's stored in a metadata table
                cursor = self._connection.cursor()
                cursor.execute("SELECT metadata_value FROM metadata_store WHERE metadata_key = ?", key)
                row = cursor.fetchone()
                if row:
                    return row[0]  # Return the stored JSON string
                return None
        except Exception:
            log.exception("Error reading data %s", key)
            return None
            
    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set data in SQL Server.
        
        For parquet files, this creates or replaces a table with the DataFrame data.
        For other files, this stores the data in a special metadata table.
        
        Args:
            key: The table/file name
            value: Either bytes (parquet) or string (JSON)
            encoding: Not used for SQL Server
        """
        try:
            cursor = self._connection.cursor()
            
            # For parquet files (DataFrame data)
            if isinstance(value, bytes) and key.endswith('.parquet'):
                table_name = key.split('.')[0]
                
                # Read DataFrame from parquet bytes
                df = pd.read_parquet(BytesIO(value))
                
                # Create table (overwrite if exists)
                cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE [{table_name}]")
                
                # Build CREATE TABLE statement based on DataFrame columns
                columns = []
                for col_name, dtype in zip(df.columns, df.dtypes):
                    sql_type = "NVARCHAR(MAX)"  # Default type
                    
                    # Map pandas dtypes to SQL Server types
                    if pd.api.types.is_integer_dtype(dtype):
                        sql_type = "BIGINT"
                    elif pd.api.types.is_float_dtype(dtype):
                        sql_type = "FLOAT"
                    elif pd.api.types.is_bool_dtype(dtype):
                        sql_type = "BIT"
                    elif pd.api.types.is_datetime64_dtype(dtype):
                        sql_type = "DATETIME2"
                        
                    columns.append(f"[{col_name}] {sql_type}")
                
                create_table_sql = f"CREATE TABLE [{table_name}] ({', '.join(columns)})"
                cursor.execute(create_table_sql)
                
                # Insert data
                for _, row in df.iterrows():
                    placeholders = ", ".join(["?" for _ in range(len(df.columns))])
                    column_names = ", ".join([f"[{col}]" for col in df.columns])
                    insert_sql = f"INSERT INTO [{table_name}] ({column_names}) VALUES ({placeholders})"
                    
                    # Handle None/NaN values and convert to list
                    values = [None if pd.isna(val) else val for val in row.tolist()]
                    cursor.execute(insert_sql, values)
            else:
                # For other types (metadata/JSON data), store in a metadata table
                
                # Ensure metadata table exists
                cursor.execute("""
                IF OBJECT_ID('metadata_store', 'U') IS NULL
                CREATE TABLE metadata_store (
                    metadata_key NVARCHAR(255) PRIMARY KEY,
                    metadata_value NVARCHAR(MAX),
                    created_at DATETIME2 DEFAULT GETUTCDATE()
                )
                """)
                
                # Upsert the metadata value
                cursor.execute("""
                MERGE metadata_store AS target
                USING (SELECT ? AS metadata_key, ? AS metadata_value) AS source
                ON target.metadata_key = source.metadata_key
                WHEN MATCHED THEN
                    UPDATE SET target.metadata_value = source.metadata_value, target.created_at = GETUTCDATE()
                WHEN NOT MATCHED THEN
                    INSERT (metadata_key, metadata_value) VALUES (source.metadata_key, source.metadata_value);
                """, key, value)
                
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            log.exception("Error writing data %s", key)
    
    async def has(self, key: str) -> bool:
        """Check if a table/file exists in SQL Server.
        
        Args:
            key: The table/file name to check
            
        Returns:
            True if the table or metadata entry exists
        """
        try:
            cursor = self._connection.cursor()
            
            if key.endswith('.parquet'):
                # Check for table existence
                table_name = key.split('.')[0]
                cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", table_name)
                return cursor.fetchone() is not None
            else:
                # Check for metadata entry
                cursor.execute("SELECT 1 FROM metadata_store WHERE metadata_key = ?", key)
                return cursor.fetchone() is not None
        except Exception:
            log.exception("Error checking existence of %s", key)
            return False
    
    async def delete(self, key: str) -> None:
        """Delete a table/file from SQL Server.
        
        Args:
            key: The table/file name to delete
        """
        try:
            cursor = self._connection.cursor()
            
            if key.endswith('.parquet'):
                # Delete table
                table_name = key.split('.')[0]
                cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE [{table_name}]")
            else:
                # Delete metadata entry
                cursor.execute("DELETE FROM metadata_store WHERE metadata_key = ?", key)
                
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            log.exception("Error deleting %s", key)

    async def clear(self) -> None:
        """Clear the pipeline storage."""
        msg = "SQL Server storage does yet not support clear operation."
        raise NotImplementedError(msg)
    
    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child pipeline storage."""
        return self
    
    def keys(self) -> list[str]:
        """List all keys in the storage."""
        msg = "SQL Server storage does yet not support listing keys."
        raise NotImplementedError(msg)
    
    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for a table or metadata entry.
        
        Args:
            key: The table/file name
            
        Returns:
            Formatted timestamp of creation date or empty string
        """
        try:
            cursor = self._connection.cursor()
            
            if key.endswith('.parquet'):
                # Get table creation date from system tables
                table_name = key.split('.')[0]
                cursor.execute("""
                    SELECT create_date 
                    FROM sys.tables t
                    JOIN sys.objects o ON t.object_id = o.object_id
                    WHERE t.name = ?
                """, table_name)
                row = cursor.fetchone()
                if row:
                    return get_timestamp_formatted_with_local_tz(row[0])
            else:
                # Get metadata entry creation date
                cursor.execute("SELECT created_at FROM metadata_store WHERE metadata_key = ?", key)
                row = cursor.fetchone()
                if row:
                    return get_timestamp_formatted_with_local_tz(row[0])
            
            return ""
        except Exception:
            log.exception("Error getting creation date for %s", key)
            return ""
    
def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )

