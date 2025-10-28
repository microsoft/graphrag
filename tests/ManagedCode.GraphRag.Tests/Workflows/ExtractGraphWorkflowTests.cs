using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using GraphRag;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Entities;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Relationships;
using GraphRag.Storage;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Xunit;
using ManagedCode.GraphRag.Tests.Infrastructure;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class ExtractGraphWorkflowTests
{
    [Fact]
    public async Task ExtractGraphWorkflow_BuildsEntitiesAndRelationships()
    {
        const string payload =
@"{
  ""entities"": [
    { ""title"": ""Alice"", ""type"": ""person"", ""description"": ""Researcher"", ""confidence"": 0.9 },
    { ""title"": ""Bob"", ""type"": ""person"", ""description"": ""Engineer"", ""confidence"": 0.8 }
  ],
  ""relationships"": [
    { ""source"": ""Alice"", ""target"": ""Bob"", ""type"": ""collaborates_with"", ""description"": ""Works together"", ""weight"": 0.7, ""bidirectional"": true }
  ]
}";

        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory(_ => new ChatResponse(new ChatMessage(ChatRole.Assistant, payload))).CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();

        var outputStorage = new MemoryPipelineStorage();
        await outputStorage.WriteTableAsync(PipelineTableNames.TextUnits, new[]
        {
            new TextUnitRecord
            {
                Id = "unit-1",
                Text = "Alice collaborates with Bob on research.",
                TokenCount = 12,
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

        var workflow = ExtractGraphWorkflow.Create();
        await workflow(new GraphRagConfig(), context, CancellationToken.None);

        var entities = await outputStorage.LoadTableAsync<EntityRecord>(PipelineTableNames.Entities);
        Assert.Equal(2, entities.Count);
        Assert.Contains(entities, entity => entity.Title == "Alice" && entity.Description?.Contains("Researcher") == true);

        var relationships = await outputStorage.LoadTableAsync<RelationshipRecord>(PipelineTableNames.Relationships);
        var rel = Assert.Single(relationships);
        Assert.Equal("Alice", rel.Source);
        Assert.Equal("Bob", rel.Target);
        Assert.Equal("collaborates_with", rel.Type);
        Assert.True(rel.Bidirectional);
        Assert.Contains("unit-1", rel.TextUnitIds);
    }
}
