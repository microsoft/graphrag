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

    config["community_report_full_content_embed"]["strategy"]["type"] = "mock"
    config["community_report_summary_embed"]["strategy"]["type"] = "mock"
    config["community_report_title_embed"]["strategy"]["type"] = "mock"
    config["document_raw_content_embed"]["strategy"]["type"] = "mock"
    config["entity_name_embed"]["strategy"]["type"] = "mock"
    config["entity_name_description_embed"]["strategy"]["type"] = "mock"
    config["relationship_description_embed"]["strategy"]["type"] = "mock"
    config["text_unit_text_embed"]["strategy"]["type"] = "mock"
    config["snapshot_embeddings"] = True

    config["embedded_fields"] = all_embeddings

    config["community_report_full_content_embed"]["strategy"]["vector_store"] = {
        "title_column": "full_content",
        "collection_name": "final_community_reports_full_content_embedding",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["community_report_summary_embed"]["strategy"]["vector_store"] = {
        "title_column": "summary",
        "collection_name": "final_community_reports_summary_embedding",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["community_report_title_embed"]["strategy"]["vector_store"] = {
        "title_column": "title",
        "collection_name": "final_community_reports_title_embedding",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["document_raw_content_embed"]["strategy"]["vector_store"] = {
        "title_column": "raw_content",
        "collection_name": "final_documents_raw_content_embedding",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["entity_name_embed"]["strategy"]["vector_store"] = {
        "title_column": "name",
        "collection_name": "entity_name_embeddings",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["entity_name_description_embed"]["strategy"]["vector_store"] = {
        "title_column": "name_description",
        "collection_name": "entity_description_embeddings",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["relationship_description_embed"]["strategy"]["vector_store"] = {
        "title_column": "description",
        "collection_name": "relationships_description_embeddings",
        "type": "lancedb",
        "db_uri": "./lancedb",
    }
    config["text_unit_text_embed"]["strategy"]["vector_store"] = {
        "title_column": "text",
        "collection_name": "text_units_embedding",
        "type": "lancedb",
        "db_uri": "./lancedb",
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
