# Workflows
Workflows are a key concept in Indexing Engine. An individual workflow is a set of verbs/steps that are chained together to form a single output, see [verbs](../verbs/README.md) for an overview of what verbs do. Workflows are defined in a YAML file. The following is an totally made up example of a workflow:

```yaml
name: my_workflow # The name of the workflow
steps: # The list of steps / verbs to run
    - verb: text_replace
      args:
        column: text
        to: text
        replacements:
            - pattern: '(\d+)(\s+)(\d+)'
                replacement: '\1_\3'
    - verb: text_summarize
      args:
        column: text
        to: summary
```

## Predefined Workflows
Indexing Engine comes with a set of predefined workflows that can be used out of the box. These workflows are defined in the [workflows](../../indexing_engine/workflows) directory. These workflows can be referenced by name in the configuration file.

For example:
```yaml
workflows:
    - name: entity_graph
      config:
        ...The config for the entity_graph workflow...
```

The following is a list of the predefined workflows:

> Note: These are currently defined using python, but the plan is to move these to YAML files. It is purely done as a way to enable workflow configuration.

- [entity_graph](../../indexing_engine/workflows/entity_graph.py): This workflow will create a graph of entities from the input data.
- [entity_extraction](../../indexing_engine/workflows/entity_extraction.py): This workflow will extract entities from the input data.

### Old Workflows
- [create_final_entities](../indexing_engine/workflows/v1/create_final_entities.py): This workflow will create a list of entities from the input data.
- [create_final_nodes](../indexing_engine/workflows/v1/create_final_nodes.py): This workflow will create a list of positioned and clustered entity nodes from the input data.
