using GraphRag.Config;
using GraphRag.Entities;
using GraphRag.Relationships;

namespace GraphRag.Community;

internal static class FastLabelPropagationCommunityDetector
{
    public static IReadOnlyDictionary<string, string> AssignLabels(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships,
        ClusterGraphConfig config)
    {
        ArgumentNullException.ThrowIfNull(entities);
        ArgumentNullException.ThrowIfNull(relationships);
        ArgumentNullException.ThrowIfNull(config);

        var adjacency = BuildAdjacency(entities, relationships);
        if (adjacency.Count == 0)
        {
            return new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        }

        var random = new Random(config.Seed);
        var labels = adjacency.Keys.ToDictionary(node => node, node => node, StringComparer.OrdinalIgnoreCase);
        var nodes = adjacency.Keys.ToList();
        var maxIterations = Math.Max(1, config.MaxIterations);

        for (var iteration = 0; iteration < maxIterations; iteration++)
        {
            var shuffled = nodes.OrderBy(_ => random.Next()).ToList();
            var changed = false;

            foreach (var node in shuffled)
            {
                var neighbors = adjacency[node];
                if (neighbors.Count == 0)
                {
                    continue;
                }

                var labelWeights = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
                foreach (var (neighbor, weight) in neighbors)
                {
                    if (!labels.TryGetValue(neighbor, out var neighborLabel))
                    {
                        continue;
                    }

                    labelWeights[neighborLabel] = labelWeights.GetValueOrDefault(neighborLabel) + (weight > 0 ? weight : 1);
                }

                if (labelWeights.Count == 0)
                {
                    continue;
                }

                var maxWeight = labelWeights.Values.Max();
                var candidates = labelWeights
                    .Where(pair => Math.Abs(pair.Value - maxWeight) < 1e-6)
                    .Select(pair => pair.Key)
                    .ToList();

                var chosen = candidates.Count == 1
                    ? candidates[0]
                    : candidates[random.Next(candidates.Count)];

                if (!string.Equals(labels[node], chosen, StringComparison.OrdinalIgnoreCase))
                {
                    labels[node] = chosen;
                    changed = true;
                }
            }

            if (!changed)
            {
                break;
            }
        }

        return labels;
    }

    private static Dictionary<string, List<(string Neighbor, double Weight)>> BuildAdjacency(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships)
    {
        var adjacency = entities
            .ToDictionary(entity => entity.Title, _ => new List<(string, double)>(), StringComparer.OrdinalIgnoreCase);

        foreach (var relationship in relationships)
        {
            if (!adjacency.TryGetValue(relationship.Source, out var sourceNeighbors))
            {
                sourceNeighbors = new List<(string, double)>();
                adjacency[relationship.Source] = sourceNeighbors;
            }

            if (!adjacency.TryGetValue(relationship.Target, out var targetNeighbors))
            {
                targetNeighbors = new List<(string, double)>();
                adjacency[relationship.Target] = targetNeighbors;
            }

            sourceNeighbors.Add((relationship.Target, relationship.Weight));
            targetNeighbors.Add((relationship.Source, relationship.Weight));
        }

        return adjacency;
    }
}
