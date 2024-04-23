```python
# Copyright (c) 2024 Microsoft Corporation. All rights reserved.
```




    '\nCopyright (c) Microsoft Corporation. All rights reserved.\n'




```python
import os
from pathlib import Path

import pandas as pd
import tiktoken

from graphrag.query.input.loaders.dfs import read_community_reports
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch

print(Path.cwd())
```

## Global Search example

Global search method generates answers by searching over all AI-generated community reports in a map-reduce fashion. This is a resource-intensive method, but often gives good responses for questions that require an understanding of the dataset as a whole (e.g. What are the most significant values of the herbs mentioned in this notebook?).

### LLM setup


```python
api_key = os.environ["GRAPHRAG_API_KEY"]
llm_model = os.environ["GRAPHRAG_EMBEDDING_MODEL"]

llm = ChatOpenAI(
    api_key=api_key,
    model=llm_model,
    api_type=OpenaiApiType.OpenAI,  # OpenaiApiType.OpenAI or OpenaiApiType.AzureOpenAI
    max_retries=20,
)

token_encoder = tiktoken.get_encoding("cl100k_base")
```

### Load community reports as context for global search

- Load all community reports from **create_final_community_reports** table from the ire-indexing engine.


```python
# parquet files generated from indexing pipeline
INPUT_DIR = "./inputs/operation dulce"
COMMUNITY_REPORT_TABLE = "create_final_community_reports"
ENTITY_TABLE = "create_final_nodes"

# community level in the Leiden community hierarchy from which we will load the community reports
# higher value means we use reports on smaller communities (and thus will have more reports to query aga
COMMUNITY_LEVEL = 2
```


```python
entity_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_TABLE}.parquet")
entity_df = entity_df[
    (entity_df.type == "entity") & (entity_df.level <= f"level_{COMMUNITY_LEVEL}")
]
entity_df["community"] = entity_df["community"].fillna(-1)
entity_df["community"] = entity_df["community"].astype(int)

entity_df = entity_df.groupby(["title"]).agg({"community": "max"}).reset_index()
entity_df["community"] = entity_df["community"].astype(str)
filtered_community_df = entity_df.rename(columns={"community": "community_id"})[
    "community_id"
].drop_duplicates()

report_df = pd.read_parquet(f"{INPUT_DIR}/{COMMUNITY_REPORT_TABLE}.parquet")
report_df = report_df[report_df.level <= f"level_{COMMUNITY_LEVEL}"]

report_df["rank"] = report_df["rank"].fillna(-1)
report_df["rank"] = report_df["rank"].astype(int)

report_df = report_df.merge(filtered_community_df, on="community_id", how="inner")

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

#### Build global context based on community reports


```python
context_builder = GlobalCommunityContext(
    community_reports=reports, token_encoder=token_encoder
)
```

#### Perform global search


```python
context_builder_params = {
    "use_community_summary": False,  # False means using full community reports. True means using community short summaries.
    "shuffle_data": True,
    "include_community_rank": True,
    "min_community_rank": 0,
    "max_tokens": 12_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
    "context_name": "Reports",
}

map_llm_params = {
    "max_tokens": 500,
    "temperature": 0.0,
}

reduce_llm_params = {
    "max_tokens": 2000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000-1500)
    "temperature": 0.0,
}
```


```python
search_engine = GlobalSearch(
    llm=llm,
    context_builder=context_builder,
    token_encoder=token_encoder,
    max_data_tokens=16_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
    map_llm_params=map_llm_params,
    reduce_llm_params=reduce_llm_params,
    context_builder_params=context_builder_params,
    concurrent_coroutines=32,
    response_type="multiple paragraphs",  # free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
)
```


```python
result = await search_engine.asearch(
    "What is the major conflict in this story and who are the protagonist and antagonist?"
)

print(result.response)
```


```python
# inspect the data used to build the context for the LLM responses
result.context_data["reports"]
```


```python
# inspect number of LLM calls and tokens
print(f"LLM calls: {result.llm_calls}. LLM tokens: {result.prompt_tokens}")
```

    LLM calls: 13. LLM tokens: 184660

