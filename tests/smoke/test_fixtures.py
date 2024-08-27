# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import json
import logging
import os
import shutil
import subprocess
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, ClassVar
from unittest import mock

import pandas as pd
import pytest

from graphrag.index.storage.blob_pipeline_storage import BlobPipelineStorage
from graphrag.query.context_builder.community_context import (
    NO_COMMUNITY_RECORDS_WARNING,
)

log = logging.getLogger(__name__)

debug = os.environ.get("DEBUG") is not None
gh_pages = os.environ.get("GH_PAGES") is not None

# cspell:disable-next-line well-known-key
WELL_KNOWN_AZURITE_CONNECTION_STRING = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1"

KNOWN_WARNINGS = [NO_COMMUNITY_RECORDS_WARNING]


def _load_fixtures():
    """Load all fixtures from the tests/data folder."""
    params = []
    fixtures_path = Path("./tests/fixtures/")
    # use the min-csv smoke test to hydrate the docsite parquet artifacts (see gh-pages.yml)
    subfolders = ["min-csv"] if gh_pages else sorted(os.listdir(fixtures_path))

    for subfolder in subfolders:
        if not os.path.isdir(fixtures_path / subfolder):
            continue

        config_file = fixtures_path / subfolder / "config.json"
        params.append((subfolder, json.loads(config_file.read_bytes().decode("utf-8"))))

    return params[1:]  # disable azure blob connection test


def pytest_generate_tests(metafunc):
    """Generate tests for all test functions in this module."""
    run_slow = metafunc.config.getoption("run_slow")
    configs = metafunc.cls.params[metafunc.function.__name__]

    if not run_slow:
        # Only run tests that are not marked as slow
        configs = [config for config in configs if not config[1].get("slow", False)]

    funcarglist = [params[1] for params in configs]
    id_list = [params[0] for params in configs]

    argnames = sorted(arg for arg in funcarglist[0] if arg != "slow")
    metafunc.parametrize(
        argnames,
        [[funcargs[name] for name in argnames] for funcargs in funcarglist],
        ids=id_list,
    )


def cleanup(skip: bool = False):
    """Decorator to cleanup the output and cache folders after each test."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AssertionError:
                raise
            finally:
                if not skip:
                    root = Path(kwargs["input_path"])
                    shutil.rmtree(root / "output", ignore_errors=True)
                    shutil.rmtree(root / "cache", ignore_errors=True)

        return wrapper

    return decorator


async def prepare_azurite_data(input_path: str, azure: dict) -> Callable[[], None]:
    """Prepare the data for the Azurite tests."""
    input_container = azure["input_container"]
    input_base_dir = azure.get("input_base_dir")

    root = Path(input_path)
    input_storage = BlobPipelineStorage(
        connection_string=WELL_KNOWN_AZURITE_CONNECTION_STRING,
        container_name=input_container,
    )
    # Bounce the container if it exists to clear out old run data
    input_storage.delete_container()
    input_storage.create_container()

    # Upload data files
    txt_files = list((root / "input").glob("*.txt"))
    csv_files = list((root / "input").glob("*.csv"))
    data_files = txt_files + csv_files
    for data_file in data_files:
        text = data_file.read_bytes().decode("utf-8")
        file_path = (
            str(Path(input_base_dir) / data_file.name)
            if input_base_dir
            else data_file.name
        )
        await input_storage.set(file_path, text, encoding="utf-8")

    return lambda: input_storage.delete_container()


class TestIndexer:
    params: ClassVar[dict[str, list[tuple[str, dict[str, Any]]]]] = {
        "test_fixture": _load_fixtures()
    }

    def __run_indexer(
        self,
        root: Path,
        input_file_type: str,
    ):
        command = [
            "poetry",
            "run",
            "poe",
            "index",
            "--verbose" if debug else None,
            "--root",
            root.absolute().as_posix(),
            "--reporter",
            "print",
        ]
        command = [arg for arg in command if arg]
        log.info("running command ", " ".join(command))
        completion = subprocess.run(
            command, env={**os.environ, "GRAPHRAG_INPUT_FILE_TYPE": input_file_type}
        )
        assert (
            completion.returncode == 0
        ), f"Indexer failed with return code: {completion.returncode}"

    def __assert_indexer_outputs(
        self, root: Path, workflow_config: dict[str, dict[str, Any]]
    ):
        outputs_path = root / "output"
        output_entries = list(outputs_path.iterdir())
        # Sort the output folders by creation time, most recent
        output_entries.sort(key=lambda entry: entry.stat().st_ctime, reverse=True)

        if not debug:
            assert (
                len(output_entries) == 1
            ), f"Expected one output folder, found {len(output_entries)}"

        output_path = output_entries[0]
        assert output_path.exists(), "output folder does not exist"

        artifacts = output_path / "artifacts"
        assert artifacts.exists(), "artifact folder does not exist"

        # Check stats for all workflow
        stats = json.loads((artifacts / "stats.json").read_bytes().decode("utf-8"))

        # Check all workflows run
        expected_workflows = set(workflow_config.keys())
        workflows = set(stats["workflows"].keys())
        assert (
            workflows == expected_workflows
        ), f"Workflows missing from stats.json: {expected_workflows - workflows}. Unexpected workflows in stats.json: {workflows - expected_workflows}"

        # [OPTIONAL] Check subworkflows
        for workflow in expected_workflows:
            if "subworkflows" in workflow_config[workflow]:
                # Check number of subworkflows
                subworkflows = stats["workflows"][workflow]
                expected_subworkflows = workflow_config[workflow].get(
                    "subworkflows", None
                )
                if expected_subworkflows:
                    assert (
                        len(subworkflows) - 1 == expected_subworkflows
                    ), f"Expected {expected_subworkflows} subworkflows, found: {len(subworkflows) - 1} for workflow: {workflow}: [{subworkflows}]"

                # Check max runtime
                max_runtime = workflow_config[workflow].get("max_runtime", None)
                if max_runtime:
                    assert (
                        stats["workflows"][workflow]["overall"] <= max_runtime
                    ), f"Expected max runtime of {max_runtime}, found: {stats['workflows'][workflow]['overall']} for workflow: {workflow}"

        # Check artifacts
        artifact_files = os.listdir(artifacts)
        assert (
            len(artifact_files) == len(expected_workflows) + 1
        ), f"Expected {len(expected_workflows) + 1} artifacts, found: {len(artifact_files)}"

        for artifact in artifact_files:
            if artifact.endswith(".parquet"):
                output_df = pd.read_parquet(artifacts / artifact)
                artifact_name = artifact.split(".")[0]
                workflow = workflow_config[artifact_name]

                # Check number of rows between range
                assert (
                    workflow["row_range"][0]
                    <= len(output_df)
                    <= workflow["row_range"][1]
                ), f"Expected between {workflow['row_range'][0]} and {workflow['row_range'][1]}, found: {len(output_df)} for file: {artifact}"

                # Get non-nan rows
                nan_df = output_df.loc[
                    :, ~output_df.columns.isin(workflow.get("nan_allowed_columns", []))
                ]
                nan_df = nan_df[nan_df.isna().any(axis=1)]
                assert (
                    len(nan_df) == 0
                ), f"Found {len(nan_df)} rows with NaN values for file: {artifact} on columns: {nan_df.columns[nan_df.isna().any()].tolist()}"

    def __run_query(self, root: Path, query_config: dict[str, str]):
        command = [
            "poetry",
            "run",
            "poe",
            "query",
            "--root",
            root.absolute().as_posix(),
            "--method",
            query_config["method"],
            "--community_level",
            str(query_config.get("community_level", 2)),
            query_config["query"],
        ]

        log.info("running command ", " ".join(command))
        return subprocess.run(command, capture_output=True, text=True)

    @cleanup(skip=debug)
    @mock.patch.dict(
        os.environ,
        {
            **os.environ,
            "BLOB_STORAGE_CONNECTION_STRING": os.getenv(
                "GRAPHRAG_CACHE_CONNECTION_STRING", WELL_KNOWN_AZURITE_CONNECTION_STRING
            ),
            "LOCAL_BLOB_STORAGE_CONNECTION_STRING": WELL_KNOWN_AZURITE_CONNECTION_STRING,
            "GRAPHRAG_CHUNK_SIZE": "1200",
            "GRAPHRAG_CHUNK_OVERLAP": "0",
            "AZURE_AI_SEARCH_URL_ENDPOINT": os.getenv("AZURE_AI_SEARCH_URL_ENDPOINT"),
            "AZURE_AI_SEARCH_API_KEY": os.getenv("AZURE_AI_SEARCH_API_KEY"),
        },
        clear=True,
    )
    @pytest.mark.timeout(800)
    def test_fixture(
        self,
        input_path: str,
        input_file_type: str,
        workflow_config: dict[str, dict[str, Any]],
        query_config: list[dict[str, str]],
    ):
        if workflow_config.get("skip", False):
            print(f"skipping smoke test {input_path})")
            return

        azure = workflow_config.get("azure")
        root = Path(input_path)
        dispose = None
        if azure is not None:
            dispose = asyncio.run(prepare_azurite_data(input_path, azure))

        print("running indexer")
        self.__run_indexer(root, input_file_type)
        print("indexer complete")

        if dispose is not None:
            dispose()

        if not workflow_config.get("skip_assert", False):
            print("performing dataset assertions")
            self.__assert_indexer_outputs(root, workflow_config)

        print("running queries")
        for query in query_config:
            result = self.__run_query(root, query)
            print(f"Query: {query}\nResponse: {result.stdout}")

            # Check stderr because lancedb logs path creating as WARN which leads to false negatives
            stderror = (
                result.stderr if "No existing dataset at" not in result.stderr else ""
            )

            assert (
                stderror == "" or stderror.replace("\n", "") in KNOWN_WARNINGS
            ), f"Query failed with error: {stderror}"
            assert result.stdout is not None, "Query returned no output"
            assert len(result.stdout) > 0, "Query returned empty output"
