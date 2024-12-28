# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import logging
import time

from datashaper import VerbCallbacks
from datashaper.progress.types import Progress

from graphrag.cache.factory import CacheFactory
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import create_input
from graphrag.index.run.profiling import _dump_stats
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.default_workflows import basic_workflows
from graphrag.logger.base import ProgressLogger
from graphrag.logger.null_progress import NullProgressLogger
from graphrag.storage.factory import StorageFactory

log = logging.getLogger(__name__)


default_workflows = [
    "create_base_text_units",
    "create_final_documents",
    "extract_graph",
    "create_final_covariates",
    "compute_communities",
    "create_final_entities",
    "create_final_relationships",
    "create_final_nodes",
    "create_final_communities",
    "create_final_text_units",
    "create_final_community_reports",
    "generate_text_embeddings",
]


async def run_workflows(
    config: GraphRagConfig,
    cache: PipelineCache | None = None,
    logger: ProgressLogger | None = None,
    run_id: str | None = None,
):
    """Run all workflows using a simplified pipeline."""
    print("RUNNING NEW PIPELINE")
    print(config)

    start_time = time.time()

    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    root_dir = config.root_dir or ""
    progress_logger = logger or NullProgressLogger()
    storage_config = config.storage.model_dump()  # type: ignore
    storage = StorageFactory().create_storage(
        storage_type=storage_config["type"],  # type: ignore
        kwargs=storage_config,
    )
    cache_config = config.cache.model_dump()  # type: ignore
    cache = cache or CacheFactory().create_cache(
        cache_type=cache_config["type"],  # type: ignore
        root_dir=root_dir,
        kwargs=cache_config,
    )
    
    context = create_run_context(storage=storage, cache=cache, stats=None)

    dataset = await create_input(config.input, progress_logger, root_dir)
    log.info("Final # of rows loaded: %s", len(dataset))
    context.stats.num_documents = len(dataset)

    await context.runtime_storage.set("input", dataset)

    for workflow in default_workflows:
        print("RUNNING WORKFLOW", workflow)
        run_workflow = basic_workflows[workflow]
        verb_callbacks = DelegatingCallbacks()
        work_time = time.time()
        await run_workflow(
            config,
            context,
            verb_callbacks,
        )
        context.stats.workflows[workflow] = {"overall": time.time() - work_time}

    context.stats.total_runtime = time.time() - start_time
    await _dump_stats(context.stats, context.storage)


class DelegatingCallbacks(VerbCallbacks):
    """TEMP: this is all to wrap into DataShaper callbacks that the flows expect."""

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Handle when an error occurs."""

    def warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""

    def log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log occurs."""

    def measure(self, name: str, value: float, details: dict | None = None) -> None:
        """Handle when a measurement occurs."""
