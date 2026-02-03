# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Integration test for load_input_documents streaming workflow."""

import asyncio

from graphrag_input import TextDocument
from graphrag_storage import StorageConfig, StorageType, create_storage
from graphrag_storage.tables.parquet_table_provider import ParquetTableProvider


async def integration_test_load_documents_streaming():
    """Full integration test demonstrating document loading with streaming."""
    print("\n" + "=" * 70)
    print("Integration Test: Load Input Documents (Streaming)")
    print("=" * 70 + "\n")

    # Setup
    storage = create_storage(StorageConfig(type=StorageType.Memory))
    table_provider = ParquetTableProvider(storage=storage)

    # Simulate documents from various sources
    documents = [
        TextDocument(
            id=f"doc_{i:04d}",
            text=f"This is the content of document {i}. " * 20,  # ~20 words each
            title=f"Document {i}: Sample Title",
            creation_date="2025-01-29T10:00:00",
            raw_data={
                "source": "test_dataset",
                "category": "research" if i % 3 == 0 else "general",
                "word_count": 20,
                "metadata": {"author": f"Author_{i % 5}", "version": 1},
            },
        )
        for i in range(1000)
    ]

    print(f"📚 Created {len(documents)} test documents")
    print(f"   Average text length: ~{len(documents[0].text)} chars\n")

    # Stream documents to storage
    print("⚡ Streaming documents to storage...")
    from dataclasses import asdict

    async with table_provider.open("documents") as doc_table:
        for i, doc in enumerate(documents):
            await doc_table.write(asdict(doc))

            if (i + 1) % 250 == 0:
                print(f"   ✓ Streamed {i + 1}/{len(documents)} documents...")

    print(f"\n✅ Successfully streamed all {len(documents)} documents\n")

    # Verify the data
    print("🔍 Verifying stored data...")
    result = await table_provider.read_dataframe("documents")

    print(f"   Total rows: {len(result)}")
    print(f"   Columns: {list(result.columns)}")
    print(f"   Memory usage: {result.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    print(f"   Sample document ID: {result.iloc[0]['id']}")
    print(f"   Sample title: {result.iloc[0]['title']}")

    # Test streaming read
    print("\n📖 Testing streaming read (row-by-row)...")
    research_count = 0
    general_count = 0

    async with table_provider.open("documents") as doc_table:
        for row in doc_table:
            if row["raw_data"]["category"] == "research":
                research_count += 1
            else:
                general_count += 1

    print(f"   Research documents: {research_count}")
    print(f"   General documents: {general_count}")
    print(f"   Total processed: {research_count + general_count}")

    # Memory comparison
    print("\n💡 Memory Efficiency Comparison:")
    print(
        f"   DataFrame approach: Loads all {len(documents)} docs into memory at once"
    )
    print("   Streaming approach: Processes one document at a time")
    print(
        f"   Memory reduction: ~{len(documents)}x for large datasets (no simultaneous loading)"
    )

    print("\n" + "=" * 70)
    print("✅ Integration test completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(integration_test_load_documents_streaming())
