using GraphRag;
using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class CreateFinalDocumentsWorkflowTests
{
    [Fact]
    public async Task RunWorkflow_AssignsTextUnitIds()
    {
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();
        var outputStorage = new MemoryPipelineStorage();

        await outputStorage.WriteTableAsync(PipelineTableNames.Documents, new[]
        {
            new DocumentRecord
            {
                Id = "doc-1",
                Title = "Sample",
                Text = "Body",
                TextUnitIds = Array.Empty<string>()
            }
        });

        await outputStorage.WriteTableAsync(PipelineTableNames.TextUnits, new[]
        {
            new TextUnitRecord
            {
                Id = "chunk-1",
                Text = "Body",
                TokenCount = 3,
                DocumentIds = new[] { "doc-1" },
                EntityIds = Array.Empty<string>(),
                RelationshipIds = Array.Empty<string>(),
                CovariateIds = Array.Empty<string>()
            }
        });

        var context = new PipelineRunContext(
            inputStorage: new MemoryPipelineStorage(),
            outputStorage: outputStorage,
            previousStorage: new MemoryPipelineStorage(),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var workflow = CreateFinalDocumentsWorkflow.Create();
        await workflow(new GraphRagConfig(), context, CancellationToken.None);

        var documents = await outputStorage.LoadTableAsync<DocumentRecord>(PipelineTableNames.Documents);
        Assert.Single(documents);
        Assert.Contains("chunk-1", documents[0].TextUnitIds);
        Assert.Equal(0, documents[0].HumanReadableId);
    }
}
