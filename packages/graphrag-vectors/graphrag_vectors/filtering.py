# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Generic filter expressions for vector store queries.

This module provides Pydantic-based filter expressions that can be:
1. Built programmatically using the F builder (for humans)
2. Generated as JSON by an LLM (structured output)
3. Serialized/deserialized for storage or transmission
4. Compiled to native query languages by each vector store implementation

Example (human usage):
    from graphrag_vectors.filtering import F

    # Simple conditions
    results = store.similarity_search_by_vector(embedding, k=10, filters=F.status == "active")
    results = store.similarity_search_by_vector(embedding, k=10, filters=F.age >= 18)

    # Complex conditions
    results = store.similarity_search_by_vector(
        embedding, k=10,
        filters=(F.status == "active") & ((F.role == "admin") | (F.role == "moderator"))
    )

Example (LLM structured output / JSON):
    {
        "and_": [
            {"field": "status", "operator": "eq", "value": "active"},
            {"field": "age", "operator": "gte", "value": 18}
        ]
    }
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class Operator(StrEnum):
    """Comparison operators for filter conditions."""

    eq = "eq"
    ne = "ne"
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"
    contains = "contains"
    startswith = "startswith"
    endswith = "endswith"
    in_ = "in"
    not_in = "not_in"
    exists = "exists"


class Condition(BaseModel):
    """A single filter condition comparing a field to a value.

    Attributes
    ----------
    field : str
        Name of the metadata field to compare.
    operator : Operator
        Comparison operator to use.
    value : Any
        Value to compare against.

    Example
    -------
        Condition(field="status", operator="eq", value="active")
        Condition(field="age", operator="gte", value=18)
    """

    field: str
    operator: Operator
    value: Any

    def evaluate(self, obj: Any) -> bool:
        """Evaluate this condition against an object.

        Parameters
        ----------
        obj : Any
            Object with attributes or a dict to evaluate against.

        Returns
        -------
        bool
            True if the condition matches.
        """
        actual = self._get_field_value(obj)

        if self.operator == Operator.exists:
            exists = actual is not None
            return exists if self.value else not exists

        if actual is None:
            return False

        return self._compare(actual, self.operator, self.value)

    def _get_field_value(self, obj: Any) -> Any:
        """Get the field value from an object or dict."""
        if isinstance(obj, dict):
            return obj.get(self.field)
        if hasattr(obj, self.field):
            return getattr(obj, self.field)
        if hasattr(obj, "data") and isinstance(obj.data, dict):
            return obj.data.get(self.field)
        return None

    def _compare(self, actual: Any, op: Operator, expected: Any) -> bool:
        """Compare actual value against expected using operator."""
        match op:
            case Operator.eq:
                return actual == expected
            case Operator.ne:
                return actual != expected
            case Operator.gt:
                return actual > expected
            case Operator.gte:
                return actual >= expected
            case Operator.lt:
                return actual < expected
            case Operator.lte:
                return actual <= expected
            case Operator.contains:
                if isinstance(actual, str):
                    return expected in actual
                try:
                    return expected in actual
                except TypeError:
                    return False
            case Operator.startswith:
                return actual.startswith(expected) if isinstance(actual, str) else False
            case Operator.endswith:
                return actual.endswith(expected) if isinstance(actual, str) else False
            case Operator.in_:
                return actual in expected if isinstance(expected, list) else False
            case Operator.not_in:
                return actual not in expected if isinstance(expected, list) else False
            case _:
                return False

    def __and__(self, other: FilterExpr) -> AndExpr:
        """Combine with AND."""
        return _make_and(self, other)

    def __or__(self, other: FilterExpr) -> OrExpr:
        """Combine with OR."""
        return _make_or(self, other)

    def __invert__(self) -> NotExpr:
        """Negate this condition."""
        return NotExpr(not_=self)


class AndExpr(BaseModel):
    """Logical AND of multiple filter expressions.

    All expressions must match for the AND to be true.

    Example
    -------
        AndExpr(and_=[
            Condition(field="status", operator="eq", value="active"),
            Condition(field="age", operator="gte", value=18)
        ])
    """

    model_config = ConfigDict(populate_by_name=True)

    and_: list[FilterExpr] = Field(validation_alias="and", serialization_alias="and")

    def evaluate(self, obj: Any) -> bool:
        """Evaluate AND expression - all must match."""
        return all(expr.evaluate(obj) for expr in self.and_)

    def __and__(self, other: FilterExpr) -> AndExpr:
        """Combine with AND."""
        return _make_and(self, other)

    def __or__(self, other: FilterExpr) -> OrExpr:
        """Combine with OR."""
        return _make_or(self, other)

    def __invert__(self) -> NotExpr:
        """Negate this expression."""
        return NotExpr(not_=self)


class OrExpr(BaseModel):
    """Logical OR of multiple filter expressions.

    At least one expression must match for the OR to be true.

    Example
    -------
        OrExpr(or_=[
            Condition(field="role", operator="eq", value="admin"),
            Condition(field="role", operator="eq", value="moderator")
        ])
    """

    model_config = ConfigDict(populate_by_name=True)

    or_: list[FilterExpr] = Field(validation_alias="or", serialization_alias="or")

    def evaluate(self, obj: Any) -> bool:
        """Evaluate OR expression - at least one must match."""
        return any(expr.evaluate(obj) for expr in self.or_)

    def __and__(self, other: FilterExpr) -> AndExpr:
        """Combine with AND."""
        return _make_and(self, other)

    def __or__(self, other: FilterExpr) -> OrExpr:
        """Combine with OR."""
        return _make_or(self, other)

    def __invert__(self) -> NotExpr:
        """Negate this expression."""
        return NotExpr(not_=self)


class NotExpr(BaseModel):
    """Logical NOT of a filter expression.

    Inverts the result of the inner expression.

    Example
    -------
        NotExpr(not_=Condition(field="deleted", operator="eq", value=True))
    """

    model_config = ConfigDict(populate_by_name=True)

    not_: FilterExpr = Field(validation_alias="not", serialization_alias="not")

    def evaluate(self, obj: Any) -> bool:
        """Evaluate NOT expression - invert the inner expression."""
        return not self.not_.evaluate(obj)

    def __and__(self, other: FilterExpr) -> AndExpr:
        """Combine with AND."""
        return _make_and(self, other)

    def __or__(self, other: FilterExpr) -> OrExpr:
        """Combine with OR."""
        return _make_or(self, other)

    def __invert__(self) -> FilterExpr:
        """Double negation returns the inner expression."""
        return self.not_


# Union type for all filter expressions
FilterExpr = Annotated[
    Condition | AndExpr | OrExpr | NotExpr,
    Field(discriminator=None),
]

# Update forward references
AndExpr.model_rebuild()
OrExpr.model_rebuild()
NotExpr.model_rebuild()


# ---------------------------------------------------------------------------
# Fluent F builder
# ---------------------------------------------------------------------------


class FieldRef:
    """Reference to a field for building filter expressions with a fluent API.

    Example
    -------
        F.age >= 18    # Condition(field="age", operator="gte", value=18)
        F.name == "x"  # Condition(field="name", operator="eq", value="x")
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> Condition:  # type: ignore[override]
        """Create an equality condition."""
        return Condition(field=self.name, operator=Operator.eq, value=other)

    def __ne__(self, other: object) -> Condition:  # type: ignore[override]
        """Create a not-equal condition."""
        return Condition(field=self.name, operator=Operator.ne, value=other)

    def __gt__(self, other: Any) -> Condition:
        """Create a greater-than condition."""
        return Condition(field=self.name, operator=Operator.gt, value=other)

    def __ge__(self, other: Any) -> Condition:
        """Create a greater-than-or-equal condition."""
        return Condition(field=self.name, operator=Operator.gte, value=other)

    def __lt__(self, other: Any) -> Condition:
        """Create a less-than condition."""
        return Condition(field=self.name, operator=Operator.lt, value=other)

    def __le__(self, other: Any) -> Condition:
        """Create a less-than-or-equal condition."""
        return Condition(field=self.name, operator=Operator.lte, value=other)

    def contains(self, value: str) -> Condition:
        """Create a 'contains' condition."""
        return Condition(field=self.name, operator=Operator.contains, value=value)

    def startswith(self, value: str) -> Condition:
        """Create a 'startswith' condition."""
        return Condition(field=self.name, operator=Operator.startswith, value=value)

    def endswith(self, value: str) -> Condition:
        """Create a 'endswith' condition."""
        return Condition(field=self.name, operator=Operator.endswith, value=value)

    def in_(self, values: list[Any]) -> Condition:
        """Create an 'in' condition."""
        return Condition(field=self.name, operator=Operator.in_, value=values)

    def not_in(self, values: list[Any]) -> Condition:
        """Create a 'not_in' condition."""
        return Condition(field=self.name, operator=Operator.not_in, value=values)

    def exists(self, value: bool = True) -> Condition:
        """Create an 'exists' condition."""
        return Condition(field=self.name, operator=Operator.exists, value=value)


class _FieldBuilder:
    """Builder for creating field references via attribute access.

    Example
    -------
        F.status == "active"  # Returns Condition
        F.age >= 18           # Returns Condition
    """

    def __getattr__(self, name: str) -> FieldRef:
        """Create a FieldRef for the given field name."""
        return FieldRef(name)


# Singleton for convenient import
F = _FieldBuilder()


# ---------------------------------------------------------------------------
# Operator overloads for combining expressions with & | ~
# ---------------------------------------------------------------------------


def _make_and(left: FilterExpr, right: FilterExpr) -> AndExpr:
    """Create AND expression, flattening nested ANDs."""
    expressions: list[FilterExpr] = []
    if isinstance(left, AndExpr):
        expressions.extend(left.and_)
    else:
        expressions.append(left)
    if isinstance(right, AndExpr):
        expressions.extend(right.and_)
    else:
        expressions.append(right)
    return AndExpr(and_=expressions)


def _make_or(left: FilterExpr, right: FilterExpr) -> OrExpr:
    """Create OR expression, flattening nested ORs."""
    expressions: list[FilterExpr] = []
    if isinstance(left, OrExpr):
        expressions.extend(left.or_)
    else:
        expressions.append(left)
    if isinstance(right, OrExpr):
        expressions.extend(right.or_)
    else:
        expressions.append(right)
    return OrExpr(or_=expressions)
