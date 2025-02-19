# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure DocumentDB Storage implementation of PipelineStorage."""

import json
import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Any

import pandas as pd

from graphrag.logger.base import ProgressLogger
from graphrag.logger.progress import Progress
from graphrag.storage.pipeline_storage import (
    PipelineStorage,
    get_timestamp_formatted_with_local_tz,
)

import psycopg2
from psycopg2.extras import RealDictCursor, Json

log = logging.getLogger(__name__)


class DocumentDBPipelineStorage(PipelineStorage):
    """The DocumentDB Storage Implementation."""

    _connection: psycopg2.extensions.connection
    _cursor: psycopg2.extensions.cursor
    _database_name: str
    _collection: str
    _encoding: str

    def __init__(
        self,
        database_name: str,
        collection: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: int = 5432,
        encoding: str = "utf-8",
    ):
        """Initialize the DocumentDB Storage."""
        self._connection = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port
        )
        self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)
        self._encoding = encoding
        self._database_name = database_name
        self._collection = collection
        log.info(
            "creating documentdb storage with database: %s and table: %s",
            self._database_name,
            self._collection,
        )

        set_first = 'SET search_path TO documentdb_api, documentdb_core;'
        self._cursor.execute(set_first)
        self._connection.commit()
        self._create_collection()

    def _create_collection(self) -> None:
        """Create the table if it doesn't exist."""
        self._cursor.execute(f"""
            SELECT documentdb_api.create_collection('{self._database_name}', '{self._collection}');
    	""")    
        self._connection.commit()

    def _delete_collection(self) -> None:
        """Delete the table if it exists."""
        self._cursor.execute(f"""
            SELECT documentdb_api.drop_collection('{self._database_name}', '{self._collection}');
    	""") 
        self._connection.commit()

    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressLogger | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find documents in a DocumentDB table using a file pattern regex and custom file filter (optional)."""
        base_dir = base_dir or ""
        log.info(
            "search table %s for documents matching %s",
            self._collection,
            file_pattern.pattern,
        )

        if not self._connection or not self._cursor:
            return
                
        try:
            find_query = { 
                "find" : self._collection, 
                "filter" : {
                    "$and": [
                        {
                            "key": {
                                "$regex": file_pattern.pattern
                            } 
                        }
                    ]
                }
            }

            if file_filter:
                for key, value in file_filter.items():
                    find_query["filter"]["$and"].append({key: value})

            if max_count > 0:
                find_query["$limit"] = max_count

            query = f"""
                SELECT cursorPage->>'cursor.firstBatch' AS results
                FROM documentdb_api.find_cursor_first_page('{self._database_name}', {Json(find_query)});
            """

            self._cursor.execute(query)
            item = self._cursor.fetchone()
            items = json.loads(item.get('results', '[]'))
            num_loaded = 0
            num_total = len(items)

            if num_total == 0:
                return
            
            num_filtered = 0
            for item in items:
                key = item["key"]
                match = file_pattern.search(key)
                if match:
                    group = match.groupdict()
                    yield (key, group)
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
        except Exception as ex:
            log.exception(
                "An error occurred while searching for documents in Document DB."
            )

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Fetch an item from the table that matches the given key."""
        try:
            find_query = { 
                "find" : self._collection, 
                "filter" : {
                    "key": key
                }
            }
            
            query = f"""
                SELECT cursorPage->>'cursor.firstBatch' AS results
                FROM documentdb_api.find_cursor_first_page('{self._database_name}', {Json(find_query)});
            """

            self._cursor.execute(query)
            item = self._cursor.fetchone()
            items = json.loads(item.get('results', '[]'))
            if len(items) == 0:
                return None
            
            item = items[0]

            if item:
                return json.dumps(item["value"])
            return None
        except Exception:
            log.exception("Error reading item %s", key)
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Insert or update the contents of a file into the DocumentDB table for the given filename key."""
        try:
            insert_query = { 
                "key": key,
                "value": json.loads(value),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self._cursor.execute(f"""
                SELECT documentdb_api.insert_one('{self._database_name}', '{self._collection}', {Json(insert_query)});
            """)
            self._connection.commit()
        except Exception:
            log.exception("Error writing item %s", key)

    async def has(self, key: str) -> bool:
        """Check if the contents of the given filename key exist in the DocumentDB table."""
        aggregate_query = { 
            "aggregate": self._collection, 
            "pipeline": [ 
                { "$match": { 
                    "key": key 
                    } 
                },
                { 
                    "$count": "key"
                } 
            ] , "cursor": { "batchSize": 1 } }

        self._cursor.execute(f"""
            SELECT jsonb_extract_path_text(results::jsonb, '0', 'key')::int AS count
            FROM (
                SELECT cursorPage->>'cursor.firstBatch' AS results
                FROM documentdb_api.aggregate_cursor_first_page('{self._database_name}', {Json(aggregate_query)})
            );
            """)
        result = self._cursor.fetchone()
        return result.get('count', 0) > 0

    async def delete(self, key: str) -> None:
        """Delete the item with the given filename key from the DocumentDB table."""
        try:
            delete_query = {
                "delete": self._collection, 
                "deletes": [
                    {
                        "q": {
                            "key": key
                        }, "limit": 1
                    }
                ]
            }
            self._cursor.execute(f"SELECT documentdb_api.delete('{self._database_name}', {Json(delete_query)});")
            self._connection.commit()
        except Exception:
            log.exception("Error deleting item %s", key)

    async def clear(self) -> None:
        """Clear all contents from storage."""
        self._delete_collection()
        self._create_collection()

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        self._cursor.execute(f"SELECT key FROM {self._table_name}")
        return [row["key"] for row in self._cursor.fetchall()]

    def child(self, name: str | None) -> PipelineStorage:
        """Create a child storage instance."""
        return self

    def _get_prefix(self, key: str) -> str:
        """Get the prefix of the filename key."""
        return key.split(".")[0]

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date of the item with the given key."""
        try:
            find_query = { 
                "find" : self._collection, 
                "filter" : {
                    "key": key
                }
            }
            
            query = f"""
                SELECT cursorPage->>'cursor.firstBatch' AS results
                FROM documentdb_api.find_cursor_first_page('{self._database_name}', {Json(find_query)});
            """

            self._cursor.execute(query)
            item = self._cursor.fetchone()
            items = json.loads(item.get('results', '[]'))
            if len(items) == 0:
                return ""
            
            item = items[0]

            if item:
                return get_timestamp_formatted_with_local_tz(
                    datetime.fromisoformat(item["created_at"])
                )
            return ""
        except Exception:
            log.exception("Error getting key %s", key)
            return ""


def create_documentdb_storage(**kwargs: Any) -> PipelineStorage:
    """Create a DocumentDB storage instance."""
    log.info("Creating postgres storage")
    database_name = kwargs["database_name"]
    collection = kwargs["collection"]
    user = kwargs["user"]
    password = kwargs["password"]
    host = kwargs.get("host", "localhost")
    port = kwargs.get("port", 5432)
    return DocumentDBPipelineStorage(
        database_name=database_name,
        collection=collection,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
