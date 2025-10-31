using System.Collections.Immutable;
using GraphRag;
using GraphRag.Callbacks;
using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Entities;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Relationships;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

public sealed class HeuristicMaintenanceIntegrationTests : IDisposable
{
    private readonly string _rootDir;

    public HeuristicMaintenanceIntegrationTests()
    {
        _rootDir = Path.Combine(Path.GetTempPath(), "GraphRag", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_rootDir);
    }

    [Fact]
    public async Task HeuristicMaintenanceWorkflow_AppliesBudgetsAndSemanticDeduplication()
    {
        var outputDir = PrepareDirectory("output-maintenance");
        var inputDir = PrepareDirectory("input-maintenance");
        var previousDir = PrepareDirectory("previous-maintenance");

        var textUnits = new[]
        {
            new TextUnitRecord
            {
                Id = "a",
                Text = "Alpha Beta",
                TokenCount = 40,
                DocumentIds = new[] { "doc-1" },
                EntityIds = Array.Empty<string>(),
                RelationshipIds = Array.Empty<string>(),
                CovariateIds = Array.Empty<string>()
            },
            new TextUnitRecord
            {
                Id = "b",
                Text = "Gamma Delta",
                TokenCount = 30,
                DocumentIds = new[] { "doc-1" },
                EntityIds = Array.Empty<string>(),
                RelationshipIds = Array.Empty<string>(),
                CovariateIds = Array.Empty<string>()
            },
            new TextUnitRecord
            {
                Id = "c",
                Text = "Trim me",
                TokenCount = 30,
                DocumentIds = new[] { "doc-1" },
                EntityIds = Array.Empty<string>(),
                RelationshipIds = Array.Empty<string>(),
                CovariateIds = Array.Empty<string>()
            },
            new TextUnitRecord
            {
                Id = "d",
                Text = "Alpha Beta",
                TokenCount = 35,
                DocumentIds = new[] { "doc-2" },
                EntityIds = Array.Empty<string>(),
                RelationshipIds = Array.Empty<string>(),
                CovariateIds = Array.Empty<string>()
            }
        };

        var outputStorage = new FilePipelineStorage(outputDir);
        await outputStorage.WriteTableAsync(PipelineTableNames.TextUnits, textUnits);

        var embeddingVectors = new Dictionary<string, float[]>
        {
            ["Alpha Beta"] = new[] { 1f, 0f },
            ["Gamma Delta"] = new[] { 0f, 1f }
        };

        using var services = new ServiceCollection()
            .AddLogging()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddSingleton<IEmbeddingGenerator<string, Embedding<float>>>(new StubEmbeddingGenerator(embeddingVectors))
            .AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>("dedupe-model", (sp, _) => sp.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>())
            .AddGraphRag()
            .BuildServiceProvider();

        var config = new GraphRagConfig
        {
            Heuristics = new HeuristicMaintenanceConfig
            {
                MaxTokensPerTextUnit = 50,
                MaxDocumentTokenBudget = 80,
                EnableSemanticDeduplication = true,
                SemanticDeduplicationThreshold = 0.75,
                EmbeddingModelId = "dedupe-model"
            }
        };

        var context = new PipelineRunContext(
            inputStorage: new FilePipelineStorage(inputDir),
            outputStorage: outputStorage,
            previousStorage: new FilePipelineStorage(previousDir),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var workflow = HeuristicMaintenanceWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var processed = await outputStorage.LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits);
        Assert.Equal(2, processed.Count);

        var merged = Assert.Single(processed, unit => unit.Id == "a");
        Assert.Equal(2, merged.DocumentIds.Count);
        Assert.Contains("doc-1", merged.DocumentIds, StringComparer.OrdinalIgnoreCase);
        Assert.Contains("doc-2", merged.DocumentIds, StringComparer.OrdinalIgnoreCase);
        Assert.Equal(35, merged.TokenCount);

        var survivor = Assert.Single(processed, unit => unit.Id == "b");
        Assert.Single(survivor.DocumentIds);
        Assert.Equal("doc-1", survivor.DocumentIds[0]);
        Assert.DoesNotContain(processed, unit => unit.Id == "c");
        Assert.DoesNotContain(processed, unit => unit.Id == "d" && unit.DocumentIds.Count == 1);
    }

    [Fact]
    public async Task ExtractGraphWorkflow_LinksOrphansAndEnforcesRelationshipFloors()
    {
        var outputDir = PrepareDirectory("output-graph");
        var inputDir = PrepareDirectory("input-graph");
        var previousDir = PrepareDirectory("previous-graph");

        var outputStorage = new FilePipelineStorage(outputDir);
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
            },
            new TextUnitRecord
            {
                Id = "unit-2",
                Text = "Charlie and Alice planned a workshop.",
                TokenCount = 18,
                DocumentIds = new[] { "doc-1" },
                EntityIds = Array.Empty<string>(),
                RelationshipIds = Array.Empty<string>(),
                CovariateIds = Array.Empty<string>()
            }
        });

        var responses = new Queue<string>(new[]
        {
            "{\"entities\": [ { \"title\": \"Alice\", \"type\": \"person\", \"description\": \"Researcher\", \"confidence\": 0.9 }, { \"title\": \"Bob\", \"type\": \"person\", \"description\": \"Engineer\", \"confidence\": 0.6 } ], \"relationships\": [ { \"source\": \"Alice\", \"target\": \"Bob\", \"type\": \"collaborates\", \"description\": \"Works together\", \"weight\": 0.1, \"bidirectional\": false } ] }",
            "{\"entities\": [ { \"title\": \"Alice\", \"type\": \"person\", \"description\": \"Researcher\", \"confidence\": 0.8 }, { \"title\": \"Charlie\", \"type\": \"person\", \"description\": \"Analyst\", \"confidence\": 0.7 } ], \"relationships\": [] }"
        });

        using var services = new ServiceCollection()
            .AddLogging()
            .AddSingleton<IChatClient>(new TestChatClientFactory(_ =>
            {
                if (responses.Count == 0)
                {
                    throw new InvalidOperationException("No chat responses remaining.");
                }

                var payload = responses.Dequeue();
                return new ChatResponse(new ChatMessage(ChatRole.Assistant, payload));
            }).CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();

        var config = new GraphRagConfig
        {
            Heuristics = new HeuristicMaintenanceConfig
            {
                LinkOrphanEntities = true,
                OrphanLinkWeight = 0.5,
                MaxTextUnitsPerRelationship = 1,
                RelationshipConfidenceFloor = 0.4
            }
        };

        var context = new PipelineRunContext(
            inputStorage: new FilePipelineStorage(inputDir),
            outputStorage: outputStorage,
            previousStorage: new FilePipelineStorage(previousDir),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var workflow = ExtractGraphWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var relationships = await outputStorage.LoadTableAsync<RelationshipRecord>(PipelineTableNames.Relationships);
        Assert.Equal(2, relationships.Count);

        var direct = Assert.Single(relationships, rel => rel.Source == "Alice" && rel.Target == "Bob");
        Assert.Equal(0.4, direct.Weight, 3);
        Assert.Contains("unit-1", direct.TextUnitIds);
        Assert.False(direct.Bidirectional);

        var synthetic = Assert.Single(relationships, rel => rel.Source == "Charlie" && rel.Target == "Alice");
        Assert.True(synthetic.Bidirectional);
        Assert.Equal(0.5, synthetic.Weight, 3);
        var orphanUnit = Assert.Single(synthetic.TextUnitIds);
        Assert.Equal("unit-2", orphanUnit);

        var entities = await outputStorage.LoadTableAsync<EntityRecord>(PipelineTableNames.Entities);
        Assert.Equal(3, entities.Count);
        Assert.Contains(entities, entity => entity.Title == "Charlie");
    }

    [Fact]
    public async Task CreateCommunitiesWorkflow_UsesFastLabelPropagationAssignments()
    {
        var outputDir = PrepareDirectory("output-communities");
        var inputDir = PrepareDirectory("input-communities");
        var previousDir = PrepareDirectory("previous-communities");

        var outputStorage = new FilePipelineStorage(outputDir);

        var entities = new[]
        {
            new EntityRecord("entity-1", 0, "Alice", "Person", "Researcher", ImmutableArray.Create("unit-1"), 2, 2, 0, 0),
            new EntityRecord("entity-2", 1, "Bob", "Person", "Engineer", ImmutableArray.Create("unit-1"), 2, 2, 0, 0),
            new EntityRecord("entity-3", 2, "Charlie", "Person", "Analyst", ImmutableArray.Create("unit-2"), 2, 1, 0, 0),
            new EntityRecord("entity-4", 3, "Diana", "Person", "Strategist", ImmutableArray.Create("unit-3"), 2, 1, 0, 0),
            new EntityRecord("entity-5", 4, "Eve", "Person", "Planner", ImmutableArray.Create("unit-3"), 2, 1, 0, 0)
        };

        await outputStorage.WriteTableAsync(PipelineTableNames.Entities, entities);

        var relationships = new[]
        {
            new RelationshipRecord("rel-1", 0, "Alice", "Bob", "collaborates", "", 0.9, 2, ImmutableArray.Create("unit-1"), true),
            new RelationshipRecord("rel-2", 1, "Bob", "Charlie", "supports", "", 0.85, 2, ImmutableArray.Create("unit-2"), true),
            new RelationshipRecord("rel-3", 2, "Diana", "Eve", "partners", "", 0.95, 2, ImmutableArray.Create("unit-3"), true)
        };

        await outputStorage.WriteTableAsync(PipelineTableNames.Relationships, relationships);

        using var services = new ServiceCollection()
            .AddLogging()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();

        var config = new GraphRagConfig
        {
            ClusterGraph = new ClusterGraphConfig
            {
                Algorithm = CommunityDetectionAlgorithm.FastLabelPropagation,
                MaxIterations = 8,
                MaxClusterSize = 10,
                Seed = 13,
                UseLargestConnectedComponent = false
            }
        };

        var context = new PipelineRunContext(
            inputStorage: new FilePipelineStorage(inputDir),
            outputStorage: outputStorage,
            previousStorage: new FilePipelineStorage(previousDir),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var workflow = CreateCommunitiesWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var communities = await outputStorage.LoadTableAsync<CommunityRecord>(PipelineTableNames.Communities);
        Assert.Equal(2, communities.Count);
        Assert.Equal(communities.Count, Assert.IsType<int>(context.Items["create_communities:count"]));

        var titleLookup = entities.ToDictionary(entity => entity.Id, entity => entity.Title, StringComparer.OrdinalIgnoreCase);

        var members = communities
            .Select(community => community.EntityIds
                .Select(id => titleLookup[id])
                .OrderBy(title => title, StringComparer.OrdinalIgnoreCase)
                .ToArray())
            .ToList();

        Assert.Contains(members, group => group.SequenceEqual(new[] { "Alice", "Bob", "Charlie" }));
        Assert.Contains(members, group => group.SequenceEqual(new[] { "Diana", "Eve" }));
    }

    public void Dispose()
    {
        try
        {
            if (Directory.Exists(_rootDir))
            {
                Directory.Delete(_rootDir, recursive: true);
            }
        }
        catch
        {
            // Ignore cleanup errors in tests.
        }
    }

    private string PrepareDirectory(string name)
    {
        var path = Path.Combine(_rootDir, name);
        Directory.CreateDirectory(path);
        return path;
    }
}
