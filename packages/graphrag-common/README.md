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

## Config module

```python
from pydantic import BaseModel, Field
from graphrag_common.config import load_config

from pathlib import Path

class Logging(BaseModel):
    """Test nested model."""

    directory: str = Field(default="output/logs")
    filename: str = Field(default="logs.txt")

class Config(BaseModel):
    """Test configuration model."""

    name: str = Field(description="Name field.")
    logging: Logging = Field(description="Nested model field.")

# Basic
# By default, ${} env variables in config file will be parsed and replaced
# can disable by setting parse_env_vars=False
config = load_config(Config, "path/to/config.[yaml|yml|json]")

# with .env file
config = load_config(
    config_initializer=Config,
    config_path="config.yaml",
    dot_env_path=".env"
)

# With overrides - provided values override whats in the config file
# Only overrides what is specified - recursively merges settings.
config = load_config(
    config_initializer=Config,
    config_path="config.yaml",
    overrides={
        "name": "some name",
        "logging": {
            "filename": "my_logs.txt"
        }
    },
)

# Set the working directory to the directory of the config file
config = load_config(
    config_initializer=Config,
    config_path="some/path/to/config.yaml",
    set_cwd=True
)

# now cwd == some/path/to
assert Path.cwd() == "some/path/to"

# And now throughout the codebase resolving relative paths in config
# will resolve relative to the config directory
Path(config.logging.directory) == "some/path/to/output/logging"

```