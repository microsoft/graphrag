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

from pydantic import BaseModel, Field


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
                return (
                    actual.startswith(expected) if isinstance(actual, str) else False
                )
            case Operator.endswith:
                return (
                    actual.endswith(expected) if isinstance(actual, str) else False
                )
            case Operator.in_:
                return actual in expected if isinstance(expected, list) else False
            case Operator.not_in:
                return (
                    actual not in expected if isinstance(expected, list) else False
                )
            case _:
                return False


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

    and_: list[FilterExpr] = Field(alias="and")

    model_config = {"populate_by_name": True}

    def evaluate(self, obj: Any) -> bool:
        """Evaluate AND expression - all must match."""
        return all(expr.evaluate(obj) for expr in self.and_)


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

    or_: list[FilterExpr] = Field(alias="or")

    model_config = {"populate_by_name": True}

    def evaluate(self, obj: Any) -> bool:
        """Evaluate OR expression - at least one must match."""
        return any(expr.evaluate(obj) for expr in self.or_)


class NotExpr(BaseModel):
    """Logical NOT of a filter expression.

    Inverts the result of the inner expression.

    Example
    -------
        NotExpr(not_=Condition(field="deleted", operator="eq", value=True))
    """

    not_: FilterExpr = Field(alias="not")

    model_config = {"populate_by_name": True}

    def evaluate(self, obj: Any) -> bool:
        """Evaluate NOT expression - invert the inner expression."""
        return not self.not_.evaluate(obj)


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
        return Condition(field=self.name, operator="eq", value=other)

    def __ne__(self, other: object) -> Condition:  # type: ignore[override]
        return Condition(field=self.name, operator="ne", value=other)

    def __gt__(self, other: Any) -> Condition:
        return Condition(field=self.name, operator="gt", value=other)

    def __ge__(self, other: Any) -> Condition:
        return Condition(field=self.name, operator="gte", value=other)

    def __lt__(self, other: Any) -> Condition:
        return Condition(field=self.name, operator="lt", value=other)

    def __le__(self, other: Any) -> Condition:
        return Condition(field=self.name, operator="lte", value=other)

    def contains(self, value: str) -> Condition:
        """Create a 'contains' condition."""
        return Condition(field=self.name, operator="contains", value=value)

    def startswith(self, value: str) -> Condition:
        """Create a 'startswith' condition."""
        return Condition(field=self.name, operator="startswith", value=value)

    def endswith(self, value: str) -> Condition:
        """Create a 'endswith' condition."""
        return Condition(field=self.name, operator="endswith", value=value)

    def in_(self, values: list[Any]) -> Condition:
        """Create an 'in' condition."""
        return Condition(field=self.name, operator="in", value=values)

    def not_in(self, values: list[Any]) -> Condition:
        """Create a 'not_in' condition."""
        return Condition(field=self.name, operator="not_in", value=values)

    def exists(self, value: bool = True) -> Condition:
        """Create an 'exists' condition."""
        return Condition(field=self.name, operator="exists", value=value)


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


# Condition overloads
def _condition_and(self: Condition, other: FilterExpr) -> AndExpr:
    return _make_and(self, other)


def _condition_or(self: Condition, other: FilterExpr) -> OrExpr:
    return _make_or(self, other)


def _condition_invert(self: Condition) -> NotExpr:
    return NotExpr(not_=self)


Condition.__and__ = _condition_and  # type: ignore[method-assign]
Condition.__or__ = _condition_or  # type: ignore[method-assign]
Condition.__invert__ = _condition_invert  # type: ignore[method-assign]


# AndExpr overloads
def _and_expr_and(self: AndExpr, other: FilterExpr) -> AndExpr:
    return _make_and(self, other)


def _and_expr_or(self: AndExpr, other: FilterExpr) -> OrExpr:
    return _make_or(self, other)


def _and_expr_invert(self: AndExpr) -> NotExpr:
    return NotExpr(not_=self)


AndExpr.__and__ = _and_expr_and  # type: ignore[method-assign]
AndExpr.__or__ = _and_expr_or  # type: ignore[method-assign]
AndExpr.__invert__ = _and_expr_invert  # type: ignore[method-assign]


# OrExpr overloads
def _or_expr_and(self: OrExpr, other: FilterExpr) -> AndExpr:
    return _make_and(self, other)


def _or_expr_or(self: OrExpr, other: FilterExpr) -> OrExpr:
    return _make_or(self, other)


def _or_expr_invert(self: OrExpr) -> NotExpr:
    return NotExpr(not_=self)


OrExpr.__and__ = _or_expr_and  # type: ignore[method-assign]
OrExpr.__or__ = _or_expr_or  # type: ignore[method-assign]
OrExpr.__invert__ = _or_expr_invert  # type: ignore[method-assign]


# NotExpr overloads
def _not_expr_and(self: NotExpr, other: FilterExpr) -> AndExpr:
    return _make_and(self, other)


def _not_expr_or(self: NotExpr, other: FilterExpr) -> OrExpr:
    return _make_or(self, other)


def _not_expr_invert(self: NotExpr) -> FilterExpr:
    # Double negation returns the inner expression
    return self.not_


NotExpr.__and__ = _not_expr_and  # type: ignore[method-assign]
NotExpr.__or__ = _not_expr_or  # type: ignore[method-assign]
NotExpr.__invert__ = _not_expr_invert  # type: ignore[method-assign]
