using GraphRag.Indexing.Workflows;

namespace GraphRag.Indexing.Runtime;

public static class IndexingPipelineDefinitions
{
    public static IndexingPipelineDescriptor Standard { get; } = new("standard", new[]
    {
        LoadInputDocumentsWorkflow.Name,
        CreateBaseTextUnitsWorkflow.Name,
        ExtractGraphWorkflow.Name,
        CreateCommunitiesWorkflow.Name,
        CommunitySummariesWorkflow.Name,
        CreateFinalDocumentsWorkflow.Name
    });
}
