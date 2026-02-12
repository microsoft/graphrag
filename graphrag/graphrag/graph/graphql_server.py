# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Experimental GraphQL server for GraphRAG Neo4j integration.

This provides a simple HTTP endpoint to execute GraphQL queries against
Neo4j data. Only READ operations are supported.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    from ariadne import graphql_sync, format_error
    from flask import Flask, request, jsonify
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False
    Flask = Any
    graphql_sync = Any
    format_error = Any


def create_graphql_app():
    """
    Create Flask app with GraphQL endpoint.
    
    EXPERIMENTAL POC: This creates a minimal GraphQL server that exposes
    read-only queries against Neo4j. The endpoint is /graphql.
    
    Returns
    -------
    Flask | None
        Flask app if libraries are available, None otherwise
    """
    if not SERVER_AVAILABLE:
        logger.warning(
            "GraphQL server dependencies not available. "
            "Install with: pip install ariadne flask"
        )
        return None
    
    from graphrag.graph.graphql_schema import create_schema
    
    schema = create_schema()
    if schema is None:
        return None
    
    app = Flask(__name__)
    
    @app.route("/graphql", methods=["POST"])
    def graphql_server():
        """
        GraphQL endpoint.
        
        Accepts POST requests with JSON body:
        {
            "query": "query { entity(name: \"EntityName\") { name documents { title } } }"
        }
        """
        try:
            data = request.get_json()
            query = data.get("query")
            variables = data.get("variables", {})
            
            if not query:
                return jsonify({"error": "Query is required"}), 400
            
            success, result = graphql_sync(
                schema,
                {"query": query, "variables": variables},
                debug=True
            )
            
            status_code = 200 if success else 400
            return jsonify(result), status_code
            
        except Exception as e:
            logger.exception("Error executing GraphQL query")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "experimental": "neo4j-graphql-poc"})
    
    return app


def run_graphql_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """
    Run the GraphQL server.
    
    EXPERIMENTAL POC: Starts a Flask server with GraphQL endpoint.
    
    Parameters
    ----------
    host : str
        Host to bind to (default: 127.0.0.1)
    port : int
        Port to bind to (default: 5000)
    debug : bool
        Enable debug mode (default: False)
    """
    app = create_graphql_app()
    if app is None:
        logger.error("Cannot start GraphQL server: dependencies not available")
        return
    
    logger.info(f"Starting experimental GraphQL server on {host}:{port}")
    logger.warning(
        "This is an experimental POC. Do not use in production."
    )
    app.run(host=host, port=port, debug=debug)

