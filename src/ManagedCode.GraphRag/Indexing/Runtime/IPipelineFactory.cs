namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Builds pipelines that mirror the original Python workflow factory.
/// </summary>
public interface IPipelineFactory
{
    WorkflowPipeline BuildIndexingPipeline(IndexingPipelineDescriptor descriptor);

    WorkflowPipeline BuildQueryPipeline(QueryPipelineDescriptor descriptor);
}

public sealed record IndexingPipelineDescriptor(string Name, IReadOnlyList<string> Steps);

public sealed record QueryPipelineDescriptor(string Name, IReadOnlyList<string> Steps);
