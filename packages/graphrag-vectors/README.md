# GraphRAG Vectors

Vector store implementations for GraphRAG.

## Basic Usage

### Using the utility function (recommended)

```python
from graphrag_vectors import (
    create_vector_store,
    VectorStoreType,
    IndexSchema,
)

# Create a vector store using the convenience function
schema_config = IndexSchema(
    index_name="my_index",
    vector_size=1536,
)

vector_store = create_vector_store(
    VectorStoreType.LanceDB,
    db_uri="./lancedb",
    index_schema=schema_config,
)

vector_store.connect(db_uri="./lancedb")
vector_store.create_index()
```

### Using the factory directly

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
    VectorStoreType.LanceDB.value,
    {
        "index_schema": schema_config,
        "db_uri": "./lancedb"
    }
)

vector_store.connect(db_uri="./lancedb")
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
    def connect(self, **kwargs):
        # Implementation
        pass
    
    def create_index(self, **kwargs):
        # Implementation
        pass
    
    # ... implement other required methods

# Register your custom implementation
register_vector_store("my_custom_store", MyCustomVectorStore)

# Use your custom vector store
custom_store = create_vector_store(
    "my_custom_store",
    index_schema=schema_config,
    # ... your custom kwargs
)
```

## Configuration

Vector stores are configured using:
- `IndexSchema`: Schema configuration (index name, field names, vector size)
- Implementation-specific kwargs passed to `create_vector_store()` or the factory's create method
