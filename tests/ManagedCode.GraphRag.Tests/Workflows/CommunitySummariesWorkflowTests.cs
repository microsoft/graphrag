using System.Collections.Immutable;
using GraphRag;
using GraphRag.Callbacks;
using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Entities;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Relationships;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class CommunitySummariesWorkflowTests
{
    [Fact]
    public async Task CommunitySummariesWorkflow_GeneratesReports()
    {
        const string summaryPayload = "Research figures collaborate on AI safety initiatives.";

        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory(_ => new ChatResponse(new ChatMessage(ChatRole.Assistant, summaryPayload))).CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();

        var outputStorage = new MemoryPipelineStorage();
        await outputStorage.WriteTableAsync(PipelineTableNames.Entities, new[]
        {
            new EntityRecord("entity-1", 0, "Alice", "Person", "AI researcher", new[] { "unit-1" }.ToImmutableArray(), 2, 1, 0, 0),
            new EntityRecord("entity-2", 1, "Bob", "Person", "Policy expert", new[] { "unit-2" }.ToImmutableArray(), 1, 1, 0, 0)
        });

        await outputStorage.WriteTableAsync(PipelineTableNames.Relationships, new[]
        {
            new RelationshipRecord("rel-1", 0, "Alice", "Bob", "collaborates_with", "Joint projects", 0.8, 2, new[] { "unit-1" }.ToImmutableArray(), true)
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

        var config = new GraphRagConfig();

        var createCommunities = CreateCommunitiesWorkflow.Create();
        await createCommunities(config, context, CancellationToken.None);

        var workflow = CommunitySummariesWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var reports = await outputStorage.LoadTableAsync<CommunityReportRecord>(PipelineTableNames.CommunityReports);
        var report = Assert.Single(reports);
        Assert.Equal("community_1", report.CommunityId);
        Assert.Contains("Alice", report.EntityTitles);
        Assert.Contains("Bob", report.EntityTitles);
        Assert.Equal(summaryPayload, report.Summary);
    }
}
