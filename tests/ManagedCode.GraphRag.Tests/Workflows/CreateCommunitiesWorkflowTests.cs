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
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class CreateCommunitiesWorkflowTests
{
    [Fact]
    public async Task RunWorkflow_GroupsEntitiesAndPersistsCommunities()
    {
        var outputStorage = new MemoryPipelineStorage();
        await outputStorage.WriteTableAsync(PipelineTableNames.Entities, new[]
        {
            new EntityRecord("entity-alice", 0, "Alice", "person", "Researcher", new[] { "unit-1" }.ToImmutableArray(), 3, 2, 0, 0),
            new EntityRecord("entity-bob", 1, "Bob", "person", "Policy expert", new[] { "unit-2" }.ToImmutableArray(), 2, 2, 0, 0),
            new EntityRecord("entity-carol", 2, "Carol", "person", "Analyst", new[] { "unit-3" }.ToImmutableArray(), 1, 1, 0, 0),
            new EntityRecord("entity-dave", 3, "Dave", "person", "Observer", new[] { "unit-4" }.ToImmutableArray(), 1, 0, 0, 0)
        });

        await outputStorage.WriteTableAsync(PipelineTableNames.Relationships, new[]
        {
            new RelationshipRecord("rel-1", 0, "Alice", "Bob", "collaborates_with", null, 0.8, 3, new[] { "unit-1", "unit-2" }.ToImmutableArray(), true),
            new RelationshipRecord("rel-2", 1, "Bob", "Carol", "mentors", null, 0.6, 3, new[] { "unit-3" }.ToImmutableArray(), false)
        });

        var context = new PipelineRunContext(
            inputStorage: new MemoryPipelineStorage(),
            outputStorage: outputStorage,
            previousStorage: new MemoryPipelineStorage(),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: new ServiceCollection().AddGraphRag().BuildServiceProvider());

        var workflow = CreateCommunitiesWorkflow.Create();
        var config = new GraphRagConfig
        {
            ClusterGraph = new ClusterGraphConfig
            {
                MaxClusterSize = 2,
                UseLargestConnectedComponent = false,
                Seed = 1337
            }
        };

        await workflow(config, context, CancellationToken.None);

        var communities = await outputStorage.LoadTableAsync<CommunityRecord>(PipelineTableNames.Communities);
        Assert.Equal(3, communities.Count);
        Assert.True(context.Items.TryGetValue("create_communities:count", out var countValue));
        Assert.Equal(3, Assert.IsType<int>(countValue));

        var communityByMembers = communities.ToDictionary(
            community => community.EntityIds.OrderBy(id => id).ToArray(),
            community => community,
            new SequenceComparer<string>());

        var aliceBob = communityByMembers[new[] { "entity-alice", "entity-bob" }];
        Assert.Equal(2, aliceBob.Size);
        Assert.Equal(aliceBob.CommunityId, aliceBob.HumanReadableId);
        Assert.Contains("rel-1", aliceBob.RelationshipIds);
        Assert.Contains("unit-1", aliceBob.TextUnitIds);
        Assert.Contains("unit-2", aliceBob.TextUnitIds);
        Assert.Equal(-1, aliceBob.ParentId);

        var carol = communityByMembers[new[] { "entity-carol" }];
        Assert.Empty(carol.RelationshipIds);
        Assert.Contains("unit-3", carol.TextUnitIds);

        var dave = communityByMembers[new[] { "entity-dave" }];
        Assert.Empty(dave.RelationshipIds);
        Assert.Contains("unit-4", dave.TextUnitIds);
    }

    private sealed class SequenceComparer<T> : IEqualityComparer<IReadOnlyList<T>> where T : notnull
    {
        public bool Equals(IReadOnlyList<T>? x, IReadOnlyList<T>? y)
        {
            if (x is null || y is null)
            {
                return x is null && y is null;
            }

            if (x.Count != y.Count)
            {
                return false;
            }

            for (var index = 0; index < x.Count; index++)
            {
                if (!EqualityComparer<T>.Default.Equals(x[index], y[index]))
                {
                    return false;
                }
            }

            return true;
        }

        public int GetHashCode(IReadOnlyList<T> obj)
        {
            var hash = new HashCode();
            foreach (var item in obj)
            {
                hash.Add(item);
            }

            return hash.ToHashCode();
        }
    }
}
