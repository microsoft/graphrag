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
