# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Profiling functions for the GraphRAG run module."""

import json
import logging
import time
from dataclasses import asdict

from datashaper import MemoryProfile, Workflow, WorkflowRunResult

from graphrag.index.context import PipelineRunStats
from graphrag.index.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


async def _save_profiler_stats(
    storage: PipelineStorage, workflow_name: str, profile: MemoryProfile
):
    """Save the profiler stats to the storage."""
    await storage.set(
        f"{workflow_name}_profiling.peak_stats.csv",
        profile.peak_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.snapshot_stats.csv",
        profile.snapshot_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.time_stats.csv",
        profile.time_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.detailed_view.csv",
        profile.detailed_view.to_csv(index=True),
    )


async def _dump_stats(stats: PipelineRunStats, storage: PipelineStorage) -> None:
    """Dump the stats to the storage."""
    await storage.set(
        "stats.json", json.dumps(asdict(stats), indent=4, ensure_ascii=False)
    )


async def _write_workflow_stats(
    workflow: Workflow,
    workflow_result: WorkflowRunResult,
    workflow_start_time: float,
    start_time: float,
    stats: PipelineRunStats,
    storage: PipelineStorage,
) -> None:
    """Write the workflow stats to the storage."""
    for vt in workflow_result.verb_timings:
        stats.workflows[workflow.name][f"{vt.index}_{vt.verb}"] = vt.timing

    workflow_end_time = time.time()
    stats.workflows[workflow.name]["overall"] = workflow_end_time - workflow_start_time
    stats.total_runtime = time.time() - start_time
    await _dump_stats(stats, storage)

    if workflow_result.memory_profile is not None:
        await _save_profiler_stats(
            storage, workflow.name, workflow_result.memory_profile
        )
