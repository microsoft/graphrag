using System.Collections.Immutable;
using BenchmarkDotNet.Attributes;
using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Entities;
using GraphRag.Relationships;

namespace ManagedCode.GraphRag.Benchmarks.Community;

[MemoryDiagnoser]
public class FastLabelPropagationBenchmarks
{
    private EntityRecord[] _smallGraphEntities = null!;
    private RelationshipRecord[] _smallGraphRelationships = null!;
    private EntityRecord[] _mediumGraphEntities = null!;
    private RelationshipRecord[] _mediumGraphRelationships = null!;
    private EntityRecord[] _largeGraphEntities = null!;
    private RelationshipRecord[] _largeGraphRelationships = null!;
    private ClusterGraphConfig _config = null!;

    [Params(10, 20, 40)]
    public int MaxIterations { get; set; }

    [GlobalSetup]
    public void Setup()
    {
        _config = new ClusterGraphConfig
        {
            Algorithm = CommunityDetectionAlgorithm.FastLabelPropagation,
            MaxIterations = MaxIterations,
            Seed = 42
        };

        // Small graph: 100 nodes, ~300 edges
        (_smallGraphEntities, _smallGraphRelationships) = GenerateGraph(100, 3);

        // Medium graph: 1,000 nodes, ~5,000 edges
        (_mediumGraphEntities, _mediumGraphRelationships) = GenerateGraph(1_000, 5);

        // Large graph: 10,000 nodes, ~50,000 edges
        (_largeGraphEntities, _largeGraphRelationships) = GenerateGraph(10_000, 5);
    }

    [Benchmark]
    public IReadOnlyDictionary<string, string> SmallGraph()
    {
        return FastLabelPropagationCommunityDetector.AssignLabels(
            _smallGraphEntities,
            _smallGraphRelationships,
            _config);
    }

    [Benchmark]
    public IReadOnlyDictionary<string, string> MediumGraph()
    {
        return FastLabelPropagationCommunityDetector.AssignLabels(
            _mediumGraphEntities,
            _mediumGraphRelationships,
            _config);
    }

    [Benchmark]
    public IReadOnlyDictionary<string, string> LargeGraph()
    {
        return FastLabelPropagationCommunityDetector.AssignLabels(
            _largeGraphEntities,
            _largeGraphRelationships,
            _config);
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
                TextUnitIds: ImmutableArray<string>.Empty,
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
                TextUnitIds: ImmutableArray<string>.Empty,
                Bidirectional: false));
        }

        return (entities, relationships.ToArray());
    }
}
