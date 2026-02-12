# GraphRAG Vectors

This package provides vector store implementations for GraphRAG with support for multiple backends including LanceDB, Azure AI Search, and Azure Cosmos DB. It offers both a convenient configuration-driven API and direct factory access for creating and managing vector stores with flexible index schema definitions.

## Basic usage with the utility function (recommended)

This demonstrates the recommended approach to create a vector store using the create_vector_store convenience function with configuration objects that specify the store type and index schema. The example shows setting up a LanceDB vector store with a defined index configuration, then connecting to it and creating the index for vector operations.

[Open the notebook to explore the basic usage with utility function example code](example_notebooks/basic_usage_with_utility_function_example.ipynb)

## Basic usage implementing the factory directly

This example shows a different approach to create vector stores by directly using the vector_store_factory with enum types and dictionary-based initialization arguments. This method provides more direct control over the factory creation process while bypassing the convenience function layer.

[Open the notebook to explore the basic usage using factory directly example code](example_notebooks/basic_usage_factory_example.ipynb)

## Supported Vector Stores

- **LanceDB**: Local vector database
- **Azure AI Search**: Azure's managed search service with vector capabilities
- **Azure Cosmos DB**: Azure's NoSQL database with vector search support

## Custom Vector Store

You can register custom vector store implementations:

[Open the notebook to explore the custom vector example code](example_notebooks/basic_usage_factory_example.ipynb)

## Configuration

Vector stores are configured using:
- `VectorStoreConfig`: baseline parameters for the store
- `IndexSchema`: Schema configuration for the specific index to create/connect to (index name, field names, vector size)
