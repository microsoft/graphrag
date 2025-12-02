using System.Collections.Immutable;
using BenchmarkDotNet.Attributes;
using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Entities;
using GraphRag.Relationships;

namespace ManagedCode.GraphRag.Benchmarks.Community;

[MemoryDiagnoser]
public class CommunityBuilderBenchmarks
{
    private EntityRecord[] _entities = null!;
    private RelationshipRecord[] _relationships = null!;
    private ClusterGraphConfig _labelPropagationConfig = null!;
    private ClusterGraphConfig _connectedComponentsConfig = null!;

    [Params(100, 1_000, 5_000)]
    public int NodeCount { get; set; }

    [GlobalSetup]
    public void Setup()
    {
        _labelPropagationConfig = new ClusterGraphConfig
        {
            Algorithm = CommunityDetectionAlgorithm.FastLabelPropagation,
            MaxIterations = 20,
            MaxClusterSize = 25,
            Seed = 42
        };

        _connectedComponentsConfig = new ClusterGraphConfig
        {
            Algorithm = CommunityDetectionAlgorithm.ConnectedComponents,
            MaxClusterSize = 25,
            Seed = 42
        };

        (_entities, _relationships) = GenerateGraph(NodeCount, avgEdgesPerNode: 5);
    }

    [Benchmark(Baseline = true)]
    public IReadOnlyList<CommunityRecord> FastLabelPropagation()
    {
        return CommunityBuilder.Build(_entities, _relationships, _labelPropagationConfig);
    }

    [Benchmark]
    public IReadOnlyList<CommunityRecord> ConnectedComponents()
    {
        return CommunityBuilder.Build(_entities, _relationships, _connectedComponentsConfig);
    }

    private static (EntityRecord[] Entities, RelationshipRecord[] Relationships) GenerateGraph(
        int nodeCount,
        int avgEdgesPerNode)
    {
        var random = new Random(42);
        var entities = new EntityRecord[nodeCount];

        for (var i = 0; i < nodeCount; i++)
        {
            entities[i] = new EntityRecord(
                Id: $"entity-{i}",
                HumanReadableId: i,
                Title: $"Entity_{i}",
                Type: "ENTITY",
                Description: $"Description for entity {i}",
                TextUnitIds: ImmutableArray.Create($"tu-{i}"),
                Frequency: 1,
                Degree: 0,
                X: 0,
                Y: 0);
        }

        var totalEdges = nodeCount * avgEdgesPerNode;
        var relationships = new List<RelationshipRecord>(totalEdges);

        for (var i = 0; i < totalEdges; i++)
        {
            var sourceIdx = random.Next(nodeCount);
            var targetIdx = random.Next(nodeCount);

            if (sourceIdx == targetIdx)
            {
                targetIdx = (targetIdx + 1) % nodeCount;
            }

            relationships.Add(new RelationshipRecord(
                Id: $"rel-{i}",
                HumanReadableId: i,
                Source: entities[sourceIdx].Title,
                Target: entities[targetIdx].Title,
                Type: "RELATED_TO",
                Description: null,
                Weight: random.NextDouble(),
                CombinedDegree: 2,
                TextUnitIds: ImmutableArray.Create($"tu-{sourceIdx}", $"tu-{targetIdx}"),
                Bidirectional: false));
        }

        return (entities, relationships.ToArray());
    }
}
