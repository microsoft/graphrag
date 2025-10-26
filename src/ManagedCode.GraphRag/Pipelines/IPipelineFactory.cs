namespace GraphRag.Pipelines;

/// <summary>
/// Builds pipelines that mirror the original Python workflow factory.
/// </summary>
public interface IPipelineFactory
{
    IPipeline BuildIndexingPipeline(IndexingPipelineDescriptor descriptor);

    IPipeline BuildQueryPipeline(QueryPipelineDescriptor descriptor);
}

public sealed record IndexingPipelineDescriptor(string Name, IReadOnlyList<string> Steps);

public sealed record QueryPipelineDescriptor(string Name, IReadOnlyList<string> Steps);
