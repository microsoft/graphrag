using GraphRag.Indexing.Workflows;

namespace GraphRag.Indexing.Runtime;

public static class IndexingPipelineDefinitions
{
    public static IndexingPipelineDescriptor Standard { get; } = new("standard", new[]
    {
        CreateBaseTextUnitsWorkflow.Name
    });
}
