# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for the filtering module (no backend required)."""

import json

from graphrag_vectors.filtering import (
    AndExpr,
    Condition,
    F,
    FilterExpr,
    NotExpr,
    Operator,
    OrExpr,
)

# ── Condition.evaluate ──────────────────────────────────────────────────────


class TestConditionEvaluate:
    """Tests for Condition.evaluate() client-side evaluation."""

    def test_eq(self):
        cond = Condition(field="color", operator=Operator.eq, value="red")
        assert cond.evaluate({"color": "red"}) is True
        assert cond.evaluate({"color": "blue"}) is False

    def test_ne(self):
        cond = Condition(field="color", operator=Operator.ne, value="red")
        assert cond.evaluate({"color": "blue"}) is True
        assert cond.evaluate({"color": "red"}) is False

    def test_gt(self):
        cond = Condition(field="score", operator=Operator.gt, value=5)
        assert cond.evaluate({"score": 10}) is True
        assert cond.evaluate({"score": 5}) is False
        assert cond.evaluate({"score": 3}) is False

    def test_gte(self):
        cond = Condition(field="score", operator=Operator.gte, value=5)
        assert cond.evaluate({"score": 5}) is True
        assert cond.evaluate({"score": 4}) is False

    def test_lt(self):
        cond = Condition(field="score", operator=Operator.lt, value=5)
        assert cond.evaluate({"score": 3}) is True
        assert cond.evaluate({"score": 5}) is False

    def test_lte(self):
        cond = Condition(field="score", operator=Operator.lte, value=5)
        assert cond.evaluate({"score": 5}) is True
        assert cond.evaluate({"score": 6}) is False

    def test_in(self):
        cond = Condition(field="tag", operator=Operator.in_, value=["a", "b", "c"])
        assert cond.evaluate({"tag": "b"}) is True
        assert cond.evaluate({"tag": "z"}) is False

    def test_missing_field_returns_false(self):
        cond = Condition(field="missing", operator=Operator.eq, value=42)
        assert cond.evaluate({"other": 1}) is False


# ── AndExpr.evaluate ────────────────────────────────────────────────────────


class TestAndEvaluate:
    """Tests for AndExpr.evaluate() client-side evaluation."""

    def test_all_true(self):
        expr = AndExpr(
            and_=[
                Condition(field="a", operator=Operator.eq, value=1),
                Condition(field="b", operator=Operator.eq, value=2),
            ]
        )
        assert expr.evaluate({"a": 1, "b": 2}) is True

    def test_one_false(self):
        expr = AndExpr(
            and_=[
                Condition(field="a", operator=Operator.eq, value=1),
                Condition(field="b", operator=Operator.eq, value=2),
            ]
        )
        assert expr.evaluate({"a": 1, "b": 99}) is False


# ── OrExpr.evaluate ─────────────────────────────────────────────────────────


class TestOrEvaluate:
    """Tests for OrExpr.evaluate() client-side evaluation."""

    def test_one_true(self):
        expr = OrExpr(
            or_=[
                Condition(field="a", operator=Operator.eq, value=1),
                Condition(field="b", operator=Operator.eq, value=2),
            ]
        )
        assert expr.evaluate({"a": 1, "b": 99}) is True

    def test_none_true(self):
        expr = OrExpr(
            or_=[
                Condition(field="a", operator=Operator.eq, value=1),
                Condition(field="b", operator=Operator.eq, value=2),
            ]
        )
        assert expr.evaluate({"a": 0, "b": 0}) is False


# ── NotExpr.evaluate ────────────────────────────────────────────────────────


class TestNotEvaluate:
    """Tests for NotExpr.evaluate() client-side evaluation."""

    def test_negates_true(self):
        inner = Condition(field="a", operator=Operator.eq, value=1)
        assert NotExpr(not_=inner).evaluate({"a": 1}) is False

    def test_negates_false(self):
        inner = Condition(field="a", operator=Operator.eq, value=1)
        assert NotExpr(not_=inner).evaluate({"a": 2}) is True


# ── F builder ───────────────────────────────────────────────────────────────


class TestFBuilder:
    """Tests for the F fluent builder."""

    def test_eq_produces_condition(self):
        expr = F.color == "red"
        assert isinstance(expr, Condition)
        assert expr.field == "color"
        assert expr.operator == Operator.eq
        assert expr.value == "red"

    def test_ne(self):
        expr = F.color != "red"
        assert isinstance(expr, Condition)
        assert expr.operator == Operator.ne

    def test_gt(self):
        expr = F.score > 5
        assert isinstance(expr, Condition)
        assert expr.operator == Operator.gt
        assert expr.value == 5

    def test_gte(self):
        expr = F.score >= 5
        assert isinstance(expr, Condition)
        assert expr.operator == Operator.gte

    def test_lt(self):
        expr = F.score < 5
        assert isinstance(expr, Condition)
        assert expr.operator == Operator.lt

    def test_lte(self):
        expr = F.score <= 5
        assert isinstance(expr, Condition)
        assert expr.operator == Operator.lte

    def test_in(self):
        expr = F.tag.in_(["a", "b"])
        assert isinstance(expr, Condition)
        assert expr.operator == Operator.in_
        assert expr.value == ["a", "b"]


# ── Operator overloads ──────────────────────────────────────────────────────


class TestOperatorOverloads:
    """Tests for & | ~ operator overloads on expression types."""

    def test_and_two_conditions(self):
        expr = (F.a == 1) & (F.b == 2)
        assert isinstance(expr, AndExpr)
        assert len(expr.and_) == 2

    def test_or_two_conditions(self):
        expr = (F.a == 1) | (F.b == 2)
        assert isinstance(expr, OrExpr)
        assert len(expr.or_) == 2

    def test_not_condition(self):
        expr = ~(F.a == 1)
        assert isinstance(expr, NotExpr)
        assert isinstance(expr.not_, Condition)

    def test_not_and(self):
        expr = ~((F.a == 1) & (F.b == 2))
        assert isinstance(expr, NotExpr)
        assert isinstance(expr.not_, AndExpr)

    def test_and_or_nesting(self):
        """Test complex nesting: (a & b) | c."""
        expr = ((F.a == 1) & (F.b == 2)) | (F.c == 3)
        assert isinstance(expr, OrExpr)


# ── AND/OR flattening ──────────────────────────────────────────────────────


class TestFlattening:
    """Tests for AND/OR expression flattening (associativity)."""

    def test_and_flattening(self):
        """(a & b) & c should produce a flat AndExpr with 3 conditions."""
        expr = (F.a == 1) & (F.b == 2) & (F.c == 3)
        assert isinstance(expr, AndExpr)
        assert len(expr.and_) == 3

    def test_or_flattening(self):
        """(a | b) | c should produce a flat OrExpr with 3 conditions."""
        expr = (F.a == 1) | (F.b == 2) | (F.c == 3)
        assert isinstance(expr, OrExpr)
        assert len(expr.or_) == 3


# ── Double negation ────────────────────────────────────────────────────────


class TestDoubleNegation:
    """Tests for double negation behavior."""

    def test_double_negation(self):
        """~~expr should return the inner expression directly."""
        inner = F.a == 1
        double_neg = ~(~inner)
        # Double negation via __invert__ on NotExpr returns self.not_
        assert isinstance(double_neg, Condition)
        assert double_neg.evaluate({"a": 1}) is True
        assert double_neg.evaluate({"a": 2}) is False


# ── JSON round-trip ─────────────────────────────────────────────────────────


class TestJsonRoundtrip:
    """Tests for JSON serialization/deserialization round-trips."""

    def _roundtrip(self, expr: FilterExpr) -> FilterExpr:
        """Serialize and deserialize a filter expression."""
        payload = expr.model_dump()
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)

        # Determine which type to deserialize based on the model's discriminator
        if isinstance(expr, Condition):
            return Condition.model_validate(parsed)
        if isinstance(expr, AndExpr):
            return AndExpr.model_validate(parsed)
        if isinstance(expr, OrExpr):
            return OrExpr.model_validate(parsed)
        if isinstance(expr, NotExpr):
            return NotExpr.model_validate(parsed)
        msg = f"Unknown type: {type(expr)}"
        raise TypeError(msg)

    def test_condition_roundtrip(self):
        original = Condition(field="x", operator=Operator.eq, value=42)
        restored = self._roundtrip(original)
        assert isinstance(restored, Condition)
        assert restored.field == "x"
        assert restored.operator == Operator.eq
        assert restored.value == 42

    def test_and_roundtrip(self):
        original = AndExpr(
            and_=[
                Condition(field="a", operator=Operator.gt, value=1),
                Condition(field="b", operator=Operator.lt, value=10),
            ]
        )
        restored = self._roundtrip(original)
        assert isinstance(restored, AndExpr)
        assert len(restored.and_) == 2

    def test_or_roundtrip(self):
        original = OrExpr(
            or_=[
                Condition(field="a", operator=Operator.eq, value="x"),
                Condition(field="b", operator=Operator.eq, value="y"),
            ]
        )
        restored = self._roundtrip(original)
        assert isinstance(restored, OrExpr)
        assert len(restored.or_) == 2

    def test_not_roundtrip(self):
        original = NotExpr(
            not_=Condition(field="z", operator=Operator.in_, value=[1, 2, 3])
        )
        restored = self._roundtrip(original)
        assert isinstance(restored, NotExpr)
        assert isinstance(restored.not_, Condition)

    def test_complex_nested_roundtrip(self):
        """Test a deeply nested expression survives round-trip."""
        original = AndExpr(
            and_=[
                OrExpr(
                    or_=[
                        Condition(field="a", operator=Operator.eq, value=1),
                        Condition(field="b", operator=Operator.eq, value=2),
                    ]
                ),
                NotExpr(not_=Condition(field="c", operator=Operator.gt, value=10)),
            ]
        )
        restored = self._roundtrip(original)
        assert isinstance(restored, AndExpr)
        assert len(restored.and_) == 2
        # Verify the evaluate logic still works after round-trip
        assert restored.evaluate({"a": 1, "b": 99, "c": 5}) is True
        assert restored.evaluate({"a": 1, "b": 99, "c": 15}) is False
