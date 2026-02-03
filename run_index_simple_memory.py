#!/usr/bin/env python3
# Copyright (C) 2025 Microsoft
# Licensed under the MIT License

"""Run GraphRAG indexing with simple memory tracking."""

import asyncio
import sys
import time
import tracemalloc
from pathlib import Path

# Add graphrag to path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "graphrag"))

from graphrag.api import build_index
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.config.load_config import load_config


def format_size(bytes):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"


async def run_indexing():
    """Run the indexing pipeline with memory tracking."""
    root_dir = Path.cwd()
    
    print(f"Loading config from: {root_dir}")
    config = load_config(root_dir=root_dir)
    
    # Skip LLM workflows
    print("\n⚠️  Running minimal workflows for memory testing")
    config.workflows = [
        "load_input_documents",
        "create_base_text_units",
        "create_final_documents"
    ]
    
    print(f"\nInput directory: {config.input_storage.base_dir}")
    print(f"Output directory: {config.output_storage.base_dir}")
    print("\n" + "=" * 70)
    print("Starting GraphRAG indexing with memory tracking...")
    print("=" * 70 + "\n")
    
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    
    # Run indexing
    callbacks = ConsoleWorkflowCallbacks()
    
    results = await build_index(
        config=config,
        callbacks=[callbacks],
        is_update_run=False,
    )
    
    # Get memory and time stats
    end_time = time.time()
    elapsed_time = end_time - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print("\n" + "=" * 70)
    print("Performance Report")
    print("=" * 70)
    print(f"Current memory: {format_size(current)}")
    print(f"Peak memory:    {format_size(peak)}")
    print(f"Execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    print(f"Workflows run:  {len(results)}")
    print("=" * 70)


def main():
    """Main entry point."""
    asyncio.run(run_indexing())


if __name__ == "__main__":
    main()
