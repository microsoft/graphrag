# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from graphrag.index.workflows.v1.create_final_text_units import (
    build_steps,
    workflow_name,
)

from .util import (
    compare_outputs,
    get_config_for_workflow,
    get_workflow_output,
    load_expected,
    load_input_tables,
)


async def test_create_final_text_units():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
        "workflow:create_final_covariates",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["covariates_enabled"] = True
    config["skip_text_unit_embedding"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    compare_outputs(actual, expected)


async def test_create_final_text_units_no_covariates():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
        "workflow:create_final_covariates",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["covariates_enabled"] = False
    config["skip_text_unit_embedding"] = True

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    # we're short a covariate_ids column
    compare_outputs(
        actual,
        expected,
        ["id", "text", "n_tokens", "document_ids", "entity_ids", "relationship_ids"],
    )


async def test_create_final_text_units_with_embeddings():
    input_tables = load_input_tables([
        "workflow:create_base_text_units",
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
        "workflow:create_final_covariates",
    ])
    expected = load_expected(workflow_name)

    config = get_config_for_workflow(workflow_name)

    config["covariates_enabled"] = True
    config["skip_text_unit_embedding"] = False
    # default config has a detailed standard embed config
    # just override the strategy to mock so the rest of the required parameters are in place
    config["text_unit_text_embed"]["strategy"]["type"] = "mock"

    steps = build_steps(config)

    actual = await get_workflow_output(
        input_tables,
        {
            "steps": steps,
        },
    )

    assert "text_embedding" in actual.columns
    assert len(actual.columns) == len(expected.columns) + 1
    # the mock impl returns an array of 3 floats for each embedding
    assert len(actual["text_embedding"][:1][0]) == 3
