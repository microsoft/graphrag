# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import pandas as pd

from ... import _model


def get_candidate_covariates(
    selected_entities: typing.List[_model.Entity],
    covariates: typing.List[_model.Covariate],
) -> typing.List[_model.Covariate]:
    """Get all covariates that are related to selected entities."""
    selected_entity_names = [entity.title for entity in selected_entities]
    return [
        covariate
        for covariate in covariates
        if covariate.subject_id in selected_entity_names
    ]


def to_covariate_dataframe(covariates: typing.List[_model.Covariate]) -> pd.DataFrame:
    """Convert a list of covariates to a pandas dataframe."""
    if len(covariates) == 0:
        return pd.DataFrame()

    # add header
    header = ["id", "entity"]
    attributes = covariates[0].attributes or {} if len(covariates) > 0 else {}
    attribute_cols = list(attributes.keys()) if len(covariates) > 0 else []
    attribute_cols = [col for col in attribute_cols if col not in header]
    header.extend(attribute_cols)

    records = []
    for covariate in covariates:
        new_record = [
            covariate.short_id if covariate.short_id else "",
            covariate.subject_id,
        ]
        for field in attribute_cols:
            field_value = (
                str(covariate.attributes.get(field))
                if covariate.attributes and covariate.attributes.get(field)
                else ""
            )
            new_record.append(field_value)
        records.append(new_record)
    return pd.DataFrame(records, columns=typing.cast(typing.Any, header))
