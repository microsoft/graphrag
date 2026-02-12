# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Experimental Neo4j client for GraphRAG.

This is a minimal proof of concept to replace 1-2 dataframe-based READ operations
during query time with Neo4j-backed reads. All Neo4j logic is optional and falls
back to existing dataframe logic if Neo4j is unavailable or disabled.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Try to import Neo4j driver, but make it optional
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning(
        "Neo4j driver not available. Install with: pip install neo4j"
    )


def _is_neo4j_enabled() -> bool:
    """Check if Neo4j is enabled via environment variable."""
    return os.getenv("GRAPHRAG_USE_NEO4J", "false").lower() == "true"


def _get_neo4j_connection():
    """Get Neo4j database connection."""
    if not NEO4J_AVAILABLE or not _is_neo4j_enabled():
        return None
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, user, password]):
        logger.warning(
            "Neo4j is enabled but connection details are missing. "
            "Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables."
        )
        return None
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        # Test connection
        driver.verify_connectivity()
        return driver
    except Exception as e:
        logger.warning(f"Failed to connect to Neo4j: {e}. Falling back to dataframe reads.")
        return None


def get_entity_by_name_neo4j(entity_name: str) -> dict[str, Any] | None:
    """
    EXPERIMENTAL: Get entity by name from Neo4j.
    
    Falls back to None if Neo4j is unavailable, allowing caller to use dataframe logic.
    
    Parameters
    ----------
    entity_name : str
        Name of the entity to lookup
        
    Returns
    -------
    dict | None
        Entity data as dict with keys: id, name, type
        Returns None if Neo4j is unavailable or entity not found
    """
    driver = _get_neo4j_connection()
    if driver is None:
        return None
    
    try:
        with driver.session() as session:
            result = session.run(
                "MATCH (e:Entity {name: $name}) RETURN e.id as id, e.name as name, e.type as type LIMIT 1",
                name=entity_name
            )
            record = result.single()
            if record:
                return {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"]
                }
            return None
    except Exception as e:
        logger.warning(f"Error querying Neo4j for entity {entity_name}: {e}")
        return None
    finally:
        if driver is not None:
            driver.close()


def get_documents_by_entity_neo4j(entity_name: str) -> list[dict[str, Any]]:
    """
    EXPERIMENTAL: Get documents that mention an entity from Neo4j.
    
    Falls back to empty list if Neo4j is unavailable, allowing caller to use dataframe logic.
    
    Parameters
    ----------
    entity_name : str
        Name of the entity
        
    Returns
    -------
    list[dict]
        List of document dicts with keys: id, title, source
        Returns empty list if Neo4j is unavailable
    """
    driver = _get_neo4j_connection()
    if driver is None:
        return []
    
    try:
        with driver.session() as session:
            result = session.run(
                "MATCH (d:Document)-[:MENTIONS]->(e:Entity {name: $name}) "
                "RETURN d.id as id, d.title as title, d.source as source",
                name=entity_name
            )
            documents = []
            for record in result:
                documents.append({
                    "id": record["id"],
                    "title": record["title"],
                    "source": record.get("source", "")
                })
            return documents
    except Exception as e:
        logger.warning(f"Error querying Neo4j for documents mentioning {entity_name}: {e}")
        return []
    finally:
        if driver is not None:
            driver.close()

