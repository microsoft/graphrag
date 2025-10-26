using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using GraphRag;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Storage;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class CreateFinalDocumentsWorkflowTests
{
    [Fact]
    public async Task RunWorkflow_AssignsTextUnitIds()
    {
        var services = new ServiceCollection().AddGraphRag().BuildServiceProvider();
        var outputStorage = new MemoryPipelineStorage();

        await outputStorage.WriteTableAsync("documents", new[]
        {
            new DocumentRecord
            {
                Id = "doc-1",
                Title = "Sample",
                Text = "Body",
                TextUnitIds = Array.Empty<string>()
            }
        });

        await outputStorage.WriteTableAsync("text_units", new[]
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
            cache: new InMemoryPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var workflow = CreateFinalDocumentsWorkflow.Create();
        await workflow(new GraphRagConfig(), context, CancellationToken.None);

        var documents = await outputStorage.LoadTableAsync<DocumentRecord>("documents");
        Assert.Single(documents);
        Assert.Contains("chunk-1", documents[0].TextUnitIds);
        Assert.Equal(0, documents[0].HumanReadableId);
    }
}
