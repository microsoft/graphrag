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

public sealed class CreateBaseTextUnitsWorkflowTests
{
    [Fact]
    public async Task RunWorkflow_PrependsMetadata_WhenConfigured()
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
            cache: new StubPipelineCache(),
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
                EncodingModel = TokenizerDefaults.DefaultEncoding,
                PrependMetadata = true,
                ChunkSizeIncludesMetadata = true
            }
        };

        var workflow = CreateBaseTextUnitsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var textUnits = await outputStorage.LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits);
        Assert.NotEmpty(textUnits);
        Assert.All(textUnits, unit => Assert.Contains("author:", unit.Text));
        Assert.All(textUnits, unit => Assert.Contains("doc-1", unit.DocumentIds));
        Assert.Equal(1, context.Stats.NumDocuments);
    }

    [Fact]
    public async Task RunWorkflow_ThrowsWhenMetadataExceedsChunkBudget()
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
                Id = "doc-2",
                Title = "Overflowing Metadata",
                Text = "Body content remains concise.",
                Metadata = new Dictionary<string, object?>
                {
                    ["notes"] = new string('x', 600)
                }
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

        var config = new GraphRagConfig
        {
            Chunks = new ChunkingConfig
            {
                Size = 15,
                Overlap = 0,
                EncodingModel = TokenizerDefaults.DefaultModel,
                PrependMetadata = true,
                ChunkSizeIncludesMetadata = true
            }
        };

        var workflow = CreateBaseTextUnitsWorkflow.Create();
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
        {
            await workflow(config, context, CancellationToken.None);
        });
    }

    [Fact]
    public async Task RunWorkflow_GeneratesStableTextUnitIds()
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
                Id = "doc-3",
                Title = "Stability",
                Text = string.Join(' ', Enumerable.Repeat("Deterministic hashing verifies repeated runs.", 8)),
                Metadata = new Dictionary<string, object?>()
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

        var config = new GraphRagConfig
        {
            Chunks = new ChunkingConfig
            {
                Size = 60,
                Overlap = 10,
                EncodingModel = "gpt-4",
                PrependMetadata = false,
                ChunkSizeIncludesMetadata = false
            }
        };

        var workflow = CreateBaseTextUnitsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);
        var first = await outputStorage.LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits);

        await workflow(config, context, CancellationToken.None);
        var second = await outputStorage.LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits);

        Assert.Equal(first.Count, second.Count);
        var firstIds = first.Select(unit => unit.Id).OrderBy(id => id, StringComparer.Ordinal).ToArray();
        var secondIds = second.Select(unit => unit.Id).OrderBy(id => id, StringComparer.Ordinal).ToArray();
        Assert.Equal(firstIds, secondIds);
    }
}
