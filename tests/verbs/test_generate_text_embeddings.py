# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from io import BytesIO

import pandas as pd

from graphrag.index.config.embeddings import (
    all_embeddings,
)
from graphrag.index.run.utils import create_run_context
from graphrag.index.workflows.v1.generate_text_embeddings import (
    build_steps,
    workflow_name,
)

from .util import (
    get_config_for_workflow,
    get_workflow_output,
    load_input_tables,
)


async def test_generate_text_embeddings():
    input_tables = load_input_tables(
        inputs=[
            "workflow:create_final_documents",
            "workflow:create_final_relationships",
            "workflow:create_final_text_units",
            "workflow:create_final_entities",
            "workflow:create_final_community_reports",
        ]
    )
    context = create_run_context(None, None, None)

    config = get_config_for_workflow(workflow_name)

    config["text_embed"]["strategy"]["type"] = "mock"
    config["embedded_fields"] = all_embeddings
    config["text_embed"]["strategy"]["vector_store"] = {
        "type": "lancedb",
        "db_uri": "./lancedb",
        "store_in_table": True,
    }

    steps = build_steps(config)

    await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
        context,
    )

    parquet_files = context.storage.keys()
    assert "create_final_documents_raw_content_embeddings.parquet" in parquet_files
    assert "create_final_relationships_description_embeddings.parquet" in parquet_files
    assert "create_final_text_units_text_embeddings.parquet" in parquet_files
    assert "create_final_entities_name_embeddings.parquet" in parquet_files
    assert "create_final_entities_description_embeddings.parquet" in parquet_files
    assert "create_final_community_reports_title_embeddings.parquet" in parquet_files
    assert "create_final_community_reports_summary_embeddings.parquet" in parquet_files
    assert (
        "create_final_community_reports_full_content_embeddings.parquet"
        in parquet_files
    )

    create_final_documents_raw_content_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_documents_raw_content_embeddings.parquet", as_bytes=True
        )
    )
    create_final_documents_raw_content_embeddings = pd.read_parquet(
        create_final_documents_raw_content_embeddings_buffer
    )
    assert len(create_final_documents_raw_content_embeddings.columns) == 2
    assert "id" in create_final_documents_raw_content_embeddings.columns
    assert "embedding" in create_final_documents_raw_content_embeddings.columns

    create_final_relationships_description_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_relationships_description_embeddings.parquet", as_bytes=True
        )
    )
    create_final_relationships_description_embeddings = pd.read_parquet(
        create_final_relationships_description_embeddings_buffer
    )
    assert len(create_final_relationships_description_embeddings.columns) == 2
    assert "id" in create_final_relationships_description_embeddings.columns
    assert "embedding" in create_final_relationships_description_embeddings.columns

    create_final_text_units_text_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_text_units_text_embeddings.parquet", as_bytes=True
        )
    )
    create_final_text_units_text_embeddings = pd.read_parquet(
        create_final_text_units_text_embeddings_buffer
    )
    assert len(create_final_text_units_text_embeddings.columns) == 2
    assert "id" in create_final_text_units_text_embeddings.columns
    assert "embedding" in create_final_text_units_text_embeddings.columns

    create_final_entities_name_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_entities_name_embeddings.parquet", as_bytes=True
        )
    )
    create_final_entities_name_embeddings = pd.read_parquet(
        create_final_entities_name_embeddings_buffer
    )
    assert len(create_final_entities_name_embeddings.columns) == 2
    assert "id" in create_final_entities_name_embeddings.columns
    assert "embedding" in create_final_entities_name_embeddings.columns

    create_final_entities_description_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_entities_description_embeddings.parquet", as_bytes=True
        )
    )
    create_final_entities_description_embeddings = pd.read_parquet(
        create_final_entities_description_embeddings_buffer
    )
    assert len(create_final_entities_description_embeddings.columns) == 2
    assert "id" in create_final_entities_description_embeddings.columns
    assert "embedding" in create_final_entities_description_embeddings.columns

    create_final_community_reports_title_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_community_reports_title_embeddings.parquet", as_bytes=True
        )
    )
    create_final_community_reports_title_embeddings = pd.read_parquet(
        create_final_community_reports_title_embeddings_buffer
    )
    assert len(create_final_community_reports_title_embeddings.columns) == 2
    assert "id" in create_final_community_reports_title_embeddings.columns
    assert "embedding" in create_final_community_reports_title_embeddings.columns

    create_final_community_reports_summary_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_community_reports_summary_embeddings.parquet", as_bytes=True
        )
    )
    create_final_community_reports_summary_embeddings = pd.read_parquet(
        create_final_community_reports_summary_embeddings_buffer
    )
    assert len(create_final_community_reports_summary_embeddings.columns) == 2
    assert "id" in create_final_community_reports_summary_embeddings.columns
    assert "embedding" in create_final_community_reports_summary_embeddings.columns

    create_final_community_reports_full_content_embeddings_buffer = BytesIO(
        await context.storage.get(
            "create_final_community_reports_full_content_embeddings.parquet",
            as_bytes=True,
        )
    )
    create_final_community_reports_full_content_embeddings = pd.read_parquet(
        create_final_community_reports_full_content_embeddings_buffer
    )
    assert len(create_final_community_reports_full_content_embeddings.columns) == 2
    assert "id" in create_final_community_reports_full_content_embeddings.columns
    assert "embedding" in create_final_community_reports_full_content_embeddings.columns
