# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Experimental GraphQL schema for GraphRAG Neo4j integration.

This is a minimal proof of concept that exposes ONE read-only query for
accessing entity information from Neo4j. No mutations are included.
"""

from typing import Any

# Try to import GraphQL libraries, but make it optional
try:
    from ariadne import QueryType, make_executable_schema, gql
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False
    # Define minimal types for type checking when GraphQL is unavailable
    QueryType = Any
    make_executable_schema = Any
    gql = Any


# GraphQL type definitions
TYPE_DEFS = """
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
"""


def _create_resolvers():
    """Create GraphQL resolvers."""
    from ariadne import ObjectType
    
    query = QueryType()
    entity_type = ObjectType("Entity")
    
    @query.field("entity")
    def resolve_entity(_, info, name: str) -> dict[str, Any] | None:
        """
        EXPERIMENTAL POC: Resolve entity query from Neo4j.
        
        Parameters
        ----------
        name : str
            Entity name to lookup
            
        Returns
        -------
        dict | None
            Entity data if found, None otherwise
        """
        try:
            from graphrag.graph.neo4j_client import get_entity_by_name_neo4j
            
            entity = get_entity_by_name_neo4j(name)
            return entity
        except Exception:
            return None
    
    @entity_type.field("documents")
    def resolve_entity_documents(entity: dict[str, Any], _) -> list[dict[str, Any]]:
        """
        EXPERIMENTAL POC: Resolve documents for an entity.
        
        Fetches documents mentioning this entity from Neo4j.
        """
        try:
            from graphrag.graph.neo4j_client import get_documents_by_entity_neo4j
            entity_name = entity.get("name")
            if entity_name:
                return get_documents_by_entity_neo4j(entity_name)
        except Exception:
            pass
        
        return []
    
    return query, entity_type


def create_schema():
    """
    Create executable GraphQL schema.
    
    Returns
    -------
    GraphQLSchema | None
        Executable schema if GraphQL libraries are available, None otherwise
    """
    if not GRAPHQL_AVAILABLE:
        return None
    
    query, entity_type = _create_resolvers()
    schema = make_executable_schema(gql(TYPE_DEFS), query, entity_type)
    return schema

