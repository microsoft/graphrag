using System.Collections.Immutable;
using GraphRag.Entities;
using GraphRag.Relationships;

namespace GraphRag.Finalization;

/// <summary>
/// Provides utilities for transforming raw entity/relationship rows into the canonical
/// shape expected by downstream consumers. The behaviour mirrors the Python-based
/// <c>finalize_graph</c> workflow but operates on lightweight in-memory objects.
/// </summary>
public static class GraphFinalizer
{
    public static GraphFinalizationResult Finalize(
        IEnumerable<EntitySeed> entitySeeds,
        IEnumerable<RelationshipSeed> relationshipSeeds,
        GraphFinalizerOptions? options = null)
    {
        ArgumentNullException.ThrowIfNull(entitySeeds);
        ArgumentNullException.ThrowIfNull(relationshipSeeds);

        options ??= GraphFinalizerOptions.Default;

        var entityList = entitySeeds.ToList();
        var relationshipList = relationshipSeeds.ToList();

        // Pre-compute node degrees (undirected graph semantics, mirroring NetworkX behaviour)
        var degrees = ComputeDegrees(entityList.Select(e => e.Title), relationshipList);

        // Determine layout points
        var positions = options.LayoutEnabled
            ? ComputeCircularLayout(entityList.Select(e => e.Title))
            : CreateZeroLayout(entityList.Select(e => e.Title));

        var entities = entityList
            .Select((seed, index) =>
            {
                var degree = degrees.TryGetValue(seed.Title, out var value) ? value : 0;
                var position = positions.TryGetValue(seed.Title, out var pos) ? pos : (0d, 0d);
                var (x, y) = position;

                return new EntityRecord(
                    Id: Guid.NewGuid().ToString(),
                    HumanReadableId: index,
                    Title: seed.Title,
                    Type: seed.Type,
                    Description: seed.Description,
                    TextUnitIds: seed.TextUnitIds.ToImmutableArray(),
                    Frequency: seed.Frequency,
                    Degree: degree,
                    X: x,
                    Y: y);
            })
            .ToList();

        var relationships = relationshipList
            .Select((seed, index) =>
            {
                var sourceDegree = degrees.TryGetValue(seed.Source, out var sd) ? sd : 0;
                var targetDegree = degrees.TryGetValue(seed.Target, out var td) ? td : 0;
                var combinedDegree = sourceDegree + targetDegree;

                return new RelationshipRecord(
                    Id: Guid.NewGuid().ToString(),
                    HumanReadableId: index,
                    Source: seed.Source,
                    Target: seed.Target,
                    Description: seed.Description,
                    Weight: seed.Weight,
                    CombinedDegree: combinedDegree,
                    TextUnitIds: seed.TextUnitIds.ToImmutableArray());
            })
            .ToList();

        return new GraphFinalizationResult(entities, relationships);
    }

    private static IReadOnlyDictionary<string, int> ComputeDegrees(
        IEnumerable<string> titles,
        IReadOnlyList<RelationshipSeed> relationships)
    {
        var degrees = titles.Distinct(StringComparer.OrdinalIgnoreCase)
            .ToDictionary(title => title, _ => 0, StringComparer.OrdinalIgnoreCase);

        foreach (var relationship in relationships)
        {
            if (!degrees.ContainsKey(relationship.Source))
            {
                degrees[relationship.Source] = 0;
            }

            if (!degrees.ContainsKey(relationship.Target))
            {
                degrees[relationship.Target] = 0;
            }

            degrees[relationship.Source]++;
            degrees[relationship.Target]++;
        }

        return degrees;
    }

    private static Dictionary<string, (double x, double y)> CreateZeroLayout(IEnumerable<string> titles)
    {
        return titles.Distinct(StringComparer.OrdinalIgnoreCase)
            .ToDictionary(title => title, _ => (0d, 0d), StringComparer.OrdinalIgnoreCase);
    }

    private static Dictionary<string, (double x, double y)> ComputeCircularLayout(IEnumerable<string> titles)
    {
        var uniqueTitles = titles.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        var layout = new Dictionary<string, (double x, double y)>(StringComparer.OrdinalIgnoreCase);

        if (uniqueTitles.Count == 0)
        {
            return layout;
        }

        var radius = Math.Max(1, uniqueTitles.Count / 2.0);
        for (var index = 0; index < uniqueTitles.Count; index++)
        {
            var angle = (2 * Math.PI * index) / uniqueTitles.Count;
            var x = radius * Math.Cos(angle);
            var y = radius * Math.Sin(angle);
            layout[uniqueTitles[index]] = (x, y);
        }

        return layout;
    }
}

public sealed record GraphFinalizerOptions(bool LayoutEnabled)
{
    public static GraphFinalizerOptions Default { get; } = new(false);
}

public sealed record GraphFinalizationResult(
    IReadOnlyList<EntityRecord> Entities,
    IReadOnlyList<RelationshipRecord> Relationships);
