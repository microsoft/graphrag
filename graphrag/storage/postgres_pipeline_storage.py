# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""PostgreSQL Storage implementation of PipelineStorage."""

import json
import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone
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
    _no_id_prefixes: list[str]

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
        self._no_id_prefixes = []
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

    def _sanitize_table_name(self, name: str) -> str:
        """Sanitize a name to be a valid PostgreSQL table name."""
        return name
        import re
        
        # Replace common problematic characters
        sanitized = name.replace("-", "_").replace(":", "_").replace(" ", "_")
        
        # Remove any characters that aren't alphanumeric, underscore, or dollar sign
        sanitized = re.sub(r'[^a-zA-Z0-9_$]', '_', sanitized)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it starts with a letter or underscore (not a digit)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"tbl_{sanitized}"
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "tbl_unnamed"
        
        # PostgreSQL has a limit of 63 characters for identifiers
        if len(sanitized) > 59:  # Leave room for prefix
            sanitized = sanitized[:59]
        log.info(f"Sanitied name {name} to {sanitized}")
        return sanitized

    def _get_table_name(self, key: str) -> str:
        """Get the table name for a given key."""
        # Extract the base name without file extension
        base_name = key.split(".")[0]
        
        # Sanitize for PostgreSQL compatibility
        sanitized_name = self._sanitize_table_name(base_name)
        
        return f"{self._collection_prefix}{sanitized_name}"

    def _get_prefix(self, key: str) -> str:
        """Get the prefix of the filename key."""
        return key.split(".")[0]

    def _get_entities_table_schema(self, table_name: str) -> str:
        """Get the SQL schema for entities table."""
        # Sanitize table name for index names
        table_name = self._sanitize_table_name(table_name)
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            human_readable_id BIGINT,
            title TEXT,
            type TEXT,
            description TEXT,
            text_unit_ids JSONB DEFAULT '[]'::jsonb,
            frequency INTEGER DEFAULT 0,
            degree INTEGER DEFAULT 0,
            x DOUBLE PRECISION DEFAULT 0.0,
            y DOUBLE PRECISION DEFAULT 0.0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Performance indexes
        CREATE INDEX idx_{table_name}_type ON {table_name}(type);
        CREATE INDEX idx_{table_name}_frequency ON {table_name}(frequency);
        CREATE INDEX idx_{table_name}_title ON {table_name}(title);
        CREATE INDEX idx_{table_name}_text_unit_ids_gin ON {table_name} USING GIN(text_unit_ids);
        """

    def _get_relationships_table_schema(self, table_name: str) -> str:
        """Get the SQL schema for relationships table."""
        # Sanitize table name for index names
        table_name = self._sanitize_table_name(table_name)
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            human_readable_id BIGINT,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            description TEXT DEFAULT '',
            weight DOUBLE PRECISION DEFAULT 0.0,
            combined_degree INTEGER DEFAULT 0,
            text_unit_ids JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Graph query indexes
        CREATE INDEX idx_{table_name}_source ON {table_name}(source);
        CREATE INDEX idx_{table_name}_target ON {table_name}(target);
        CREATE INDEX idx_{table_name}_weight ON {table_name}(weight);
        CREATE INDEX idx_{table_name}_source_target ON {table_name}(source, target);
        CREATE INDEX idx_{table_name}_text_unit_ids_gin ON {table_name} USING GIN(text_unit_ids);
        """

    def _get_communities_table_schema(self, table_name: str) -> str:
        """Get the SQL schema for communities table."""
        # Sanitize table name for index names
        table_name = self._sanitize_table_name(table_name)
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            human_readable_id BIGINT,
            community INTEGER,
            level INTEGER DEFAULT 0,
            parent INTEGER,
            children JSONB DEFAULT '[]'::jsonb,
            text_unit_ids JSONB DEFAULT '[]'::jsonb,
            entity_ids JSONB DEFAULT '[]'::jsonb,
            relationship_ids JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Community hierarchy indexes
        CREATE INDEX idx_{table_name}_community ON {table_name}(community);
        CREATE INDEX idx_{table_name}_level ON {table_name}(level);
        CREATE INDEX idx_{table_name}_parent ON {table_name}(parent);
        CREATE INDEX idx_{table_name}_text_unit_ids_gin ON {table_name} USING GIN(text_unit_ids);
        CREATE INDEX idx_{table_name}_entity_ids_gin ON {table_name} USING GIN(entity_ids);
        CREATE INDEX idx_{table_name}_relationship_ids_gin ON {table_name} USING GIN(relationship_ids);
        """

    def _get_text_units_table_schema(self, table_name: str) -> str:
        """Get the SQL schema for text_units table."""
        # Sanitize table name for index names
        table_name = self._sanitize_table_name(table_name)
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            human_readable_id BIGINT,
            text TEXT,
            n_tokens INTEGER DEFAULT 0,
            document_ids JSONB DEFAULT '[]'::jsonb,
            entity_ids JSONB DEFAULT '[]'::jsonb,
            relationship_ids JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Text search and relationship indexes
        CREATE INDEX idx_{table_name}_n_tokens ON {table_name}(n_tokens);
        CREATE INDEX idx_{table_name}_text_gin ON {table_name} USING GIN(to_tsvector('english', text));
        CREATE INDEX idx_{table_name}_document_ids_gin ON {table_name} USING GIN(document_ids);
        CREATE INDEX idx_{table_name}_entity_ids_gin ON {table_name} USING GIN(entity_ids);
        CREATE INDEX idx_{table_name}_relationship_ids_gin ON {table_name} USING GIN(relationship_ids);
        """

    def _get_documents_table_schema(self, table_name: str) -> str:
        """Get the SQL schema for documents table."""
        # Sanitize table name for index names
        table_name = self._sanitize_table_name(table_name)
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            human_readable_id BIGINT,
            title TEXT,
            text TEXT,
            text_unit_ids JSONB DEFAULT '[]'::jsonb,
            creation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Document search indexes
        CREATE INDEX idx_{table_name}_title ON {table_name}(title);
        CREATE INDEX idx_{table_name}_creation_date ON {table_name}(creation_date);
        CREATE INDEX idx_{table_name}_text_gin ON {table_name} USING GIN(to_tsvector('english', text));
        CREATE INDEX idx_{table_name}_text_unit_ids_gin ON {table_name} USING GIN(text_unit_ids);
        CREATE INDEX idx_{table_name}_metadata_gin ON {table_name} USING GIN(metadata);
        """

    def _get_generic_table_schema(self, table_name: str) -> str:
        """Get the SQL schema for generic data (fallback)."""
        # Sanitize table name for index names
        table_name = self._sanitize_table_name(table_name)
        return f"""
        CREATE TABLE {table_name} (
            id TEXT PRIMARY KEY,
            data JSONB NOT NULL,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Generic indexes
        CREATE INDEX idx_{table_name}_data_gin ON {table_name} USING GIN(data);
        CREATE INDEX idx_{table_name}_metadata_gin ON {table_name} USING GIN(metadata);
        """

    def _get_table_schema_sql(self, table_name: str) -> str:
        """Get the appropriate schema SQL for the table type."""
        # Sanitize table name for schema generation
        table_name = self._sanitize_table_name(table_name)
        
        if 'entities' in table_name:
            return self._get_entities_table_schema(table_name)
        elif 'relationships' in table_name:
            return self._get_relationships_table_schema(table_name)
        elif 'communities' in table_name:
            return self._get_communities_table_schema(table_name)
        elif 'text_units' in table_name:
            return self._get_text_units_table_schema(table_name)
        elif 'documents' in table_name:
            return self._get_documents_table_schema(table_name)
        else:
            return self._get_generic_table_schema(table_name)

    async def _ensure_table_exists_with_schema(self, table_name: str) -> None:
        # Ensure table name is properly sanitized for SQL operations
        table_name = self._sanitize_table_name(table_name)

        conn = await self._get_connection()
        try:
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name
            )
            if not table_exists:
                # Create table with appropriate typed schema (pass original table_name for type detection)
                schema_sql = self._get_table_schema_sql(table_name)
                await conn.execute(schema_sql)
                log.info(f"Created table {table_name} with specific schema")
            
        finally:
            await self._release_connection(conn)

    def _process_id_field(self, df: pd.DataFrame, table_name: str) -> list[str]:
        """Process ID values - store clean IDs with prefix following CosmosDB pattern in GraphRAG."""
        prefix = self._get_prefix(table_name.replace(self._collection_prefix, ""))
        id_values = []
        
        if "id" not in df.columns:
            # No ID column - create prefixed sequential IDs and track this prefix
            for index in range(len(df)):
                id_values.append(f"{prefix}:{index}")
            if prefix not in self._no_id_prefixes:
                self._no_id_prefixes.append(prefix)
            log.info(f"No ID column found for {prefix}, generated prefixed sequential IDs")
        else:
            # Has ID column - process each row with prefix
            for index, val in enumerate(df["id"]):
                if self._is_scalar_na(val) or val == '' or val == 'nan' or (isinstance(val, list) and (len(val) == 0 or self._is_scalar_na(val[0]) or str(val[0]).strip() == '')):
                    # Missing ID - create prefixed sequential ID and track this prefix
                    id_values.append(f"{prefix}:{index}")
                    if prefix not in self._no_id_prefixes:
                        self._no_id_prefixes.append(prefix)
                else:
                    # Valid ID - use as is without prefix
                    if isinstance(val, list):
                        id_values.append(str(val[0]))
                    else:
                        id_values.append(str(val))
        
        return id_values

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
        """Prepare DataFrame data for PostgreSQL insertion with typed columns."""
        log.info(f"Preparing data for table {table_name}, DataFrame shape: {df.shape}")
        log.info(f"DataFrame columns: {df.columns.tolist()}")
        
        # Add human_readable_id if missing
        if 'human_readable_id' not in df.columns:
            df = df.copy()
            df['human_readable_id'] = range(len(df))
            log.info(f"Generated sequential human_readable_id for {len(df)} records")
        
        # Process IDs - for typed tables, we can use simpler ID handling
        ids = self._process_id_field(df, table_name)
        
        # Determine if this is a typed table or generic table
        is_typed_table = any(table_type in table_name for table_type in 
                           ['entities', 'relationships', 'communities', 'text_units', 'documents'])
        
        if is_typed_table:
            return self._prepare_data_for_typed_table(df, table_name, ids)
        else:
            return self._prepare_data_for_generic_table(df, table_name, ids)

    def _prepare_data_for_typed_table(self, df: pd.DataFrame, table_name: str, ids: list[str]) -> list[dict]:
        """Prepare data for typed PostgreSQL tables with specific columns."""
        records = []
        
        for i in range(len(df)):
            record = {'id': ids[i]}
            row = df.iloc[i]
            
            # Map DataFrame columns to table columns based on table type
            if 'entities' in table_name:
                record.update({
                    'human_readable_id': int(row.get('human_readable_id', i)),
                    'title': str(row.get('title', '')),
                    'type': str(row.get('type', '')),
                    'description': str(row.get('description', '')),
                    'text_unit_ids': self._ensure_json_list(row.get('text_unit_ids', [])),
                    'frequency': int(row.get('frequency', 0)) if pd.notna(row.get('frequency', 0)) else 0,
                    'degree': int(row.get('degree', 0)) if pd.notna(row.get('degree', 0)) else 0,
                    'x': float(row.get('x', 0.0)) if pd.notna(row.get('x', 0.0)) else 0.0,
                    'y': float(row.get('y', 0.0)) if pd.notna(row.get('y', 0.0)) else 0.0
                })
            elif 'relationships' in table_name:
                record.update({
                    'human_readable_id': int(row.get('human_readable_id', i)),
                    'source': str(row.get('source', '')),
                    'target': str(row.get('target', '')),
                    'description': str(row.get('description', '')),
                    'weight': float(row.get('weight', 0.0)) if pd.notna(row.get('weight', 0.0)) else 0.0,
                    'combined_degree': int(row.get('combined_degree', 0)) if pd.notna(row.get('combined_degree', 0)) else 0,
                    'text_unit_ids': self._ensure_json_list(row.get('text_unit_ids', []))
                })
            elif 'communities' in table_name:
                record.update({
                    'human_readable_id': int(row.get('human_readable_id', i)),
                    'community': int(row.get('community', 0)) if pd.notna(row.get('community')) and str(row.get('community', '')).strip() != '' else 0,
                    'level': int(row.get('level', 0)) if pd.notna(row.get('level', 0)) else 0,
                    'parent': int(row.get('parent', 0)) if pd.notna(row.get('parent')) and str(row.get('parent', '')).strip() != '' else None,
                    'children': self._ensure_json_list(row.get('children', [])),
                    'text_unit_ids': self._ensure_json_list(row.get('text_unit_ids', [])),
                    'entity_ids': self._ensure_json_list(row.get('entity_ids', [])),
                    'relationship_ids': self._ensure_json_list(row.get('relationship_ids', []))
                })
            elif 'text_units' in table_name:
                record.update({
                    'human_readable_id': int(row.get('human_readable_id', i)),
                    'text': str(row.get('text', '')),
                    'n_tokens': int(row.get('n_tokens', 0)) if pd.notna(row.get('n_tokens', 0)) else 0,
                    'document_ids': self._ensure_json_list(row.get('document_ids', [])),
                    'entity_ids': self._ensure_json_list(row.get('entity_ids', [])),
                    'relationship_ids': self._ensure_json_list(row.get('relationship_ids', []))
                })
            elif 'documents' in table_name:
                record.update({
                    'human_readable_id': int(row.get('human_readable_id', i)),
                    'title': str(row.get('title', '')),
                    'text': str(row.get('text', '')),
                    'text_unit_ids': self._ensure_json_list(row.get('text_unit_ids', [])),
                    'creation_date': self._ensure_datetime(row.get('creation_date')),
                    'metadata': self._ensure_json_dict(row.get('metadata', {}))
                })
            
            records.append(record)
        
        log.info(f"Prepared {len(records)} records for typed table {table_name}")
        if records:
            log.info(f"Sample typed record: {list(records[0].keys())}")
        
        return records

    def _prepare_data_for_generic_table(self, df: pd.DataFrame, table_name: str, ids: list[str]) -> list[dict]:
        """Prepare data for generic PostgreSQL tables (fallback to JSONB storage)."""
        records = []
        for i in range(len(df)):
            # Create record with ID and all data in JSONB field
            record_data = df.iloc[i].to_dict()
            
            # Convert numpy types to native Python types for JSON serialization
            for key, value in record_data.items():
                if isinstance(value, (list, dict)):
                    record_data[key] = value
                elif hasattr(value, 'tolist'):
                    # Handle numpy arrays and other numpy types
                    record_data[key] = value.tolist()
                elif hasattr(value, 'item') and hasattr(value, 'size') and value.size == 1:
                    record_data[key] = value.item()
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    record_data[key] = value.isoformat() if pd.notna(value) else None
                elif self._is_scalar_na(value):
                    record_data[key] = None
                elif isinstance(value, (list, np.ndarray)) and len(value) == 0:
                    record_data[key] = []
                else:
                    record_data[key] = value
            
            record = {
                'id': ids[i],
                'data': record_data,
                'metadata': {}
            }
            records.append(record)
        
        log.info(f"Prepared {len(records)} records for generic table {table_name}")
        return records

    def _ensure_json_list(self, value: Any) -> list:
        """Ensure a value is a proper list for JSONB storage."""
        if isinstance(value, list):
            # Convert any numpy arrays in the list to regular Python lists
            return [item.tolist() if hasattr(item, 'tolist') else item for item in value]
        elif hasattr(value, 'tolist'):
            # Handle numpy arrays directly
            converted = value.tolist()
            return converted if isinstance(converted, list) else [converted]
        elif isinstance(value, str) and value:
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        elif value is None or pd.isna(value):
            return []
        else:
            return [value] if value else []

    def _ensure_json_dict(self, value: Any) -> dict:
        """Ensure a value is a proper dict for JSONB storage."""
        if isinstance(value, dict):
            # Convert any numpy arrays in the dict to regular Python objects
            result = {}
            for k, v in value.items():
                if hasattr(v, 'tolist'):
                    result[k] = v.tolist()
                elif hasattr(v, 'item') and hasattr(v, 'size') and v.size == 1:
                    result[k] = v.item()
                else:
                    result[k] = v
            return result
        elif isinstance(value, str) and value:
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        elif value is None or pd.isna(value):
            return {}
        else:
            return {'value': str(value)} if value else {}

    def _ensure_timezone_aware_datetimes(self, records: list[dict]) -> list[dict]:
        """Ensure all datetime fields in records are timezone-aware for PostgreSQL."""
        datetime_fields = ['creation_date', 'created_at', 'updated_at']
        
        for record in records:
            for field in datetime_fields:
                if field in record:
                    value = record[field]
                    if value is not None:
                        record[field] = self._ensure_datetime(value)
        
        return records

    def _ensure_datetime(self, value: Any) -> datetime:
        """Ensure a value is a proper timezone-aware datetime object for PostgreSQL storage."""
        from dateutil import parser
        
        if isinstance(value, datetime):
            # If it's already a datetime, ensure it has timezone info
            if value.tzinfo is None:
                # If it's timezone-naive, localize to UTC
                return value.replace(tzinfo=timezone.utc)
            else:
                # Already timezone-aware
                return value
        elif isinstance(value, pd.Timestamp):
            # Convert pandas Timestamp to datetime
            dt = value.to_pydatetime()
            # Ensure timezone awareness
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            else:
                return dt
        elif isinstance(value, str) and value:
            try:
                # Try to parse the string as a datetime
                parsed_dt = parser.parse(value)
                # Ensure timezone awareness
                if parsed_dt.tzinfo is None:
                    return parsed_dt.replace(tzinfo=timezone.utc)
                else:
                    return parsed_dt
            except (ValueError, TypeError):
                # If parsing fails, return current time
                return datetime.now(timezone.utc)
        elif value is None or pd.isna(value):
            return datetime.now(timezone.utc)
        else:
            # For any other type, return current time
            return datetime.now(timezone.utc)

    async def _batch_upsert_records(self, conn: Connection, table_name: str, records: list[dict]) -> None:
        """Perform high-performance batch upsert of records using executemany."""
        total_records = len(records)
        log.info(f"Starting batch upsert of {total_records} records to {table_name} with batch size {self._batch_size}")
        
        # Ensure all datetime fields are timezone-aware
        records = self._ensure_timezone_aware_datetimes(records)
        
        processed_count = 0
        
        # Determine if this is a typed table or generic table
        is_typed_table = any(table_type in table_name for table_type in 
                           ['entities', 'relationships', 'communities', 'text_units', 'documents'])
        
        # Process records in batches for optimal performance
        for i in range(0, total_records, self._batch_size):
            batch = records[i:i + self._batch_size]
            batch_end = min(i + self._batch_size, total_records)

            try:
                if is_typed_table:
                    await self._batch_upsert_typed_records(conn, table_name, batch)
                else:
                    await self._batch_upsert_generic_records(conn, table_name, batch)
                    
            except Exception as e:
                log.warning(f"Batch method failed for batch {i}-{batch_end}, falling back to individual inserts: {e}")
                
                # Fallback to individual inserts within the batch
                try:
                    async with conn.transaction():
                        if is_typed_table:
                            for record in batch:
                                await self._insert_typed_record(conn, table_name, record)
                        else:
                            upsert_sql = f"""
                                INSERT INTO {table_name} (id, data, updated_at)
                                VALUES ($1, $2, NOW())
                                ON CONFLICT (id) 
                                DO UPDATE SET 
                                    data = EXCLUDED.data,
                                    updated_at = NOW()
                            """
                            for record in batch:
                                await conn.execute(upsert_sql, record['id'], json.dumps(record['data']))
                except Exception as inner_e:
                    log.error(f"Both batch and individual insert methods failed for batch {i}-{batch_end}: {inner_e}")
                    raise
            
            processed_count += len(batch)
            
            # Log progress every batch for visibility
            if i % self._batch_size == 0 or batch_end == total_records:
                log.info(f"Batch upsert progress: {processed_count}/{total_records} records ({processed_count/total_records*100:.1f}%)")

    async def _batch_upsert_typed_records(self, conn: Connection, table_name: str, batch: list[dict]) -> None:
        """Batch upsert for typed tables with specific columns."""
        async with conn.transaction():
            # Ensure table name is properly sanitized for SQL
            table_name = self._sanitize_table_name(table_name)

            if 'entities' in table_name:
                upsert_sql = f"""
                    INSERT INTO {table_name} (id, human_readable_id, title, type, description, text_unit_ids, frequency, degree, x, y, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        human_readable_id = EXCLUDED.human_readable_id,
                        title = EXCLUDED.title,
                        type = EXCLUDED.type,
                        description = EXCLUDED.description,
                        text_unit_ids = EXCLUDED.text_unit_ids,
                        frequency = EXCLUDED.frequency,
                        degree = EXCLUDED.degree,
                        x = EXCLUDED.x,
                        y = EXCLUDED.y,
                        updated_at = NOW()
                """
                batch_data = [
                    (r['id'], r['human_readable_id'], r['title'], r['type'], r['description'], 
                     json.dumps(r['text_unit_ids']), r['frequency'], r['degree'], r['x'], r['y'])
                    for r in batch
                ]
            elif 'relationships' in table_name:
                upsert_sql = f"""
                    INSERT INTO {table_name} (id, human_readable_id, source, target, description, weight, combined_degree, text_unit_ids, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        human_readable_id = EXCLUDED.human_readable_id,
                        source = EXCLUDED.source,
                        target = EXCLUDED.target,
                        description = EXCLUDED.description,
                        weight = EXCLUDED.weight,
                        combined_degree = EXCLUDED.combined_degree,
                        text_unit_ids = EXCLUDED.text_unit_ids,
                        updated_at = NOW()
                """
                batch_data = [
                    (r['id'], r['human_readable_id'], r['source'], r['target'], r['description'], 
                     r['weight'], r['combined_degree'], json.dumps(r['text_unit_ids']))
                    for r in batch
                ]
            elif 'communities' in table_name:
                upsert_sql = f"""
                    INSERT INTO {table_name} (id, human_readable_id, community, level, parent, children, text_unit_ids, entity_ids, relationship_ids, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        human_readable_id = EXCLUDED.human_readable_id,
                        community = EXCLUDED.community,
                        level = EXCLUDED.level,
                        parent = EXCLUDED.parent,
                        children = EXCLUDED.children,
                        text_unit_ids = EXCLUDED.text_unit_ids,
                        entity_ids = EXCLUDED.entity_ids,
                        relationship_ids = EXCLUDED.relationship_ids,
                        updated_at = NOW()
                """
                batch_data = [
                    (r['id'], r['human_readable_id'], r['community'], r['level'], r['parent'],
                     json.dumps(r['children']), json.dumps(r['text_unit_ids']), 
                     json.dumps(r['entity_ids']), json.dumps(r['relationship_ids']))
                    for r in batch
                ]
            elif 'text_units' in table_name:
                upsert_sql = f"""
                    INSERT INTO {table_name} (id, human_readable_id, text, n_tokens, document_ids, entity_ids, relationship_ids, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        human_readable_id = EXCLUDED.human_readable_id,
                        text = EXCLUDED.text,
                        n_tokens = EXCLUDED.n_tokens,
                        document_ids = EXCLUDED.document_ids,
                        entity_ids = EXCLUDED.entity_ids,
                        relationship_ids = EXCLUDED.relationship_ids,
                        updated_at = NOW()
                """
                batch_data = [
                    (r['id'], r['human_readable_id'], r['text'], r['n_tokens'],
                     json.dumps(r['document_ids']), json.dumps(r['entity_ids']), json.dumps(r['relationship_ids']))
                    for r in batch
                ]
            elif 'documents' in table_name:
                upsert_sql = f"""
                    INSERT INTO {table_name} (id, human_readable_id, title, text, text_unit_ids, creation_date, metadata, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        human_readable_id = EXCLUDED.human_readable_id,
                        title = EXCLUDED.title,
                        text = EXCLUDED.text,
                        text_unit_ids = EXCLUDED.text_unit_ids,
                        creation_date = EXCLUDED.creation_date,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """
                batch_data = [
                    (r['id'], r['human_readable_id'], r['title'], r['text'],
                     json.dumps(r['text_unit_ids']), 
                     self._ensure_datetime(r['creation_date']),
                     json.dumps(r['metadata']))
                    for r in batch
                ]
            else:
                raise ValueError(f"Unknown typed table: {table_name}")
            
            await conn.executemany(upsert_sql, batch_data)

    async def _batch_upsert_generic_records(self, conn: Connection, table_name: str, batch: list[dict]) -> None:
        """Batch upsert for generic tables using JSONB."""
        async with conn.transaction():
            # Ensure table name is properly sanitized for SQL
            table_name = self._sanitize_table_name(table_name)
            upsert_sql = f"""
                INSERT INTO {table_name} (id, data, metadata, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (id) 
                DO UPDATE SET 
                    data = EXCLUDED.data,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """
            batch_data = [
                (record['id'], json.dumps(record['data']), json.dumps(record['metadata']))
                for record in batch
            ]
            await conn.executemany(upsert_sql, batch_data)

    async def _insert_typed_record(self, conn: Connection, table_name: str, record: dict) -> None:
        """Insert a single typed record (fallback method)."""
        # This is a simplified fallback - implement based on table type if needed
        # For now, just use the batch method with a single record
        await self._batch_upsert_typed_records(conn, table_name, [record])

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
                
                # Determine if this is a typed table or generic table
                is_typed_table = any(table_type in table_name for table_type in 
                                   ['entities', 'relationships', 'communities', 'text_units', 'documents'])
                
                if is_typed_table:
                    # For typed tables, select all columns except created_at/updated_at
                    if 'documents' in table_name:
                        query = "SELECT id, human_readable_id, title, text, text_unit_ids, creation_date, metadata FROM {} ORDER BY created_at".format(table_name)
                    elif 'entities' in table_name:
                        query = "SELECT id, human_readable_id, title, type, description, text_unit_ids, frequency, degree, x, y FROM {} ORDER BY created_at".format(table_name)
                    elif 'relationships' in table_name:
                        query = "SELECT id, human_readable_id, source, target, description, weight, combined_degree, text_unit_ids FROM {} ORDER BY created_at".format(table_name)
                    elif 'communities' in table_name:
                        query = "SELECT id, human_readable_id, community, level, parent, children, text_unit_ids, entity_ids, relationship_ids FROM {} ORDER BY created_at".format(table_name)
                    elif 'text_units' in table_name:
                        query = "SELECT id, human_readable_id, text, n_tokens, document_ids, entity_ids, relationship_ids FROM {} ORDER BY created_at".format(table_name)
                    else:
                        # Fallback for unknown typed table
                        query = "SELECT * FROM {} ORDER BY created_at".format(table_name)
                else:
                    # For generic tables, use the data column
                    query = "SELECT id, data FROM {} ORDER BY created_at".format(table_name)
                
                rows = await conn.fetch(query)
                
                if not rows:
                    log.info(f"No data found in table {table_name}")
                    return None

                log.info(f"Retrieved {len(rows)} records from table {table_name}")

                # Check if this should be treated as raw data instead of tabular data
                if (not key.endswith('.parquet') or 
                    'state' in key.lower() or 
                    key.endswith('.json') or 
                    'context' in table_name.lower()):
                    # Handle state.json or context.json as raw data
                    # For non-tabular data, return the raw content from the first record
                    if rows:
                        if is_typed_table:
                            # For typed tables, convert row to dict and return as JSON
                            row_dict = dict(rows[0])
                            json_str = json.dumps(row_dict)
                            return json_str.encode(encoding or self._encoding) if as_bytes else json_str
                        elif 'data' in rows[0]:
                            raw_content = rows[0]['data']
                            if isinstance(raw_content, dict):
                                json_str = json.dumps(raw_content)
                                return json_str.encode(encoding or self._encoding) if as_bytes else json_str
                    return b"" if as_bytes else ""

                # Convert to DataFrame
                records = []
                for row in rows:
                    if is_typed_table:
                        # For typed tables, the row is already the data we need
                        record_data = dict(row)
                        
                        # Convert JSONB fields back to proper Python objects
                        for field in ['text_unit_ids', 'children', 'entity_ids', 'relationship_ids', 'document_ids', 'metadata']:
                            if field in record_data:
                                value = record_data[field]
                                
                                if value is None:
                                    record_data[field] = {} if field == 'metadata' else []
                                elif isinstance(value, str):
                                    # Handle JSONB strings - they should always be valid JSON
                                    try:
                                        parsed = json.loads(value)
                                        # Validate the parsed type
                                        if field == 'metadata':
                                            record_data[field] = parsed if isinstance(parsed, dict) else {}
                                        else:
                                            record_data[field] = parsed if isinstance(parsed, list) else []
                                    except (json.JSONDecodeError, TypeError):
                                        log.warning(f"Failed to parse JSONB field {field}: {value}")
                                        # Fallback for non-JSON strings
                                        if field == 'metadata':
                                            record_data[field] = {}
                                        else:
                                            record_data[field] = []
                                elif isinstance(value, (list, dict)):
                                    # Already correct type (shouldn't happen with JSONB, but handle it)
                                    record_data[field] = value
                                else:
                                    # Convert other types
                                    if field == 'metadata':
                                        record_data[field] = {'value': str(value)} if value else {}
                                    else:
                                        record_data[field] = [value] if value else []
                    else:
                        # Handle generic table data (JSONB data column)
                        if isinstance(row['data'], dict):
                            record_data = dict(row['data'])
                        else:
                            # If it's a string, parse it as JSON
                            record_data = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
                    
                    # Clean up the record data - convert None to proper values and handle NaN
                    cleaned_data = {}
                    for key_name, value in record_data.items():
                        if self._is_scalar_na(value) or value is None:
                            cleaned_data[key_name] = None
                        elif isinstance(value, str) and key_name == 'text_unit_ids' and not is_typed_table:
                            # Try to parse text_unit_ids back from JSON string if needed (only for generic tables)
                            try:
                                parsed_value = json.loads(value)
                                cleaned_data[key_name] = parsed_value if isinstance(parsed_value, list) else [value]
                            except (json.JSONDecodeError, TypeError):
                                # If it's not JSON, treat as a single item list or keep as string
                                cleaned_data[key_name] = [value] if value else []
                        elif key_name in ['children', 'entity_ids', 'relationship_ids', 'text_unit_ids', 'document_ids'] and not is_typed_table:
                            # Always ensure these columns are lists (only for generic tables - typed tables already handled this)
                            if isinstance(value, list):
                                cleaned_data[key_name] = value
                            elif isinstance(value, str):
                                try:
                                    parsed_value = json.loads(value)
                                    cleaned_data[key_name] = parsed_value if isinstance(parsed_value, list) else []
                                except (json.JSONDecodeError, TypeError):
                                    cleaned_data[key_name] = []
                            elif value is None:
                                cleaned_data[key_name] = []
                            else:
                                # fallback: wrap single value in a list
                                cleaned_data[key_name] = [value]
                        elif isinstance(value, (list, np.ndarray)) and len(value) == 0:
                            # Handle empty arrays/lists
                            cleaned_data[key_name] = []
                        else:
                            cleaned_data[key_name] = value
                    
                    # Always include the ID column for GraphRAG compatibility
                    # Use the storage ID as is since we simplified ID handling
                    storage_id = row['id']
                    cleaned_data['id'] = storage_id
                    
                    records.append(cleaned_data)

                df = pd.DataFrame(records)
                
                # Additional cleanup for NaN values in the DataFrame
                df = df.where(pd.notna(df), None)
                log.info(f"Created DataFrame with shape: {df.shape}")
                log.info(f"Table {table_name} DataFrame columns: {df.columns.tolist()}")

                if len(df) > 0:
                    log.debug(f"Table {table_name} Sample record: {df.iloc[0].to_dict()}")
                    # Debug: Check if children column exists and its type
                    if 'children' in df.columns:
                        sample_children = df.iloc[0]['children']
                        log.debug(f"Table {table_name} Sample children value: {sample_children}, type: {type(sample_children)}")

                # Handle bytes conversion for GraphRAG compatibility
                if as_bytes or kwargs.get("as_bytes"):
                    log.info(f"Converting DataFrame to parquet bytes for key: {key}")
                    
                    # Apply column filtering similar to Milvus implementation
                    df_clean = df.copy()
                    
                    # Define expected columns for each data type
                    if 'documents' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'title', 'text', 'creation_date', 'metadata']
                    elif 'entities' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'title', 'type', 'description', 'text_unit_ids', 'frequency', 'degree', 'x', 'y']
                    elif 'relationships' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'source', 'target', 'description', 'weight', 'text_unit_ids']
                        if 'combined_degree' in df_clean.columns:
                            expected_columns.append('combined_degree')
                    elif 'text_units' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'text', 'n_tokens', 'document_ids', 'entity_ids', 'relationship_ids']
                    elif 'communities' in table_name:
                        expected_columns = ['id', 'human_readable_id', 'community', 'level', 'parent', 'children', 'text_unit_ids', 'entity_ids', 'relationship_ids']
                    else:
                        expected_columns = list(df_clean.columns)
                    
                    # Filter columns
                    available_columns = [col for col in expected_columns if col in df_clean.columns]
                    if available_columns != expected_columns:
                        missing = set(expected_columns) - set(available_columns)
                        extra = set(df_clean.columns) - set(expected_columns)
                        log.warning(f"Column mismatch - Expected: {expected_columns}, Available: {available_columns}, Missing: {missing}, Extra: {extra}")
                    
                    df_clean = df_clean[available_columns]
                    log.info(f"Table {table_name} final filtered columns: {df_clean.columns.tolist()}")

                    # Convert to parquet bytes
                    try:
                        # Handle list columns for PyArrow compatibility
                        df_for_parquet = df_clean.copy()
                        
                        # For PyArrow/parquet compatibility, we need to handle list columns carefully
                        # Instead of converting to JSON strings, let's try a different approach
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
                                
                                if isinstance(first_non_null, list) or col in ['children', 'entity_ids', 'relationship_ids', 'text_unit_ids', 'document_ids']:
                                    list_columns.append(col)
                                    # Ensure all values in this column are proper lists
                                    df_for_parquet[col] = df_for_parquet[col].apply(
                                        lambda x: x if isinstance(x, list) else ([] if x is None or pd.isna(x) else [str(x)])
                                    )
                        
                        if list_columns:
                            log.info(f"Ensured list columns are proper lists for parquet: {list_columns}")
                        
                        # Try to convert to parquet without JSON string conversion
                        buffer = BytesIO()
                        df_for_parquet.to_parquet(buffer, engine='pyarrow')
                        buffer.seek(0)
                        parquet_bytes = buffer.getvalue()
                        log.info(f"Successfully converted DataFrame to {len(parquet_bytes)} bytes of parquet data")
                        return parquet_bytes
                    except Exception as e:
                        log.warning(f"Direct parquet conversion failed: {e}, trying with JSON string conversion")
                        
                        # Fallback: convert lists to JSON strings
                        try:
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
                                    elif col in ['children', 'entity_ids', 'relationship_ids', 'text_unit_ids', 'document_ids']:
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
                            log.info(f"Successfully converted DataFrame to {len(parquet_bytes)} bytes of parquet data (with JSON conversion)")
                            return parquet_bytes
                        except Exception as e2:
                            log.exception(f"Failed to convert DataFrame to parquet bytes: {e2}")
                            return b""
                
                return df
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception(f"Error retrieving data from table {table_name}: {e}")
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Insert data into PostgreSQL table with drop/recreate to avoid duplicates."""
        try:
            table_name = self._get_table_name(key)
            log.info(f"Setting data for key: {key}, table: {table_name}")
            
            # Use new table creation approach with duplicate prevention
            await self._ensure_table_exists_with_schema(table_name)
            
            conn = await self._get_connection()
            try:
                if isinstance(value, bytes):
                    # Parse parquet data
                    df = pd.read_parquet(BytesIO(value))
                    log.info(f"Parsed parquet data, DataFrame shape: {df.shape}")
                    # output sample record for debugging
                    log.debug(f"Table {table_name} Sample record (first row): {df.iloc[0].to_dict()}")
                    log.info(f"Parsed DataFrame columns: {df.columns.tolist()}")
                    
                    # Prepare data for PostgreSQL (typed or generic)
                    records = self._prepare_data_for_postgres(df, table_name)
                    
                    if records:
                        # Use batch insert for much better performance
                        await self._batch_upsert_records(conn, table_name, records)
                        
                        log.info(f"Successfully inserted {len(records)} records to {table_name}")
                        
                        # Log ID handling info
                        if any(record['id'].split(':')[0] in self._no_id_prefixes for record in records if 'id' in record):
                            log.info(f"Some records used auto-generated IDs in table {table_name}")
                        
                else:
                    # Handle non-parquet data (e.g., JSON, stats) - always use generic table
                    log.info(f"Handling non-parquet data for key: {key}")
                    
                    record_data = json.loads(value) if isinstance(value, str) else value
                    
                    # Use generic table insertion for non-parquet data
                    records = [{
                        'id': key,
                        'data': record_data,
                        'metadata': {'type': 'non_parquet', 'created': datetime.now(timezone.utc).isoformat()}
                    }]
                    
                    await self._batch_upsert_generic_records(conn, table_name, records)
                    log.info("Non-parquet data insertion successful")
                
            finally:
                await self._release_connection(conn)
                
        except Exception as e:
            log.exception("Error setting data in PostgreSQL table %s: %s", table_name, e)
            raise

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
                await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                log.info(f"Deleted record for key {key}")
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
