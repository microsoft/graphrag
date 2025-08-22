# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""PostgreSQL Storage implementation of PipelineStorage"""

import json
import logging
import re
from collections.abc import Iterator
from io import BytesIO
from typing import Any

import pandas as pd
import asyncpg
from asyncpg import Connection

from graphrag.storage.pipeline_storage import (
    PipelineStorage,
    get_timestamp_formatted_with_local_tz,
)

log = logging.getLogger(__name__)

class PostgresPipelineStorage(PipelineStorage):
    """Simplified PostgreSQL Storage Implementation."""

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
        command_timeout: int = 600,
        connection_timeout: int = 60,
        batch_size: int = 50,
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
        self._connection_timeout = connection_timeout
        self._batch_size = batch_size
        self._pool = None

        if connection_string:
            self._connection_string = connection_string
        else:
            if password:
                self._connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            else:
                self._connection_string = f"postgresql://{username}@{host}:{port}/{database}"

        log.info(
            "Initializing PostgreSQL storage with host: %s:%s, database: %s, collection_prefix: %s",
            self._host, self._port, self._database, self._collection_prefix
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
                    server_settings={'application_name': 'graphrag_postgres_storage'},
                    timeout=self._connection_timeout
                )
                log.info("Created PostgreSQL connection pool")
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
        base_name = key.split(".")[0]
        return f"{self._collection_prefix}{base_name}"

    def _get_universal_table_schema(self, table_name: str) -> str:
        """Universal schema that works for all GraphRAG data types."""
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            human_readable_id BIGINT,
            data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_{table_name}_data_gin ON {table_name} USING GIN(data);
        CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);
        """

    async def _ensure_table_exists(self, table_name: str) -> None:
        """Ensure table exists with universal schema."""
        conn = await self._get_connection()
        try:
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name
            )
            if not table_exists:
                schema_sql = self._get_universal_table_schema(table_name)
                await conn.execute(schema_sql)
                log.info(f"Created table {table_name}")
        finally:
            await self._release_connection(conn)

    def _prepare_dataframe_for_storage(self, df: pd.DataFrame) -> list[dict]:
        """Convert DataFrame to records for storage."""
        records = []
        
        for i, row in df.iterrows():
            record_data = row.to_dict()
            
            # Convert pandas/numpy types to JSON-serializable types
            for key, value in record_data.items():
                if pd.isna(value):
                    record_data[key] = None
                elif isinstance(value, (list, dict)):
                    record_data[key] = value
                elif hasattr(value, 'tolist'):
                    record_data[key] = value.tolist()
                elif hasattr(value, 'item') and hasattr(value, 'size') and value.size == 1:
                    record_data[key] = value.item()
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    record_data[key] = value.isoformat() if pd.notna(value) else None
                else:
                    record_data[key] = value

            # Extract ID and human_readable_id
            record_id = record_data.pop('id', f"record_{i}")
            human_readable_id = record_data.pop('human_readable_id', i)
            
            records.append({
                'id': str(record_id),
                'human_readable_id': int(human_readable_id) if pd.notna(human_readable_id) else i,
                'data': record_data
            })
        
        return records

    async def _batch_upsert(self, conn: Connection, table_name: str, records: list[dict]) -> None:
        """Perform batch upsert of records."""
        total_records = len(records)
        log.info(f"Starting batch upsert of {total_records} records to {table_name}")
        
        upsert_sql = f"""
            INSERT INTO {table_name} (id, human_readable_id, data, updated_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (id) 
            DO UPDATE SET 
                human_readable_id = EXCLUDED.human_readable_id,
                data = EXCLUDED.data,
                updated_at = NOW()
        """
        
        # Process in batches
        for i in range(0, total_records, self._batch_size):
            batch = records[i:i + self._batch_size]
            batch_data = [
                (record['id'], record['human_readable_id'], json.dumps(record['data']))
                for record in batch
            ]
            
            try:
                async with conn.transaction():
                    await conn.executemany(upsert_sql, batch_data)
                
                log.info(f"Batch upsert progress: {min(i + self._batch_size, total_records)}/{total_records}")
                
            except Exception as e:
                log.error(f"Batch upsert failed for batch {i}-{min(i + self._batch_size, total_records)}: {e}")
                # Fallback to individual inserts
                async with conn.transaction():
                    for record in batch:
                        await conn.execute(upsert_sql, record['id'], record['human_readable_id'], json.dumps(record['data']))

    def _parse_jsonb_field(self, value: Any, default_type: str = "list") -> Any:
        """Parse JSONB field back to Python object."""
        if value is None:
            return {} if default_type == "dict" else []
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {} if default_type == "dict" else []
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

    async def get(self, key: str, as_bytes: bool | None = None, encoding: str | None = None, **kwargs) -> Any:
        """Retrieve data from PostgreSQL table."""
        try:
            table_name = self._get_table_name(key)
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
                rows = await conn.fetch(
                    f"SELECT id, human_readable_id, data FROM {table_name} ORDER BY created_at"
                )
                
                if not rows:
                    log.info(f"No data found in table {table_name}")
                    return None

                log.info(f"Retrieved {len(rows)} records from table {table_name}")

                # Handle non-parquet data (JSON/state files)
                if not key.endswith('.parquet') or 'state' in key.lower() or 'context' in key.lower():
                    if rows:
                        first_record_data = rows[0]['data']
                        if isinstance(first_record_data, dict):
                            json_str = json.dumps(first_record_data)
                        else:
                            json_str = json.dumps(first_record_data)
                        return json_str.encode(encoding or self._encoding) if as_bytes else json_str
                    return b"" if as_bytes else ""

                # Convert to DataFrame
                records = []
                for row in rows:
                    record_data = dict(row['data']) if isinstance(row['data'], dict) else json.loads(row['data'])
                    
                    # Add back the ID and human_readable_id
                    record_data['id'] = row['id']
                    record_data['human_readable_id'] = row['human_readable_id']
                    
                    # Parse JSONB list fields back to proper Python lists
                    for field in ['text_unit_ids', 'children', 'entity_ids', 'relationship_ids', 'document_ids']:
                        if field in record_data:
                            record_data[field] = self._parse_jsonb_field(record_data[field], "list")
                    
                    # Parse metadata as dict
                    if 'metadata' in record_data:
                        record_data['metadata'] = self._parse_jsonb_field(record_data['metadata'], "dict")
                    
                    records.append(record_data)

                df = pd.DataFrame(records)
                
                # Clean up NaN values
                df = df.where(pd.notna(df), None)
                
                log.info(f"Created DataFrame with shape: {df.shape}")
                log.info(f"DataFrame columns: {df.columns.tolist()}")

                # Convert to bytes if requested
                if as_bytes or kwargs.get("as_bytes"):
                    return self._convert_dataframe_to_parquet_bytes(df)
                
                return df
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error retrieving data from table {table_name}: {e}")
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Store data in PostgreSQL table."""
        try:
            table_name = self._get_table_name(key)
            log.info(f"Setting data for key: {key}, table: {table_name}")
            
            await self._ensure_table_exists(table_name)
            
            conn = await self._get_connection()
            try:
                if isinstance(value, bytes):
                    # Handle parquet data
                    df = pd.read_parquet(BytesIO(value))
                    log.info(f"Parsed parquet data, DataFrame shape: {df.shape}")
                    
                    records = self._prepare_dataframe_for_storage(df)
                    if records:
                        await self._batch_upsert(conn, table_name, records)
                        log.info(f"Successfully stored {len(records)} records to {table_name}")
                else:
                    # Handle non-parquet data (JSON, etc.)
                    record_data = json.loads(value) if isinstance(value, str) else value
                    record = {
                        'id': key,
                        'human_readable_id': 0,
                        'data': record_data
                    }
                    
                    await conn.execute(
                        f"""INSERT INTO {table_name} (id, human_readable_id, data, updated_at) 
                           VALUES ($1, $2, $3, NOW()) 
                           ON CONFLICT (id) DO UPDATE SET 
                               data = EXCLUDED.data, updated_at = NOW()""",
                        record['id'], record['human_readable_id'], json.dumps(record['data'])
                    )
                    log.info(f"Successfully stored non-parquet data for key: {key}")
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error setting data for key {key}: {e}")
            raise

    async def has(self, key: str) -> bool:
        """Check if data exists for the given key."""
        try:
            table_name = self._get_table_name(key)
            conn = await self._get_connection()
            try:
                table_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table_name
                )
                if not table_exists:
                    return False
                
                if key.endswith('.parquet'):
                    # For parquet files, check if table has records
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    return count > 0
                else:
                    # For specific keys, check exact match
                    exists = await conn.fetchval(
                        f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE id = $1)", key
                    )
                    return exists
                    
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error checking existence for key {key}: {e}")
            return False

    async def delete(self, key: str) -> None:
        """Delete data for the given key."""
        try:
            table_name = self._get_table_name(key)
            conn = await self._get_connection()
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                log.info(f"Deleted table for key {key}")
            finally:
                await self._release_connection(conn)
        except Exception as e:
            log.exception(f"Error deleting key {key}: {e}")

    async def clear(self) -> None:
        """Clear all tables with the configured prefix."""
        try:
            conn = await self._get_connection()
            try:
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
            log.exception(f"Error clearing tables: {e}")

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        log.warning("keys() method not fully implemented for async storage")
        return []

    def child(self, name: str | None) -> PipelineStorage:
        """Create a child storage instance."""
        return self

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find data in PostgreSQL tables using a file pattern regex."""
        log.info("Searching PostgreSQL tables for pattern %s", file_pattern.pattern)
        return iter([])

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for data."""
        try:
            table_name = self._get_table_name(key)
            conn = await self._get_connection()
            try:
                if key.endswith('.parquet'):
                    created_at = await conn.fetchval(
                        f"SELECT MIN(created_at) FROM {table_name}"
                    )
                else:
                    created_at = await conn.fetchval(
                        f"SELECT created_at FROM {table_name} WHERE id = $1", key
                    )
                
                if created_at:
                    return get_timestamp_formatted_with_local_tz(created_at)
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error getting creation date for {key}: {e}")
        
        return ""

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            log.info("Closed PostgreSQL connection pool")