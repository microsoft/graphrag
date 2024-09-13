import pandas as pd
from datashaper import Workflow

# import any non-built-in verbs so they get registered
from graphrag.index.verbs.overrides.aggregate import aggregate

# list out any inputs from the schema so they are loaded into the table context for the workflow
INPUTS = [
    'workflow:create_final_entities',
]
# this is the final output (usually the name of the workflow we're running), which we will load from the test data to assert against
OUTPUT = 'join_text_units_to_entity_ids'

# a copy of the schema. we could load these from their actual workflow python files, but this is easier for now
SCHEMA = {
    "steps": [
        {
            "verb": "select",
            "args": {"columns": ["id", "text_unit_ids"]},
            "input": {"source": "workflow:create_final_entities"},
        },
        {
            "verb": "unroll",
            "args": {
                "column": "text_unit_ids",
            },
        },
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": ["text_unit_ids"],
                "aggregations": [
                    {
                        "column": "id",
                        "operation": "array_agg_distinct",
                        "to": "entity_ids",
                    },
                    {
                        "column": "text_unit_ids",
                        "operation": "any",
                        "to": "id",
                    },
                ],
            },
        },
    ]
}

async def test_join_text_units_to_entity_ids():
    # stick all the inputs in a map - Workflow looks them up by name
    tables: dict[str, pd.DataFrame] = {}
    for input in INPUTS:
        # remove the workflow: prefix if it exists, because that is not part of the actual table filename
        name = input.replace("workflow:", "")
        tables[input] = pd.read_parquet(f'tests/verbs/data/{name}.parquet')

    # the bare minimum workflow is the pipeline schema and table context
    workflow = Workflow(
        schema=SCHEMA,
        input_tables=tables,
    )

    await workflow.run()

    # if there's only one output, it is the default here, no name required
    output = workflow.output()

    # read our pre-computed baseline to compare
    baseline = pd.read_parquet(f'tests/verbs/data/{OUTPUT}.parquet')
    assert output.shape == baseline.shape