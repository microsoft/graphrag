# Bring Your Own Graph

Several users have asked if they can bring their own existing graph and have it summarized for query with GraphRAG. There are many possible ways to do this, but here we'll describe a simple method that aligns with the existing GraphRAG workflows quite easily.

To cover the basic use cases for GraphRAG query, you should have two or three tables derived from your data:

- entities.parquet - this is the list of entities found in the dataset, which are the nodes of the graph.
- relationships.parquet - this is the list of relationships found in the dataset, which are the edges of the graph.
- text_units.parquet - this is the source text chunks the graph was extracted from. This is optional depending on the query method you intend to use (described later).

The approach described here will be to run a custom GraphRAG workflow pipeline that assumes the text chunking, entity extraction, and relationship extraction has already occurred.

## Tables

### Entities

See the full entities [table schema](./outputs.md#entities). For graph summarization purposes, you only need id, title, description, and the list of text_unit_ids.

The additional properties are used for optional graph visualization purposes.

### Relationships

See the full relationships [table schema](./outputs.md#relationships). For graph summarization purposes, you only need id, source, target, description, weight, and the list of text_unit_ids.

> Note: the `weight` field is important because it is used to properly compute Leiden communities!

## Workflow Configuration

GraphRAG includes the ability to specify *only* the specific workflow steps that you need. For basic graph summarization and query, you need the following config in your settings.yaml:

```yaml
workflows: [create_communities, create_community_reports]
```

This will result in only the minimal workflows required for GraphRAG [Global Search](../query/global_search.md).

## Optional Additional Config

If you would like to run [Local](../query/local_search.md), [DRIFT](../query/drift_search.md), or [Basic](../query/overview.md#basic-search) Search, you will need to include text_units and some embeddings.

### Text Units

See the full text_units [table schema](./outputs.md#text_units). Text units are chunks of your documents that are sized to ensure they fit into the context window of your model. Some search methods use these, so you may want to include them if you have them.

### Expanded Config

To perform the other search types above, you need some of the content to be embedded. Simply add the embeddings workflow:

```yaml
workflows: [create_communities, create_community_reports, generate_text_embeddings]
```

### FastGraphRAG

[FastGraphRAG](./methods.md#fastgraphrag) uses text_units for the community reports instead of the entity and relationship descriptions. If your graph is sourced in such a way that it does not have descriptions, this might be a useful alternative. In this case, you would update your workflows list to include the text variant:

```yaml
workflows: [create_communities, create_community_reports_text, generate_text_embeddings]
```

This method requires that your entities and relationships tables have valid links to a list of text_unit_ids. Also note that `generate_text_embeddings` is still only required if you are doing searches other than Global Search.


## Setup

Putting it all together:

- `input`: GraphRAG does require an input document set, even if you don't need us to process it. You can create an input folder and drop a dummy.txt document in there to work around this.
- `output`: Create an output folder and put your entities and relationships (and optionally text_units) parquet files in it.
- Update your config as noted above to only run the workflows subset you need.
- Run `graphrag index --root <your project root>`