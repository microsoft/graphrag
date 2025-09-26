# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""PostgreSQL Storage implementation of PipelineStorage."""

import json
import logging
import re
from collections.abc import Iterator
from io import BytesIO
from typing import Any
import numpy as np
import pandas as pd
import asyncpg
from asyncpg import Connection, Pool

from graphrag.storage.pipeline_storage import (
    PipelineStorage,
    get_timestamp_formatted_with_local_tz,
)

log = logging.getLogger(__name__)

class PostgresPipelineStorage(PipelineStorage):
    """The PostgreSQL Storage Implementation."""

    _pool: Pool | None
    _connection_string: str
    _database: str
    _collection_prefix: str
    _encoding: str

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "graphrag",
        username: str = "postgres",
        password: str | None = None,
        collection_prefix: str = "lgr_",
        encoding: str = "utf-8",
        connection_string: str | None = None,
        command_timeout: int = 600,      # 10 minutes for SQL commands
        server_timeout: int = 120,       # 2 minutes for server connection
        connection_timeout: int = 60,    # 1 minute to establish connection
        batch_size: int = 50,           # Smaller batch size to reduce timeout risk
        **kwargs: Any,
    ):
        """Initialize the PostgreSQL Storage."""
        self._host = host
        self._port = port
        self._database = database
        self._username = username
        self._password = password
        self._collection_prefix = collection_prefix
        self._encoding = encoding
        self._command_timeout = command_timeout
        self._server_timeout = server_timeout
        self._connection_timeout = connection_timeout
        self._batch_size = batch_size
        self._pool = None

        # Build connection string from components or use provided one
        if connection_string:
            self._connection_string = connection_string
        else:
            if password:
                self._connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            else:
                self._connection_string = f"postgresql://{username}@{host}:{port}/{database}"

        log.info(
            "Initializing PostgreSQL storage with host: %s:%s, database: %s, collection_prefix: %s, command_timeout: %s, batch_size: %s",
            self._host,
            self._port,
            self._database,
            self._collection_prefix,
            self._command_timeout,
            self._batch_size,
        )

    async def _get_connection(self) -> Connection:
        """Get a database connection from the pool."""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    self._connection_string,
                    min_size=1,
                    max_size=10,
                    command_timeout=self._command_timeout,
                    server_settings={
                        'application_name': 'graphrag_postgres_storage'
                    },
                    # Use connection_timeout for initial connection establishment
                    timeout=self._connection_timeout
                )
                log.info("Created PostgreSQL connection pool with command_timeout: %s, connection_timeout: %s", 
                        self._command_timeout, self._connection_timeout)
            except Exception as e:
                log.error("Failed to create PostgreSQL connection pool: %s", e)
                raise

        return await self._pool.acquire()

    async def _release_connection(self, conn: Connection) -> None:
        """Release a connection back to the pool."""
        if self._pool:
            await self._pool.release(conn)

    def _get_table_name(self, key: str) -> str:
        """Get the table name for a given key."""
        # Extract the base name without file extension
        base_name = key.split(".")[0]
        return f"{self._collection_prefix}{base_name}"

    def _get_prefix(self, key: str) -> str:
        """Get the prefix of the filename key."""
        return key.split(".")[0]

    async def _ensure_table_exists(self, table_name: str) -> None:
        """Ensure a table exists, create if it doesn't."""
        conn = await self._get_connection()
        try:
            # Create table with flexible schema similar to CosmosDB approach
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id TEXT PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);
            CREATE INDEX IF NOT EXISTS idx_{table_name}_data_gin ON {table_name} USING GIN(data);
            """
            
            await conn.execute(create_sql)
            log.debug("Ensured table exists: %s", table_name)
        finally:
            await self._release_connection(conn)

    def _is_scalar_na(self, value: Any) -> bool:
        """Safely check if a value is NA/null, avoiding issues with arrays."""
        try:
            # Handle arrays/lists - check if it's an array-like object
            if hasattr(value, '__len__') and hasattr(value, '__getitem__'):
                # For arrays, check if all elements are NA
                if isinstance(value, (list, tuple)):
                    return all(pd.isna(item) if not hasattr(item, '__len__') or len(str(item)) < 100 else False for item in value)
                elif hasattr(value, 'size'):
                    # NumPy array - be careful with large arrays
                    if value.size > 100:
                        return False
                    try:
                        return pd.isna(value).all() if value.size > 1 else pd.isna(value.item())
                    except (ValueError, TypeError):
                        return False
                else:
                    return False
            
            # For scalar values, use pandas isna
            return pd.isna(value)
        except (ValueError, TypeError):
            # If pd.isna fails, assume it's not NA
            return False
    def _prepare_data_for_postgres(self, df: pd.DataFrame, table_name: str) -> list[dict]:
        """Prepare DataFrame data for PostgreSQL insertion following CosmosDB pattern."""
        log.info(f"Preparing data for table {table_name}, DataFrame shape: {df.shape}")
        log.info(f"DataFrame columns: {df.columns.tolist()}")
        
        # Add human_readable_id if missing
        if 'human_readable_id' not in df.columns:
            df = df.copy()
            df['human_readable_id'] = range(len(df))
            log.info(f"Generated sequential human_readable_id for {len(df)} records")
        
        # Process IDs
        ids = df['id'].astype(str).tolist()
        
        records = []
        for i in range(len(df)):
            # Create record with ID and all data in JSONB field
            record_data = df.iloc[i].to_dict()
            
            # Convert numpy types to native Python types for JSON serialization
            for key, value in record_data.items():
                if key in ['text_unit_ids', 'children', 'entity_ids', 'relationship_ids', 'document_ids']:
                    # Clean list fields during storage preparation
                    if isinstance(value, list):
                        record_data[key] = self._ensure_string_list(value)
                    elif self._is_scalar_na(value) or value is None:
                        record_data[key] = []
                    elif hasattr(value, '__len__') and len(value) == 0:
                        # Handle empty arrays/lists
                        record_data[key] = []
                    elif hasattr(value, '__len__') and len(value) > 0:
                        # Handle non-empty arrays/lists
                        record_data[key] = self._ensure_string_list(value.tolist() if hasattr(value, 'tolist') else list(value))
                    else:
                        # Handle single values or other scalar types
                        record_data[key] = [str(value)] if str(value).strip() else []
                elif isinstance(value, (list, dict)):
                    # Keep other lists and dicts as-is
                    record_data[key] = value
                elif hasattr(value, 'item') and hasattr(value, 'size') and value.size == 1:
                    # Only use .item() for numpy scalars (arrays of size 1)
                    record_data[key] = value.item()
                elif hasattr(value, 'tolist'):
                    # Convert numpy arrays to Python lists
                    record_data[key] = value.tolist()
                elif isinstance(value, pd.Timestamp):
                    # Handle pandas Timestamp objects
                    try:
                        record_data[key] = value.isoformat() if not self._is_scalar_na(value) else None
                    except AttributeError:
                        record_data[key] = str(value) if not self._is_scalar_na(value) else None
                elif hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat', None)):
                    # Handle other datetime-like objects
                    try:
                        record_data[key] = value.isoformat() if not self._is_scalar_na(value) else None
                    except (AttributeError, TypeError):
                        record_data[key] = str(value) if not self._is_scalar_na(value) else None
                elif self._is_scalar_na(value):
                    # Only check pd.isna for scalar-like values
                    record_data[key] = None
                elif isinstance(value, (list, np.ndarray)) and len(value) == 0:
                    # Handle empty arrays/lists
                    record_data[key] = []
                else:
                    record_data[key] = value
            
            record = {
                'id': ids[i],
                'data': record_data
            }
            records.append(record)
        
        log.info(f"Prepared {len(records)} records for PostgreSQL")
        return records
    async def _batch_upsert_records(self, conn: Connection, table_name: str, records: list[dict]) -> None:
        """Perform high-performance batch upsert of records using executemany."""
        total_records = len(records)
        batch_size = self._batch_size
        log.info(f"Starting batch upsert of {total_records} records to {table_name} with batch size {batch_size}")
        
        processed_count = 0
        
        # Process records in batches for optimal performance
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            batch_end = min(i + batch_size, total_records)
            
            # Prepare batch data
            ids = [record['id'] for record in batch]
            data_json_list = [json.dumps(record['data']) for record in batch]
            
            try:
                async with conn.transaction():
                    # Use executemany for reliable batch processing
                    upsert_sql = f"""
                        INSERT INTO {table_name} (id, data, updated_at)
                        VALUES ($1, $2, NOW())
                        ON CONFLICT (id) 
                        DO UPDATE SET 
                            data = EXCLUDED.data,
                            updated_at = NOW()
                    """
                    
                    # Prepare data for executemany
                    batch_data = [(record_id, data_json) for record_id, data_json in zip(ids, data_json_list)]
                    await conn.executemany(upsert_sql, batch_data)
                    
            except Exception as e:
                log.warning(f"Batch method failed for batch {i}-{batch_end}, falling back to individual inserts: {e}")
                
                # Fallback to individual inserts within the batch
                try:
                    async with conn.transaction():
                        upsert_sql = f"""
                            INSERT INTO {table_name} (id, data, updated_at)
                            VALUES ($1, $2, NOW())
                            ON CONFLICT (id) 
                            DO UPDATE SET 
                                data = EXCLUDED.data,
                                updated_at = NOW()
                        """
                        
                        for record_id, data_json in zip(ids, data_json_list):
                            await conn.execute(upsert_sql, record_id, data_json)
                except Exception as inner_e:
                    log.error(f"Both batch and individual insert methods failed for batch {i}-{batch_end}: {inner_e}")
                    raise
            
            processed_count += len(batch)
            
            # Log progress every batch for visibility
            # if i % batch_size == 0 or batch_end == total_records:
            #     log.debug(f"Batch upsert progress: {processed_count}/{total_records} records ({processed_count/total_records*100:.1f}%)")
    
    def find(
    self,
    file_pattern: re.Pattern[str],
    base_dir: str | None = None,
    file_filter: dict[str, Any] | None = None,
    max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        return iter([])
        
    def _parse_jsonb_field(self, value: Any, default_type: str = "list") -> Any:
        """Parse JSONB field back to Python object with better type consistency."""
        if value is None:
            return {} if default_type == "dict" else []
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                # Ensure we return the correct type
                if default_type == "dict":
                    return parsed if isinstance(parsed, dict) else {}
                else:
                    return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return {} if default_type == "dict" else []
        # For any other type (including float/NaN), return empty default
        return {} if default_type == "dict" else []

    def _convert_dataframe_to_parquet_bytes(self, df: pd.DataFrame) -> bytes:
        """Convert DataFrame to parquet bytes."""
        try:
            buffer = BytesIO()
            df.to_parquet(buffer, engine='pyarrow', index=False)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            log.error(f"Failed to convert DataFrame to parquet bytes: {e}")
            return b""

    def _ensure_string_list(self, value: Any) -> list[str]:
        """Ensure a value is a list of strings, filtering out invalid items."""
        if not isinstance(value, list):
            return []
        
        result = []
        for item in value:
            # Skip None values
            if item is None:
                continue
            # Skip NaN values (both float NaN and string 'nan')
            if isinstance(item, float) and (pd.isna(item) or item != item):  # NaN check
                continue
            if isinstance(item, str) and item.lower() in ['nan', 'none', '']:
                continue
            # Convert to string and add
            result.append(str(item))
        
        return result

    async def get(self, key: str, as_bytes: bool | None = None, encoding: str | None = None, **kwargs) -> Any:
        """Retrieve data from PostgreSQL table."""
        table_name = self._get_table_name(key)
        try:
            log.info(f"Retrieving data from table: {table_name}")
            
            conn = await self._get_connection()
            try:
                # Check if table exists
                table_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table_name
                )
                
                if not table_exists:
                    log.warning(f"Table {table_name} does not exist")
                    return None

                # Get all records
                rows = await conn.fetch(f"SELECT * FROM {table_name} ORDER BY created_at")
                
                if not rows:
                    log.info(f"No data found in table {table_name}")
                    return None

                log.info(f"Retrieved {len(rows)} records from table {table_name}")

                # Handle non-parquet data (JSON/state files)
                if (not key.endswith('.parquet') or 
                    'state' in key.lower() or 
                    'context' in table_name.lower()):
                    # For non-tabular data, return the raw content from the first record
                    if rows and 'data' in rows[0]:
                        raw_content = rows[0]['data']
                        if isinstance(raw_content, dict):
                            json_str = json.dumps(raw_content)
                            return json_str.encode(encoding or self._encoding) if as_bytes else json_str
                    return b"" if as_bytes else ""

                # Convert to DataFrame
                records = []
                for row in rows:
                    record_data = dict(row['data']) if isinstance(row['data'], dict) else json.loads(row['data'])
                    
                    # Clean up the record data with better type consistency
                    cleaned_data = {}
                    for field_name, value in record_data.items():
                        if field_name in ['text_unit_ids', 'children', 'entity_ids', 'relationship_ids', 'document_ids']:
                            # These should always be lists of strings
                            parsed_list = self._parse_jsonb_field(value, "list")
                            # Use the robust string list converter
                            cleaned_data[field_name] = self._ensure_string_list(parsed_list)
                        elif field_name == 'metadata':
                            # Metadata should be a dict
                            cleaned_data[field_name] = self._parse_jsonb_field(value, "dict")
                        elif self._is_scalar_na(value) or value is None:
                            cleaned_data[field_name] = None
                        elif isinstance(value, float) and pd.isna(value):
                            cleaned_data[field_name] = None
                        else:
                            cleaned_data[field_name] = value
                    
                    records.append(cleaned_data)

                df = pd.DataFrame(records)
                
                # Additional cleanup - ensure list columns are properly typed using the robust method
                for col in ['text_unit_ids', 'children', 'entity_ids', 'relationship_ids', 'document_ids']:
                    if col in df.columns:
                        df[col] = df[col].apply(self._ensure_string_list)
                
                # Clean up NaN values
                df = df.where(pd.notna(df), None)

                log.info(f"Get table {table_name} DataFrame with shape: {df.shape}")
                log.info(f"Get table {table_name} DataFrame columns: {df.columns.tolist()}")

                # Convert to bytes if requested
                if as_bytes or kwargs.get("as_bytes"):
                    return self._convert_dataframe_to_parquet_bytes(df)
                
                return df
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error retrieving data from table {table_name}: %s", e)
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Insert data into PostgreSQL table with upsert capability."""
        try:
            table_name = self._get_table_name(key)
            log.info(f"Setting data for key: {key}, table: {table_name}")
            
            await self._ensure_table_exists(table_name)
            
            conn = await self._get_connection()
            try:
                if isinstance(value, bytes):
                    # Parse parquet data
                    df = pd.read_parquet(BytesIO(value))
                    log.info(f"Parsed parquet data on set method, DataFrame shape: {df.shape}")
                    log.info(f"Parsed DataFrame head: {df.head()}")
                    
                    # Prepare data for PostgreSQL
                    records = self._prepare_data_for_postgres(df, table_name)
                    
                    if records:
                        # Use batch insert for much better performance
                        await self._batch_upsert_records(conn, table_name, records)
                        
                        log.info(f"Successfully upserted {len(records)} records to {table_name}")
                        
                else:
                    # Handle non-parquet data (e.g., JSON, stats)
                    log.info(f"Handling non-parquet data for key: {key}")
                    
                    record_data = json.loads(value) if isinstance(value, str) else value
                    record = {
                        'id': key,
                        'data': record_data
                    }
                    
                    upsert_sql = f"""
                    INSERT INTO {table_name} (id, data, updated_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        data = EXCLUDED.data,
                        updated_at = NOW()
                    """
                    
                    await conn.execute(
                        upsert_sql,
                        record['id'],
                        json.dumps(record['data'])
                    )
                    
                    log.info("Non-parquet data upsert successful")
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception("Error setting data for key %s: %s", key, e)

    async def has(self, key: str) -> bool:
        """Check if data exists for the given key."""
        try:
            table_name = self._get_table_name(key)
            log.info(f"Checking existence for key: {key}, table: {table_name}")
            conn = await self._get_connection()
            try:
                # Check if table exists
                table_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table_name
                )
                log.info(f"Table {table_name} exists: {table_exists}")
                return table_exists
            finally:
                await self._release_connection(conn)
        except Exception as e:
            log.exception("Error checking existence for key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> None:
        """Delete data for the given key."""
        try:
            table_name = self._get_table_name(key)
            conn = await self._get_connection()
            try:
                result = await conn.execute(
                   f"TRUNCATE TABLE {table_name}"
                )
                log.info(f"Deleted record for key {key}: {result}")
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception("Error deleting key %s: %s", key, e)

    async def clear(self) -> None:
        """Clear all tables with the configured prefix."""
        try:
            conn = await self._get_connection()
            try:
                # Get all tables with our prefix
                tables = await conn.fetch(
                    "SELECT table_name FROM information_schema.tables WHERE table_name LIKE $1",
                    f"{self._collection_prefix}%"
                )
                
                for table_row in tables:
                    table_name = table_row['table_name']
                    await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    log.info(f"Dropped table: {table_name}")
                
                log.info(f"Cleared all tables with prefix: {self._collection_prefix}")
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception("Error clearing tables: %s", e)

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        # This would need to be async to properly implement
        # For now, return empty list
        log.warning("keys() method not fully implemented for async storage")
        return []

    def child(self, name: str | None) -> PipelineStorage:
        """Create a child storage instance."""
        return self


    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for data."""
        try:
            table_name = self._get_table_name(key)
            conn = await self._get_connection()
            try:
                if key.endswith('.parquet'):
                    prefix = self._get_prefix(key)
                    created_at = await conn.fetchval(
                        f"SELECT MIN(created_at) FROM {table_name} WHERE id LIKE $1",
                        f"{prefix}:%"
                    )
                else:
                    created_at = await conn.fetchval(
                        f"SELECT created_at FROM {table_name} WHERE id = $1",
                        key
                    )
                
                if created_at:
                    return get_timestamp_formatted_with_local_tz(created_at)
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception("Error getting creation date for %s: %s", key, e)
        
        return ""

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            log.info("Closed PostgreSQL connection pool")
