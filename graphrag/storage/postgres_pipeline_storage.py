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

from graphrag.logger.progress import Progress
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

    # def _process_id_field(self, df: pd.DataFrame, table_name: str) -> list[str]:
    #     """Process ID values - store clean IDs with prefix following CosmosDB pattern."""
    #     prefix = self._get_prefix(table_name.replace(self._collection_prefix, ""))
    #     id_values = []
        
    #     if "id" not in df.columns:
    #         # No ID column - create prefixed sequential IDs and track this prefix
    #         for index in range(len(df)):
    #             id_values.append(f"{prefix}:{index}")
    #         if prefix not in self._no_id_prefixes:
    #             self._no_id_prefixes.append(prefix)
    #         log.info(f"No ID column found for {prefix}, generated prefixed sequential IDs")
    #     else:
    #         # Has ID column - process each row with prefix
    #         for index, val in enumerate(df["id"]):
    #             if self._is_scalar_na(val) or val == '' or val == 'nan' or (isinstance(val, list) and (len(val) == 0 or self._is_scalar_na(val[0]) or str(val[0]).strip() == '')):
    #                 # Missing ID - create prefixed sequential ID and track this prefix
    #                 id_values.append(f"{prefix}:{index}")
    #                 if prefix not in self._no_id_prefixes:
    #                     self._no_id_prefixes.append(prefix)
    #             else:
    #                 # Valid ID - use with prefix (following CosmosDB pattern)
    #                 if isinstance(val, list):
    #                     id_values.append(f"{prefix}:{val[0]}")
    #                 else:
    #                     id_values.append(f"{prefix}:{val}")
        
    #     return id_values

    def _is_scalar_na(self, value: Any) -> bool:
        """Safely check if a value is NA/null, avoiding issues with arrays."""
        try:
            # Don't check pd.isna on complex objects or large arrays
            if isinstance(value, (list, dict)):
                return False
            if hasattr(value, '__len__') and len(str(value)) > 100:
                return False
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
        
        # Process IDs with prefix
        ids = df['id'].astype(str).tolist() if 'id' in df.columns else [f"{self._get_prefix(table_name.replace(self._collection_prefix, ''))}:{i}" for i in range(len(df))]
        
        records = []
        for i in range(len(df)):
            # Create record with ID and all data in JSONB field
            record_data = df.iloc[i].to_dict()
            
            # Convert numpy types to native Python types for JSON serialization
            for key, value in record_data.items():
                # Handle different value types carefully
                if isinstance(value, (list, dict)):
                    # Keep lists and dicts as-is (like text_unit_ids)
                    record_data[key] = value
                elif hasattr(value, 'item') and hasattr(value, 'size') and value.size == 1:
                    # Only use .item() for numpy scalars (arrays of size 1)
                    record_data[key] = value.item()
                elif hasattr(value, 'tolist'):
                    # Convert numpy arrays to Python lists
                    record_data[key] = value.tolist()
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    record_data[key] = value.isoformat() if pd.notna(value) else None
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

    async def _batch_upsert_records(self, conn: Connection, table_name: str, records: list[dict], batch_size: int = 1000) -> None:
        """Perform high-performance batch upsert of records using executemany."""
        total_records = len(records)
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
            if i % batch_size == 0 or batch_end == total_records:
                log.info(f"Batch upsert progress: {processed_count}/{total_records} records ({processed_count/total_records*100:.1f}%)")

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find data in PostgreSQL tables using a file pattern regex."""
        # This is a synchronous method, but we need async operations
        # For now, implement a basic version - in practice, this would need refactoring
        log.info("Searching PostgreSQL tables for pattern %s", file_pattern.pattern)
        
        # Note: This is simplified - full implementation would need async/await support
        # in the find method signature or use asyncio.run()
        return iter([])
    
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

                log.info(f"Get table {table_name} DataFrame with shape: {df.shape}")
                log.info(f"Get table {table_name} DataFrame columns: {df.columns.tolist()}")

                # Convert to bytes if requested
                if as_bytes or kwargs.get("as_bytes"):
                    return self._convert_dataframe_to_parquet_bytes(df)
                
                return df
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error retrieving data from table {table_name}: {e}")
            return None
    async def get1(self, key: str, as_bytes: bool | None = None, encoding: str | None = None, **kwargs) -> Any:
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

                # Query all records for this prefix
                rows = await conn.fetch(f"SELECT * FROM {table_name} ORDER BY created_at")
                
                if not rows:
                    log.info(f"No data found in table {table_name}")
                    return None

                log.info(f"Retrieved {len(rows)} records from table {table_name}")

                # Check if this should be treated as raw data instead of tabular data
                if (not key.endswith('.parquet') or 
                    'state' in key.lower() or 
                    key.endswith('.json') or 
                    key.endswith('.txt') or 
                    key.endswith('.yaml') or
                    key.endswith('.yml') or
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
                    # Handle JSONB data properly - row['data'] should already be a dict from asyncpg
                    if isinstance(row['data'], dict):
                        record_data = dict(row['data'])
                    else:
                        # If it's a string, parse it as JSON
                        record_data = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
                    
                    # Clean up the record data - convert None to proper values and handle NaN
                    cleaned_data = {}
                    for key, value in record_data.items():
                        if self._is_scalar_na(value) or value is None:
                            cleaned_data[key] = None
                        elif isinstance(value, str) and key == 'text_unit_ids':
                            # Try to parse text_unit_ids back from JSON string if needed
                            try:
                                parsed_value = json.loads(value)
                                cleaned_data[key] = parsed_value if isinstance(parsed_value, list) else [value]
                            except (json.JSONDecodeError, TypeError):
                                # If it's not JSON, treat as a single item list or keep as string
                                cleaned_data[key] = [value] if value else []
                        elif key in ['children', 'entity_ids', 'relationship_ids', 'text_unit_ids']:
                            # Always ensure these columns are lists
                            if isinstance(value, list):
                                cleaned_data[key] = value
                            elif isinstance(value, str):
                                try:
                                    parsed_value = json.loads(value)
                                    cleaned_data[key] = parsed_value if isinstance(parsed_value, list) else []
                                except (json.JSONDecodeError, TypeError):
                                    cleaned_data[key] = []
                            elif value is None:
                                cleaned_data[key] = []
                            else:
                                # fallback: wrap single value in a list
                                cleaned_data[key] = [value]
                        elif isinstance(value, (list, np.ndarray)) and len(value) == 0:
                            # Handle empty arrays/lists
                            cleaned_data[key] = []
                        else:
                            cleaned_data[key] = value
                    
                    # # Always include the ID column for GraphRAG compatibility
                    # # Extract the actual ID from the prefixed storage ID
                    # storage_id = row['id']
                    # # if ':' in storage_id:
                    # #     actual_id = storage_id.split(':', 1)[1]
                    # #     # Only use the actual ID if it's not a sequential index
                    # #     if not actual_id.isdigit() or prefix not in self._no_id_prefixes:
                    # #         cleaned_data['id'] = actual_id
                    # #     else:
                    # #         # For auto-generated sequential IDs, use the storage ID as the ID
                    # #         cleaned_data['id'] = storage_id
                    # # else:
                    # #     # If no prefix found, use the storage ID as is
                    # cleaned_data['id'] = storage_id
                    records.append(cleaned_data)

                df = pd.DataFrame(records)
                
                # Additional cleanup for NaN values in the DataFrame
                df = df.where(pd.notna(df), None)
                log.info(f"Get DataFrame with shape: {df.shape}")
                log.info(f"DataFrame columns: {df.columns.tolist()}")

                # if len(df) > 0:
                #     log.info(f"Sample record: {df.iloc[0].to_dict()}")
                #     # Debug: Check if children column exists and its type
                #     if 'children' in df.columns:
                #         sample_children = df.iloc[0]['children']
                #         log.info(f"Sample children value: {sample_children}, type: {type(sample_children)}")

                # Handle bytes conversion for GraphRAG compatibility
                if as_bytes or kwargs.get("as_bytes"):
                    log.info(f"Converting DataFrame to parquet bytes for key: {key}")
                    
                    # Apply column filtering similar to Milvus implementation
                    df_clean = df.copy()
                    
                    # Define expected columns for each data type
                    if 'documents' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'title', 'text', 'creation_date', 'metadata']
                        # Include text_unit_ids if it has meaningful data
                        if 'text_unit_ids' in df_clean.columns and any(
                            len(tuid) > 0 for tuid in df_clean['text_unit_ids'] if isinstance(tuid, list)
                        ):
                            expected_columns.insert(4, 'text_unit_ids')
                            log.info("Including text_unit_ids (appears to be final documents)")
                    elif 'entities' in table_name:
                        # Exclude degree column for GraphRAG compatibility
                        expected_columns = ['id', 'human_readable_id', 'title', 'type', 'description', 'text_unit_ids', 'frequency']
                        log.info("Excluding degree column from entities for finalize_entities compatibility")
                    elif 'relationships' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'source', 'target', 'description', 'weight', 'text_unit_ids']
                        if 'combined_degree' in df_clean.columns:
                            expected_columns.append('combined_degree')
                    elif 'text_units' in table_name:
                        expected_columns = ['id', 'text', 'n_tokens', 'document_ids', 'entity_ids', 'relationship_ids']
                    elif 'communities' in table_name:
                        expected_columns = ['id', 'community', 'level', 'parent', 'children', 'text_unit_ids', 'entity_ids', 'relationship_ids']
                    else:
                        expected_columns = list(df_clean.columns)
                    
                    # Filter columns
                    available_columns = [col for col in expected_columns if col in df_clean.columns]
                    if available_columns != expected_columns:
                        missing = set(expected_columns) - set(available_columns)
                        extra = set(df_clean.columns) - set(expected_columns)
                        log.warning(f"Column mismatch - Expected: {expected_columns}, Available: {available_columns}, Missing: {missing}, Extra: {extra}")
                    
                    df_clean = df_clean[available_columns]
                    log.info(f"Final filtered columns: {df_clean.columns.tolist()}")

                    # Convert to parquet bytes
                    try:
                        # Handle list columns that PyArrow can't serialize directly
                        df_for_parquet = df_clean.copy()
                        
                        # Convert list columns to JSON strings for parquet compatibility
                        list_columns = []
                        for col in df_for_parquet.columns:
                            if col in df_for_parquet.columns and len(df_for_parquet) > 0:
                                # Check if this column contains lists
                                first_non_null = None
                                for val in df_for_parquet[col]:
                                    if isinstance(val, list):
                                        first_non_null = val
                                        break
                                    elif val is not None and not isinstance(val, (list, np.ndarray)) and pd.notna(val):
                                        first_non_null = val
                                        break
                                if isinstance(first_non_null, list):
                                    list_columns.append(col)
                                    # Convert lists to JSON strings
                                    df_for_parquet[col] = df_for_parquet[col].apply(
                                        lambda x: json.dumps(x) if isinstance(x, list) else (json.dumps([]) if x is None else str(x))
                                    )
                                elif col in ['children', 'entity_ids', 'relationship_ids', 'text_unit_ids']:
                                    # These columns should always be lists, even if empty
                                    list_columns.append(col)
                                    df_for_parquet[col] = df_for_parquet[col].apply(
                                        lambda x: json.dumps(x) if isinstance(x, list) else (json.dumps([]) if x is None else str(x))
                                    )
                        
                        if list_columns:
                            log.info(f"Converted list columns to JSON strings for parquet: {list_columns}")
                        
                        buffer = BytesIO()
                        df_for_parquet.to_parquet(buffer, engine='pyarrow')
                        buffer.seek(0)
                        parquet_bytes = buffer.getvalue()
                        log.info(f"Successfully converted DataFrame to {len(parquet_bytes)} bytes of parquet data")
                        return parquet_bytes
                    except Exception as e:
                        log.exception(f"Failed to convert DataFrame to parquet bytes: {e}")
                        return b""
                
                return df
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error retrieving data from table {table_name}: {e}")
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
                    log.info(f"Parsed parquet data, DataFrame shape: {df.shape}")
                    log.info(f"Parsed DataFrame head: {df.head()}")
                    
                    # Prepare data for PostgreSQL
                    records = self._prepare_data_for_postgres(df, table_name)
                    
                    if records:
                        # Use batch insert for much better performance
                        await self._batch_upsert_records(conn, table_name, records)
                        
                        log.info(f"Successfully upserted {len(records)} records to {table_name}")
                        
                        # # Log duplicate handling info
                        # if any(record['id'].split(':')[0] in self._no_id_prefixes for record in records):
                        #     log.info("Some records used auto-generated IDs")
                        
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
            log.exception("Error setting data in PostgreSQL table %s: %s", table_name, e)

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
                log.debug(f"Table {table_name} exists: {table_exists}")
                if not table_exists:
                    return False
                
                if key.endswith('.parquet'):
                    # For parquet files, check if table has any records
                    total_count = await conn.fetchval(
                        f"SELECT COUNT(*) FROM {table_name}"
                    )
                    if total_count > 0:
                        return True
                    else:
                        raise ValueError(f"No records found in table {table_name} for parquet key {key}")
                else:
                    # Check for exact key match
                    exists = await conn.fetchval(
                        f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE id = $1)",
                        key
                    )
                    return exists
                    
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
                if key.endswith('.parquet'):
                    # Delete all records with this prefix
                    prefix = self._get_prefix(key)
                    result = await conn.execute(
                        f"DELETE FROM {table_name} WHERE id LIKE $1",
                        f"{prefix}:%"
                    )
                    log.info(f"Deleted records for prefix {prefix}: {result}")
                else:
                    # Delete exact key match
                    result = await conn.execute(
                        f"DELETE FROM {table_name} WHERE id = $1",
                        key
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
        if name is None:
            return self
        
        # Create child with modified table prefix
        child_prefix = f"{self._collection_prefix}{name}_"
        return PostgresPipelineStorage(
            host=self._host,
            port=self._port,
            database=self._database,
            username=self._username,
            password=self._password,
            collection_prefix=child_prefix,
            encoding=self._encoding,
        )

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
