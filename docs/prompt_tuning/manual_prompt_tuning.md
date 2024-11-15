# Manual Prompt Tuning ⚙️

The GraphRAG indexer, by default, will run with a handful of prompts that are designed to work well in the broad context of knowledge discovery.
However, it is quite common to want to tune the prompts to better suit your specific use case.
We provide a means for you to do this by allowing you to specify a custom prompt file, which will each use a series of token-replacements internally.

Each of these prompts may be overridden by writing a custom prompt file in plaintext. We use token-replacements in the form of `{token_name}`, and the descriptions for the available tokens can be found below.

## Indexing Prompts

### Entity/Relationship Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/entity_extraction.py)

#### Tokens

- **{input_text}** - The input text to be processed.
- **{entity_types}** - A list of entity types
- **{tuple_delimiter}** - A delimiter for separating values within a tuple. A single tuple is used to represent an individual entity or relationship.
- **{record_delimiter}** - A delimiter for separating tuple instances.
- **{completion_delimiter}** - An indicator for when generation is complete.

### Summarize Entity/Relationship Descriptions

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/summarize_descriptions.py)

#### Tokens

- **{entity_name}** - The name of the entity or the source/target pair of the relationship.
- **{description_list}** - A list of descriptions for the entity or relationship.

### Claim Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/claim_extraction.py)

#### Tokens

- **{input_text}** - The input text to be processed.
- **{tuple_delimiter}** - A delimiter for separating values within a tuple. A single tuple is used to represent an individual entity or relationship.
- **{record_delimiter}** - A delimiter for separating tuple instances.
- **{completion_delimiter}** - An indicator for when generation is complete.
- **{entity_specs}** - A list of entity types.
- **{claim_description}** - Description of what claims should look like. Default is: `"Any claims or facts that could be relevant to information discovery."`

See the [configuration documentation](../config/overview.md) for details on how to change this.

### Generate Community Reports

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/community_report.py)

#### Tokens

- **{input_text}** - The input text to generate the report with. This will contain tables of entities and relationships.

## Query Prompts

### Local Search

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/local_search_system_prompt.py)

#### Tokens

- **{response_type}** - Describe how the response should look. We default to "multiple paragraphs".
- **{context_data}** - The data tables from GraphRAG's index.

### Global Search

[Mapper Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_map_system_prompt.py)

[Reducer Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_reduce_system_prompt.py)

[Knowledge Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_knowledge_system_prompt.py)

Global search uses a map/reduce approach to summarization. You can tune these prompts independently. This search also includes the ability to adjust the use of general knowledge from the model's training.

#### Tokens

- **{response_type}** - Describe how the response should look (reducer only). We default to "multiple paragraphs".
- **{context_data}** - The data tables from GraphRAG's index.

### Drift Search

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/drift_search_system_prompt.py)

#### Tokens

- **{response_type}** - Describe how the response should look. We default to "multiple paragraphs".
- **{context_data}** - The data tables from GraphRAG's index.
- **{community_reports}** - The most relevant community reports to include in the summarization.
- **{query}** - The query text as injected into the context.