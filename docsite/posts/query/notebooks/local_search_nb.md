```python
# Copyright (c) 2024 Microsoft Corporation. All rights reserved.
```


```python
import os

import pandas as pd
import tiktoken

from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.input.loaders.dfs import (
    read_community_reports,
    read_covariates,
    read_entities,
    read_relationships,
    read_text_units,
    store_entity_semantic_embeddings,
)
from graphrag.query.input.retrieval.relationships import (
    calculate_relationship_combined_rank,
)
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.qdrant import Qdrant
```

## Local Search Example

Local search method generates answers by combining relevant data from the AI-extracted knowledge-graph with text chunks of the raw documents. This method is suitable for questions that require an understanding of specific entities mentioned in the documents (e.g. What are the healing properties of chamomile?).

### Load text units and graph data tables as context for local search

- In this test we first load indexing outputs from parquet files to dataframes, then convert these dataframes into collections of data objects aligning with the knowledge model.

### Load tables to dataframes


```python
INPUT_DIR = "./inputs/operation dulce"

COMMUNITY_REPORT_TABLE = "create_final_community_reports"
ENTITY_TABLE = "create_final_nodes"
ENTITY_EMBEDDING_TABLE = "create_final_entities"
RELATIONSHIP_TABLE = "create_final_relationships"
COVARIATE_TABLE = "create_final_covariates"
TEXT_UNIT_TABLE = "create_final_text_units"
COMMUNITY_LEVEL = 2
```

#### Read entities


```python
# read nodes table to get community and degree data
entity_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_TABLE}.parquet")
entity_df = entity_df[
    (entity_df.type == "entity") & (entity_df.level <= f"level_{COMMUNITY_LEVEL}")
]
entity_df = entity_df[["title", "degree", "community"]].rename(
    columns={"title": "name", "degree": "rank"}
)

entity_df["community"] = entity_df["community"].fillna(-1)
entity_df["community"] = entity_df["community"].astype(int)
entity_df["rank"] = entity_df["rank"].astype(int)

# for duplicate entities, keep the one with the highest community level
entity_df = entity_df.groupby(["name", "rank"]).agg({"community": "max"}).reset_index()
entity_df["community"] = entity_df["community"].apply(lambda x: [str(x)])

entity_embedding_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_EMBEDDING_TABLE}.parquet")
entity_embedding_df = entity_embedding_df[
    [
        "id",
        "human_readable_id",
        "name",
        "type",
        "description",
        "description_embedding",
        "text_unit_ids",
    ]
]

entity_df = entity_df.merge(
    entity_embedding_df, on="name", how="inner"
).drop_duplicates(subset=["name"])

# read entity dataframe to knowledge model objects
entities = read_entities(
    df=entity_df,
    id_col="id",
    title_col="name",
    type_col="type",
    short_id_col="human_readable_id",
    description_col="description",
    community_col="community",
    rank_col="rank",
    name_embedding_col=None,
    description_embedding_col="description_embedding",
    graph_embedding_col=None,
    text_unit_ids_col="text_unit_ids",
    document_ids_col=None,
)

# load description embeddings to an in-memory qdrant vectorstore
# to connect to a remote db, specify url and port values.
description_embedding_store = Qdrant(
    collection_name="entity_description_embeddings",
)
description_embedding_store.connect()
entity_description_embeddings = store_entity_semantic_embeddings(
    entities=entities, vectorstore=description_embedding_store
)

print(f"Entity count: {len(entity_df)}")
entity_df.head()
```

#### Read relationships


```python
relationship_df = pd.read_parquet(f"{INPUT_DIR}/{RELATIONSHIP_TABLE}.parquet")
relationship_df = relationship_df[
    [
        "id",
        "human_readable_id",
        "source",
        "target",
        "description",
        "weight",
        "text_unit_ids",
    ]
]
relationship_df["id"] = relationship_df["id"].astype(str)
relationship_df["human_readable_id"] = relationship_df["human_readable_id"].astype(str)
relationship_df["weight"] = relationship_df["weight"].astype(float)
relationship_df["text_unit_ids"] = relationship_df["text_unit_ids"].apply(
    lambda x: x.split(",")
)

relationships = read_relationships(
    df=relationship_df,
    id_col="id",
    short_id_col="human_readable_id",
    source_col="source",
    target_col="target",
    description_col="description",
    weight_col="weight",
    description_embedding_col=None,
    text_unit_ids_col="text_unit_ids",
    document_ids_col=None,
)
relationships = calculate_relationship_combined_rank(
    relationships=relationships, entities=entities, ranking_attribute="rank"
)

print(f"Relationship count: {len(relationship_df)}")
relationship_df.head()
```


```python
try:
    covariate_df = pd.read_parquet(f"{INPUT_DIR}/{COVARIATE_TABLE}.parquet")
    covariate_df = (
        covariate_df[
            [
                "id",
                "human_readable_id",
                "type",
                "subject_id",
                "subject_type",
                "object_id",
                "status",
                "start_date",
                "end_date",
                "description",
            ]
        ],
    )

except:  # noqa: E722
    columns = [
        "id",
        "human_readable_id",
        "type",
        "subject_id",
        "object_id",
        "status",
        "start_date",
        "end_date",
        "description",
    ]
    covariate_df = pd.DataFrame({column: [] for column in columns})

covariate_df["id"] = covariate_df["id"].astype(str)
covariate_df["human_readable_id"] = covariate_df["human_readable_id"].astype(str)

claims = read_covariates(
    df=covariate_df,
    id_col="id",
    short_id_col="human_readable_id",
    subject_col="subject_id",
    subject_type_col=None,
    covariate_type_col="type",
    attributes_cols=[
        "object_id",
        "status",
        "start_date",
        "end_date",
        "description",
    ],
    text_unit_ids_col=None,
    document_ids_col=None,
)
print(f"Claim records: {len(claims)}")
covariates = {"claims": claims}
```

#### Read community reports


```python
# get a list of communities from entity table
community_df = entity_df[["community"]].copy()
community_df["community_id"] = community_df["community"].apply(lambda x: str(x[0]))
community_df = community_df[["community_id"]].drop_duplicates(subset=["community_id"])
print(f"Community records: {len(community_df)}")
```


```python
report_df = pd.read_parquet(f"{INPUT_DIR}/{COMMUNITY_REPORT_TABLE}.parquet")
report_df = report_df[report_df.level <= f"level_{COMMUNITY_LEVEL}"]

report_df["rank"] = report_df["rank"].fillna(-1)
report_df["rank"] = report_df["rank"].astype(int)

report_df = report_df.merge(community_df, on="community_id", how="inner")

reports = read_community_reports(
    df=report_df,
    id_col="community_id",
    short_id_col="community_id",
    community_col="community_id",
    title_col="title",
    summary_col="summary",
    content_col="full_content",
    rank_col="rank",
    summary_embedding_col=None,
    content_embedding_col=None,
)

print(f"Report records: {len(report_df)}")
report_df.head()
```

#### Read text units


```python
text_unit_df = pd.read_parquet(f"{INPUT_DIR}/{TEXT_UNIT_TABLE}.parquet")

text_units = read_text_units(
    df=text_unit_df,
    id_col="id",
    short_id_col=None,
    text_col="text",
    embedding_col="text_embedding",
    entities_col=None,
    relationships_col=None,
    covariates_col=None,
)
print(f"Text unit records: {len(text_unit_df)}")
text_unit_df.head()
```


```python
api_key = os.environ["GRAPHRAG_API_KEY"]
llm_model = os.environ["GRAPHRAG_EMBEDDING_MODEL"]
embedding_model = os.environ["GRAPHRAG_EMBEDDING_MODEL"]

llm = ChatOpenAI(
    api_key=api_key,
    model=llm_model,
    api_type=OpenaiApiType.OpenAI,  # OpenaiApiType.OpenAI or OpenaiApiType.AzureOpenAI
    max_retries=20,
)

token_encoder = tiktoken.get_encoding("cl100k_base")

text_embedder = OpenAIEmbedding(
    api_key=api_key,
    api_base=None,
    api_type=OpenaiApiType.OpenAI,
    model=embedding_model,
    deployment_name=embedding_model,
    max_retries=20,
)
```

### Create local search context builder


```python
context_builder = LocalSearchMixedContext(
    community_reports=reports,
    text_units=text_units,
    entities=entities,
    relationships=relationships,
    covariates=covariates,
    entity_text_embeddings=description_embedding_store,
    embedding_vectorstore_key=EntityVectorStoreKey.ID,  # if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
    text_embedder=text_embedder,
    token_encoder=token_encoder,
)
```

### Create local search engine


```python
# text_unit_prop: proportion of context window dedicated to related text units
# community_prop: proportion of context window dedicated to community reports.
# The remaining proportion is dedicated to entities and relationships. Sum of text_unit_prop and community_prop should be <= 1
# conversation_history_max_turns: maximum number of turns to include in the conversation history.
# conversation_history_user_turns_only: if True, only include user queries in the conversation history.
# top_k_mapped_entities: number of related entities to retrieve from the entity description embedding store.
# top_k_relationships: control the number of out-of-network relationships to pull into the context window.
# include_entity_rank: if True, include the entity rank in the entity table in the context window. Default entity rank = node degree.
# include_relationship_weight: if True, include the relationship weight in the context window.
# include_community_rank: if True, include the community rank in the context window.
# return_candidate_context: if True, return a set of dataframes containing all candidate entity/relationship/covariate records that
# could be relevant. Note that not all of these records will be included in the context window. The "in_context" column in these
# dataframes indicates whether the record is included in the context window.
# max_tokens: maximum number of tokens to use for the context window.


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
    "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
    "max_tokens": 12_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
}

llm_params = {
    "max_tokens": 2_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
    "temperature": 0.0,
}
```


```python
search_engine = LocalSearch(
    llm=llm,
    context_builder=context_builder,
    token_encoder=token_encoder,
    llm_params=llm_params,
    context_builder_params=local_context_params,
    response_type="multiple paragraphs",  # free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
)
```

### Run local search on sample queries


```python
result = await search_engine.asearch("Tell me about Agent Mercer")
print(result.response)
```


```python
question = "Tell me about Dr. Jordan Hayes"
result = await search_engine.asearch(question)
print(result.response)
```

#### Inspecting the context data used to generate the response


```python
result.context_data["entities"].head()
```


```python
result.context_data["relationships"].head()
```


```python
result.context_data["reports"].head()
```


```python
result.context_data["sources"].head()
```

### Question Generation

This function takes a list of user queries and generates the next candidate questions.


```python
question_generator = LocalQuestionGen(
    llm=llm,
    context_builder=context_builder,
    token_encoder=token_encoder,
    llm_params=llm_params,
    context_builder_params=local_context_params,
)
```


```python
question_history = [
    "Tell me about Agent Mercer",
    "What happens in Dulce military base?",
]
candidate_questions = await question_generator.agenerate(
    question_history=question_history, context_data=None, question_count=5
)
print(candidate_questions.response)
```
