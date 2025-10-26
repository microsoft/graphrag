using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using GraphRag;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Chunking;
using GraphRag.Config;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Logging;
using GraphRag.Storage;
using GraphRag.Tokenization;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class CreateBaseTextUnitsWorkflowTests
{
    [Fact]
    public async Task RunWorkflow_PrependsMetadata_WhenConfigured()
    {
        var services = new ServiceCollection().AddGraphRag().BuildServiceProvider();
        var outputStorage = new MemoryPipelineStorage();
        await outputStorage.WriteTableAsync("documents", new[]
        {
            new DocumentRecord
            {
                Id = "doc-1",
                Title = "Sample",
                Text = "Alice met Bob at the conference and shared insights.",
                Metadata = new Dictionary<string, object?>
                {
                    ["author"] = "Alice",
                    ["category"] = "meeting"
                }
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

        var config = new GraphRagConfig
        {
            Chunks = new ChunkingConfig
            {
                Size = 25,
                Overlap = 5,
                EncodingModel = "o200k_base",
                PrependMetadata = true,
                ChunkSizeIncludesMetadata = true
            }
        };

        var workflow = CreateBaseTextUnitsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var textUnits = await outputStorage.LoadTableAsync<TextUnitRecord>("text_units");
        Assert.NotEmpty(textUnits);
        Assert.All(textUnits, unit => Assert.Contains("author:", unit.Text));
        Assert.All(textUnits, unit => Assert.Contains("doc-1", unit.DocumentIds));
        Assert.Equal(1, context.Stats.NumDocuments);
    }
}
