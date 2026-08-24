# GraphRAG Common

> [!WARNING]
> GraphRAG is a research project that explores the functional use of graphs to form a targeted context for question answering. Since our first release in July 2024 the capabilities of frontier models have changed dramatically, and our portfolio of research projects has diversified to match. This project is largely in maintenance mode, and won't be accepting new PRs or implementing new features. We'll perform bug fixes and dependency updates as appropriate, particularly to address CVEs as they arise.

This package provides utility modules for GraphRAG, including a flexible factory system for dependency injection and service registration, and a comprehensive configuration loading system with Pydantic model support, environment variable substitution, and automatic file discovery.

## Factory module

The Factory class provides a flexible dependency injection pattern that can register and create instances of classes implementing a common interface using string-based strategies. It supports both transient scope (creates new instances on each request) and singleton scope (returns the same instance after first creation).

[Open the notebook to explore the factory module example code](example_notebooks/factory_module_example.ipynb)

## Config module

The load_config function provides a comprehensive configuration loading system that automatically discovers and parses YAML/JSON config files into Pydantic models with support for environment variable substitution and .env file loading. It offers flexible features like config overrides, custom parsers for different file formats, and automatically sets the working directory to the config file location for relative path resolution.

[Open the notebook to explore the config module example code](example_notebooks/config_module_example.ipynb)
