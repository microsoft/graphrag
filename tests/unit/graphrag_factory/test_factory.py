# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for graphrag_factory package."""

from abc import ABC, abstractmethod

from graphrag_common.factory import Factory


class TestABC(ABC):
    """Test abstract base class."""

    @abstractmethod
    def get_value(self) -> str:
        """
        Get a string value.

        Returns
        -------
            str: A string value.
        """
        msg = "Subclasses must implement the get_value method."
        raise NotImplementedError(msg)


class ConcreteTestClass(TestABC):
    """Concrete implementation of TestABC."""

    def __init__(self, value: str):
        """Initialize with a string value."""
        self._value = value

    def get_value(self) -> str:
        """Get a string value.

        Returns
        -------
            str: A string value.
        """
        return self._value


def test_factory() -> None:
    """Test the factory behavior."""

    class TestFactory(Factory[TestABC]):
        """Test factory for TestABC implementations."""

    factory = TestFactory()
    factory.register("transient_strategy", ConcreteTestClass)
    factory.register("singleton_strategy", ConcreteTestClass, scope="singleton")

    trans1 = factory.create("transient_strategy", {"value": "test1"})
    trans2 = factory.create("transient_strategy", {"value": "test2"})

    assert trans1 is not trans2
    assert trans1.get_value() == "test1"
    assert trans2.get_value() == "test2"

    single1 = factory.create("singleton_strategy", {"value": "singleton"})
    single2 = factory.create("singleton_strategy", {"value": "singleton"})

    assert single1 is single2
    assert single1.get_value() == "singleton"
    assert single2.get_value() == "singleton"
