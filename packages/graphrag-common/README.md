# GraphRAG Common

## Factory module

```python
from abc import ABC, abstractmethod

from graphrag_common.factory import Factory

class SampleABC(ABC):

    @abstractmethod
    def get_value(self) -> str:
        msg = "Subclasses must implement the get_value method."
        raise NotImplementedError(msg)


class ConcreteClass(SampleABC):
    def __init__(self, value: str):
        self._value = value

    def get_value(self) -> str:
        return self._value

class SampleFactory(Factory[SampleABC]):
"""A Factory for SampleABC classes."""

factory = SampleFactory()

# Registering transient services
# A new one is created for every request
factory.register("some_strategy", ConcreteTestClass)

trans1 = factory.create("some_strategy", {"value": "test1"})
trans2 = factory.create("some_strategy", {"value": "test2"})

assert trans1 is not trans2
assert trans1.get_value() == "test1"
assert trans2.get_value() == "test2"

# Registering singleton services
# After first creation, the same one is returned every time
factory.register("some_other_strategy", ConcreteTestClass, scope="singleton")

single1 = factory.create("some_other_strategy", {"value": "singleton"})
single2 = factory.create("some_other_strategy", {"value": "ignored"})

assert single1 is single2
assert single1.get_value() == "singleton"
assert single2.get_value() == "singleton"
```