# GraphRAG Vectors

This package provides vector store implementations for GraphRAG with support for multiple backends including LanceDB, Azure AI Search, and Azure Cosmos DB. It offers both a convenient configuration-driven API and direct factory access for creating and managing vector stores with flexible index schema definitions.

## Basic usage with the utility function (recommended)

This demonstrates the recommended approach to create a vector store using the create_vector_store convenience function with configuration objects that specify the store type and index schema. The example shows setting up a LanceDB vector store with a defined index configuration, then connecting to it and creating the index for vector operations.

```python
from graphrag_vectors import (
    create_vector_store,
    VectorStoreType,
    IndexSchema,
)

# Create a vector store using the convenience function
store_config = VectorStoreConfig(
    type="lancedb",
    db_uri="lance"
)

schema_config = IndexSchema(
    index_name="my_index",
    vector_size=1536,
)

vector_store = create_vector_store(
    config=store_config
    index_schema=schema_config,
)

vector_store.connect()
vector_store.create_index()
```

## Basic usage implementing the factory directly

This example shows a different approach to create vector stores by directly using the vector_store_factory with enum types and dictionary-based initialization arguments. This method provides more direct control over the factory creation process while bypassing the convenience function layer.

```python
from graphrag_vectors import (
    VectorStoreFactory,
    vector_store_factory,
    VectorStoreType,
    IndexSchema,
)

# Create a vector store using the factory
schema_config = IndexSchema(
    index_name="my_index",
    vector_size=1536,
)

vector_store = vector_store_factory.create(
    VectorStoreType.LanceDB,
    {
        "index_schema": schema_config,
        "db_uri": "./lancedb"
    }
)

vector_store.connect()
vector_store.create_index()
```

## Supported Vector Stores

- **LanceDB**: Local vector database
- **Azure AI Search**: Azure's managed search service with vector capabilities
- **Azure Cosmos DB**: Azure's NoSQL database with vector search support

## Custom Vector Store

You can register custom vector store implementations:

```python
from graphrag_vectors import VectorStore, register_vector_store, create_vector_store

class MyCustomVectorStore(VectorStore):
    def __init__(self, my_param):
        self.my_param = my_param

    def connect(self):
        # Implementation
        pass
    
    def create_index(self):
        # Implementation
        pass
    
    # ... implement other required methods

# Register your custom implementation
register_vector_store("my_custom_store", MyCustomVectorStore)

# Use your custom vector store
config = VectorStoreConfig(
    type="my_custom_store",
    my_param="something"
)
custom_store = create_vector_store(
    config=config,
    index_schema=schema_config,
)
```

## Configuration

Vector stores are configured using:
- `VectorStoreConfig`: baseline parameters for the store
- `IndexSchema`: Schema configuration for the specific index to create/connect to (index name, field names, vector size)
