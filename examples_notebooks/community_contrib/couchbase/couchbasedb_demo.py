"""
Couchbase Vector Store Demo for GraphRAG.

This module demonstrates the usage of Couchbase as a vector store for GraphRAG,
including data loading, vector store setup, and query execution.
"""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any

import pandas as pd
import tiktoken
from dotenv import load_dotenv

from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.input.loaders.dfs import store_entity_semantic_embeddings
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.couchbasedb import CouchbaseVectorStore

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

INPUT_DIR = os.getenv("INPUT_DIR")
COUCHBASE_CONNECTION_STRING = os.getenv(
    "COUCHBASE_CONNECTION_STRING", "couchbase://localhost"
)
COUCHBASE_USERNAME = os.getenv("COUCHBASE_USERNAME", "Administrator")
COUCHBASE_PASSWORD = os.getenv("COUCHBASE_PASSWORD", "password")
COUCHBASE_BUCKET_NAME = os.getenv("COUCHBASE_BUCKET_NAME", "graphrag-demo")
COUCHBASE_SCOPE_NAME = os.getenv("COUCHBASE_SCOPE_NAME", "shared")
COUCHBASE_COLLECTION_NAME = os.getenv(
    "COUCHBASE_COLLECTION_NAME", "entity_description_embeddings"
)
COUCHBASE_VECTOR_INDEX_NAME = os.getenv("COUCHBASE_VECTOR_INDEX_NAME", "graphrag_index")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# Constants
COMMUNITY_LEVEL = 2

# Table names
TABLE_NAMES = {
    "COMMUNITY_REPORT_TABLE": "create_final_community_reports",
    "ENTITY_TABLE": "create_final_nodes",
    "ENTITY_EMBEDDING_TABLE": "create_final_entities",
    "RELATIONSHIP_TABLE": "create_final_relationships",
    "COVARIATE_TABLE": "create_final_covariates",
    "TEXT_UNIT_TABLE": "create_final_text_units",
}


def load_data() -> dict[str, Any]:
    """Load data from parquet files."""
    logger.info("Loading data from parquet files")
    data = {}

    def load_table(table_name: str, read_function: Callable, *args) -> Any:
        try:
            table_data = pd.read_parquet(
                f"{INPUT_DIR}/{TABLE_NAMES[table_name]}.parquet"
            )
            result = read_function(table_data, *args)
        except FileNotFoundError:
            logger.warning(
                "%(table_name)s file not found. Setting %(table_name_lower)s to None.",
                {"table_name": table_name, "table_name_lower": table_name.lower()},
            )
            result = None
        except Exception:
            logger.exception("Error loading %s", table_name)
            result = None
        return result

    data["entities"] = load_table(
        "ENTITY_TABLE",
        read_indexer_entities,
        pd.read_parquet(f"{INPUT_DIR}/{TABLE_NAMES['ENTITY_EMBEDDING_TABLE']}.parquet"),
        COMMUNITY_LEVEL,
    )
    data["relationships"] = load_table("RELATIONSHIP_TABLE", read_indexer_relationships)
    data["covariates"] = load_table("COVARIATE_TABLE", read_indexer_covariates)
    data["reports"] = load_table(
        "COMMUNITY_REPORT_TABLE",
        read_indexer_reports,
        pd.read_parquet(f"{INPUT_DIR}/{TABLE_NAMES['ENTITY_TABLE']}.parquet"),
        COMMUNITY_LEVEL,
    )
    data["text_units"] = load_table("TEXT_UNIT_TABLE", read_indexer_text_units)

    logger.info("Data loading completed")
    return data


def setup_vector_store() -> CouchbaseVectorStore:
    """Set up and connect to CouchbaseVectorStore."""
    logger.info("Setting up CouchbaseVectorStore")
    try:
        description_embedding_store = CouchbaseVectorStore(
            collection_name=COUCHBASE_COLLECTION_NAME,
            bucket_name=COUCHBASE_BUCKET_NAME,
            scope_name=COUCHBASE_SCOPE_NAME,
            index_name=COUCHBASE_VECTOR_INDEX_NAME,
        )

        auth = PasswordAuthenticator(COUCHBASE_USERNAME, COUCHBASE_PASSWORD)
        cluster_options = ClusterOptions(auth)

        description_embedding_store.connect(
            connection_string=COUCHBASE_CONNECTION_STRING,
            cluster_options=cluster_options,
        )
        logger.info("CouchbaseVectorStore setup completed")
    except Exception:
        logger.exception("Error setting up CouchbaseVectorStore")
        raise
    return description_embedding_store


def setup_models() -> dict[str, Any]:
    """Set up LLM and embedding models."""
    logger.info("Setting up LLM and embedding models")
    try:
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL,
            api_type=OpenaiApiType.OpenAI,
            max_retries=20,
        )

        token_encoder = tiktoken.get_encoding("cl100k_base")

        text_embedder = OpenAIEmbedding(
            api_key=OPENAI_API_KEY,
            api_base=None,
            api_type=OpenaiApiType.OpenAI,
            model=EMBEDDING_MODEL,
            deployment_name=EMBEDDING_MODEL,
            max_retries=20,
        )

        logger.info("LLM and embedding models setup completed")
    except Exception:
        logger.exception("Error setting up models")
        raise

    return {
        "llm": llm,
        "token_encoder": token_encoder,
        "text_embedder": text_embedder,
    }


def store_embeddings(entities: list[Any], vector_store: CouchbaseVectorStore) -> None:
    """Store entity semantic embeddings in Couchbase."""
    logger.info("Storing entity embeddings")

    try:
        store_entity_semantic_embeddings(entities=entities, vectorstore=vector_store)
        logger.info("Entity semantic embeddings stored successfully")
    except AttributeError:
        logger.exception(
            "Error storing entity semantic embeddings. Ensure all entities have an 'id' attribute"
        )
        raise
    except Exception:
        logger.exception("Error storing entity semantic embeddings")
        raise


def create_search_engine(
    data: dict[str, Any], models: dict[str, Any], vector_store: CouchbaseVectorStore
) -> LocalSearch:
    """Create and configure the search engine."""
    logger.info("Creating search engine")
    try:
        context_builder = LocalSearchMixedContext(
            community_reports=data["reports"],
            text_units=data["text_units"],
            entities=data["entities"],
            relationships=data["relationships"],
            covariates=data["covariates"],
            entity_text_embeddings=vector_store,
            embedding_vectorstore_key=EntityVectorStoreKey.ID,
            text_embedder=models["text_embedder"],
            token_encoder=models["token_encoder"],
        )

        local_context_params = {
            "text_unit_prop": 0.5,
            "community_prop": 0.1,
            "conversation_history_max_turns": 5,
            "conversation_history_user_turns_only": True,
            "top_k_mapped_entities": 10,
            "top_k_relationships": 10,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,
            "max_tokens": 12_000,
        }

        llm_params = {
            "max_tokens": 2_000,
            "temperature": 0.0,
        }

        search_engine = LocalSearch(
            llm=models["llm"],
            context_builder=context_builder,
            token_encoder=models["token_encoder"],
            llm_params=llm_params,
            context_builder_params=local_context_params,
            response_type="multiple paragraphs",
        )
        logger.info("Search engine created")
    except Exception:
        logger.exception("Error creating search engine")
        raise
    return search_engine


async def run_query(search_engine: LocalSearch, question: str) -> None:
    """Run a query using the search engine."""
    try:
        logger.info("Running query: %s", question)
        result = await search_engine.asearch(question)
        logger.info("Question: %s", question)
        logger.info("Answer: %s", result.response)
        logger.info("Query completed successfully")
    except Exception:
        logger.exception("An error occurred while processing the query")


async def main() -> None:
    """Orchestrate the demo."""
    try:
        # Start the Couchbase demo
        logger.info("Starting Couchbase demo")

        # Load data from parquet files
        data = load_data()

        # Set up the Couchbase vector store
        vector_store = setup_vector_store()

        # Set up the language models
        models = setup_models()

        # Store entity embeddings if entities exist
        if data["entities"]:
            store_embeddings(data["entities"], vector_store)
        else:
            logger.warning("No entities found to store in Couchbase")

        # Create the search engine
        search_engine = create_search_engine(data, models, vector_store)

        # Run a sample query
        question = "Give me a summary about the story"
        await run_query(search_engine, question)

        logger.info("Couchbase demo completed")
    except Exception:
        logger.exception("An error occurred in the main function")


if __name__ == "__main__":
    asyncio.run(main())
