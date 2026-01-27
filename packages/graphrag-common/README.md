# GraphRAG Common

This package provides utility modules for GraphRAG, including a flexible factory system for dependency injection and service registration, and a comprehensive configuration loading system with Pydantic model support, environment variable substitution, and automatic file discovery.

## Factory module

The Factory class provides a flexible dependency injection pattern that can register and create instances of classes implementing a common interface using string-based strategies. It supports both transient scope (creates new instances on each request) and singleton scope (returns the same instance after first creation).

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

The load_config function provides a comprehensive configuration loading system that automatically discovers and parses YAML/JSON config files into Pydantic models with support for environment variable substitution and .env file loading. It offers flexible features like config overrides, custom parsers for different file formats, and automatically sets the working directory to the config file location for relative path resolution.

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

# Basic - by default:
# - searches for Path.cwd() / settings.[yaml|yml|json] 
# - sets the CWD to the directory containing the config file.
#   so if no custom config path is provided than CWD remains unchanged.
# - loads config_directory/.env file
# - parses ${env} in the config file
config = load_config(Config)

# Custom file location
config = load_config(Config, "path_to_config_filename_or_directory_containing_settings.[yaml|yml|json]")

# Using a custom file extension with 
# custom config parser (str) -> dict[str, Any]
config = load_config(
    config_initializer=Config,
    config_path="config.toml",
    config_parser=lambda contents: toml.loads(contents) # Needs toml pypi package
)

# With overrides - provided values override whats in the config file
# Only overrides what is specified - recursively merges settings.
config = load_config(
    config_initializer=Config,
    overrides={
        "name": "some name",
        "logging": {
            "filename": "my_logs.txt"
        }
    },
)

# By default, sets CWD to directory containing config file
# So custom config paths will change the CWD.
config = load_config(
    config_initializer=Config,
    config_path="some/path/to/config.yaml",
    set_cwd=True # default
)

# now cwd == some/path/to
assert Path.cwd() == "some/path/to"

# And now throughout the codebase resolving relative paths in config
# will resolve relative to the config directory
Path(config.logging.directory) == "some/path/to/output/logs"

```