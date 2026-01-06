# Neo4j and GraphQL Integration (Experimental POC)

## Overview

This is a **minimal proof of concept** (POC) to explore replacing 1-2 dataframe-based READ operations during query time with Neo4j-backed reads, and expose a read-only GraphQL query interface.

**Status**: Experimental / POC - Not for production use

## Scope

### What Was Changed

This POC makes **minimal, targeted changes** to exactly **two workflow steps**:

1. **Entity lookup by name** (`graphrag/query/context_builder/entity_extraction.py`)
   - When entities are looked up by name during query execution, Neo4j is attempted first
   - Falls back to existing dataframe logic if Neo4j is unavailable

2. **Entity→Document relationship lookup** (`graphrag/query/input/retrieval/text_units.py`)
   - When finding documents/text units that mention an entity, Neo4j is attempted first
   - Falls back to existing dataframe logic if Neo4j is unavailable

### What Was NOT Changed

- ❌ Indexing logic remains unchanged (still writes to parquet files)
- ❌ Embedding logic remains unchanged
- ❌ All WRITE operations remain dataframe-based
- ❌ Defaults and prompts are unchanged
- ❌ Settings.yaml behavior is unchanged
- ❌ No other query operations were modified

## Architecture

### Neo4j Data Model

The POC uses a minimal schema with only three node/relationship types:

```cypher
(:Entity {id, name, type})
(:Document {id, title, source})
(:Document)-[:MENTIONS]->(:Entity)
```

**No additional nodes, relationships, or properties are used.**

### Feature Flag

Neo4j usage is controlled by environment variable:

```bash
GRAPHRAG_USE_NEO4J=true
```

When disabled (default), all operations use existing dataframe logic.

### Neo4j Connection

Neo4j connection details are read from environment variables:

- `NEO4J_URI` - Neo4j connection URI (e.g., `bolt://localhost:7687`)
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password

If connection fails or Neo4j is unavailable, the system gracefully falls back to dataframe reads.

## GraphQL API

A minimal GraphQL schema is provided with **ONE read-only query**:

### Schema

```graphql
type Query {
  entity(name: String!): Entity
}

type Entity {
  id: String
  name: String
  type: String
  documents: [Document]
}

type Document {
  id: String
  title: String
  source: String
}
```

### Example Query

```graphql
query {
  entity(name: "Microsoft") {
    id
    name
    type
    documents {
      id
      title
      source
    }
  }
}
```

### Running the GraphQL Server

```python
from graphrag.graph.graphql_server import run_graphql_server

# Start server on default port 5000
run_graphql_server()

# Or customize host/port
run_graphql_server(host="0.0.0.0", port=8080)
```

Then access at `http://localhost:5000/graphql`:

```bash
curl -X POST http://localhost:5000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { entity(name: \"Microsoft\") { name documents { title } } }"}'
```

## Setup

### Prerequisites

1. **Neo4j Database**: A running Neo4j instance with the required schema
2. **Python Dependencies** (optional - only if using GraphQL):
   ```bash
   pip install neo4j ariadne flask
   ```

### Environment Configuration

Add to your `.env` file or environment:

```bash
# Enable Neo4j (disabled by default)
GRAPHRAG_USE_NEO4J=true

# Neo4j connection details
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## Data Population

**Important**: This POC does NOT automatically populate Neo4j with data. You must manually populate Neo4j with entities and documents using the schema above.

Example Cypher for populating data:

```cypher
// Create an entity
CREATE (e:Entity {id: "entity-1", name: "Microsoft", type: "organization"})

// Create a document
CREATE (d:Document {id: "doc-1", title: "Microsoft Research", source: "example.txt"})

// Create relationship
MATCH (d:Document {id: "doc-1"}), (e:Entity {name: "Microsoft"})
CREATE (d)-[:MENTIONS]->(e)
```

## Code Locations

- **Neo4j Client**: `graphrag/graph/neo4j_client.py`
- **GraphQL Schema**: `graphrag/graph/graphql_schema.py`
- **GraphQL Server**: `graphrag/graph/graphql_server.py`
- **Modified Query Logic**: 
  - `graphrag/query/context_builder/entity_extraction.py` (entity lookup)
  - `graphrag/query/input/retrieval/text_units.py` (document lookup)

## Limitations and Considerations

1. **Read-only**: Only READ operations are replaced. All WRITE operations remain unchanged.
2. **Minimal scope**: Only 2 specific workflow steps are modified
3. **Fallback logic**: If Neo4j fails, dataframe logic is used automatically
4. **No data migration**: Neo4j must be populated separately
5. **Experimental**: This is a POC for exploration, not production-ready code

## Future Work

If this POC proves valuable, potential next steps could include:
- Automatic data population from indexing outputs
- Additional query operations
- Performance optimization
- Production hardening

However, this POC intentionally remains minimal to assess feasibility without extensive changes to the codebase.

