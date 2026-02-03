# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Example demonstrating streaming table usage.

This example shows how to use the new Table abstraction for memory-efficient
row-by-row processing of large datasets.
"""

import asyncio

import pandas as pd
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


async def example_streaming_write():
    """Demonstrate writing rows incrementally without loading full dataset."""
    storage = create_storage(StorageConfig(type=StorageType.Memory))
    table_provider = ParquetTableProvider(storage=storage)

    print("=== Streaming Write Example ===")

    # Write rows one at a time - memory efficient for large datasets
    async with table_provider.open("users") as table:
        # Simulate processing large dataset row-by-row
        for i in range(1000):
            await table.write({
                "id": i,
                "name": f"User_{i}",
                "email": f"user{i}@example.com",
                "score": i * 1.5,
            })

            if i % 100 == 0:
                print(f"  Processed {i} rows...")

    print("  ✓ Written 1000 rows to 'users' table")

    # Verify using DataFrame API
    result = await table_provider.read_dataframe("users")
    print(f"  ✓ Verified: table has {len(result)} rows\n")


async def example_streaming_read():
    """Demonstrate reading and processing rows incrementally."""
    storage = create_storage(StorageConfig(type=StorageType.Memory))
    table_provider = ParquetTableProvider(storage=storage)

    # Create sample data
    df = pd.DataFrame({
        "id": range(500),
        "value": [f"item_{i}" for i in range(500)],
        "quantity": [i * 2 for i in range(500)],
    })
    await table_provider.write_dataframe("inventory", df)

    print("=== Streaming Read Example ===")

    # Process rows one at a time - memory efficient
    total_quantity = 0
    processed_count = 0

    async with table_provider.open("inventory") as table:
        for row in table:
            total_quantity += row["quantity"]
            processed_count += 1

            if processed_count % 100 == 0:
                print(f"  Processed {processed_count} rows...")

    print(f"  ✓ Processed {processed_count} rows")
    print(f"  ✓ Total quantity: {total_quantity}\n")


async def example_transform_workflow():
    """Demonstrate a transformation workflow using streaming."""
    storage = create_storage(StorageConfig(type=StorageType.Memory))
    table_provider = ParquetTableProvider(storage=storage)

    print("=== Streaming Transform Example ===")

    # Create source data
    source_df = pd.DataFrame({
        "document_id": range(100),
        "text": [f"Document text {i} " * 10 for i in range(100)],
    })
    await table_provider.write_dataframe("documents", source_df)
    print("  Created 100 source documents")

    # Transform: chunk each document into multiple text units (streaming)
    async with table_provider.open("documents") as doc_table:
        async with table_provider.open("text_units") as tu_table:
            chunk_id = 0
            for doc in doc_table:
                # Simulate chunking - split text into parts
                text = doc["text"]
                chunks = [text[i : i + 50] for i in range(0, len(text), 50)]

                # Write each chunk as a separate row
                for chunk_text in chunks:
                    await tu_table.write({
                        "id": chunk_id,
                        "document_id": doc["document_id"],
                        "text": chunk_text,
                        "n_tokens": len(chunk_text.split()),
                    })
                    chunk_id += 1

    # Verify results
    result = await table_provider.read_dataframe("text_units")
    print(f"  ✓ Created {len(result)} text units from {len(source_df)} documents")
    print(
        f"  ✓ Average chunks per document: {len(result) / len(source_df):.1f}\n"
    )


async def example_backward_compatibility():
    """Show that old DataFrame API still works alongside new streaming API."""
    storage = create_storage(StorageConfig(type=StorageType.Memory))
    table_provider = ParquetTableProvider(storage=storage)

    print("=== Backward Compatibility Example ===")

    # Old way: DataFrame API
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    await table_provider.write_dataframe("legacy_users", df)
    print("  ✓ Written using DataFrame API")

    # New way: Streaming read of same data
    async with table_provider.open("legacy_users") as table:
        names = [row["name"] for row in table]
    print(f"  ✓ Read using streaming API: {names}")

    # Mixed: Read with DataFrame, write with streaming
    old_data = await table_provider.read_dataframe("legacy_users")
    async with table_provider.open("new_users") as table:
        for _, row in old_data.iterrows():
            await table.write({
                "id": row["id"],
                "name": row["name"],
                "email": f"{row['name'].lower()}@example.com",
            })
    print("  ✓ Mixed usage: DataFrame → Streaming works seamlessly\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("GraphRAG Streaming Table Examples")
    print("=" * 60 + "\n")

    await example_streaming_write()
    await example_streaming_read()
    await example_transform_workflow()
    await example_backward_compatibility()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
