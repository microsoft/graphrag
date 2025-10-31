using System.Collections.Immutable;
using System.Globalization;
using GraphRag.Config;
using GraphRag.Entities;
using GraphRag.Relationships;

namespace GraphRag.Community;

internal static class CommunityBuilder
{
    public static IReadOnlyList<CommunityRecord> Build(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships,
        ClusterGraphConfig? config)
    {
        ArgumentNullException.ThrowIfNull(entities);
        ArgumentNullException.ThrowIfNull(relationships);

        config ??= new ClusterGraphConfig();

        if (entities.Count == 0)
        {
            return Array.Empty<CommunityRecord>();
        }

        var titleLookup = entities.ToDictionary(entity => entity.Title, StringComparer.OrdinalIgnoreCase);
        var components = config.Algorithm switch
        {
            CommunityDetectionAlgorithm.FastLabelPropagation => BuildUsingLabelPropagation(entities, relationships, config),
            _ => BuildUsingConnectedComponents(entities, relationships, config)
        };

        if (config.UseLargestConnectedComponent && components.Count > 0)
        {
            var largestSize = components.Max(component => component.Count);
            components = components
                .Where(component => component.Count == largestSize)
                .Take(1)
                .ToList();
        }

        var clusters = components
            .SelectMany(component => SplitComponent(component, config.MaxClusterSize))
            .ToList();

        if (clusters.Count == 0)
        {
            return Array.Empty<CommunityRecord>();
        }

        var period = DateTime.UtcNow.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        var communityRecords = new List<CommunityRecord>(clusters.Count);
        var relationshipLookup = relationships.ToList();

        var communityIndex = 0;
        foreach (var cluster in clusters)
        {
            var memberTitles = cluster
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .Where(titleLookup.ContainsKey)
                .ToList();

            if (memberTitles.Count == 0)
            {
                continue;
            }

            var members = memberTitles
                .Select(title => titleLookup[title])
                .OrderBy(entity => entity.HumanReadableId)
                .ToList();

            if (members.Count == 0)
            {
                continue;
            }

            communityIndex++;
            var communityId = communityIndex;

            var entityIds = members
                .Select(member => member.Id)
                .ToImmutableArray();

            var membership = new HashSet<string>(memberTitles, StringComparer.OrdinalIgnoreCase);
            var relationshipIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var textUnitIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

            foreach (var relationship in relationshipLookup)
            {
                if (!membership.Contains(relationship.Source) || !membership.Contains(relationship.Target))
                {
                    continue;
                }

                relationshipIds.Add(relationship.Id);

                foreach (var textUnitId in relationship.TextUnitIds)
                {
                    if (!string.IsNullOrWhiteSpace(textUnitId))
                    {
                        textUnitIds.Add(textUnitId);
                    }
                }
            }

            if (textUnitIds.Count == 0)
            {
                foreach (var member in members)
                {
                    foreach (var textUnitId in member.TextUnitIds)
                    {
                        if (!string.IsNullOrWhiteSpace(textUnitId))
                        {
                            textUnitIds.Add(textUnitId);
                        }
                    }
                }
            }

            var record = new CommunityRecord(
                Id: Guid.NewGuid().ToString(),
                HumanReadableId: communityId,
                CommunityId: communityId,
                Level: 0,
                ParentId: -1,
                Children: ImmutableArray<int>.Empty,
                Title: $"Community {communityId}",
                EntityIds: entityIds,
                RelationshipIds: relationshipIds
                    .OrderBy(id => id, StringComparer.Ordinal)
                    .ToImmutableArray(),
                TextUnitIds: textUnitIds
                    .OrderBy(id => id, StringComparer.Ordinal)
                    .ToImmutableArray(),
                Period: period,
                Size: members.Count);

            communityRecords.Add(record);
        }

        return communityRecords;
    }

    private static List<List<string>> BuildUsingConnectedComponents(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships,
        ClusterGraphConfig config)
    {
        var adjacency = BuildAdjacency(entities, relationships);
        var random = new Random(config.Seed);
        var orderedTitles = adjacency.Keys
            .OrderBy(_ => random.Next())
            .ToList();

        var visited = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var components = new List<List<string>>();

        foreach (var title in orderedTitles)
        {
            if (!visited.Add(title))
            {
                continue;
            }

            var component = new List<string>();
            var queue = new Queue<string>();
            queue.Enqueue(title);

            while (queue.Count > 0)
            {
                var current = queue.Dequeue();
                component.Add(current);

                if (!adjacency.TryGetValue(current, out var neighbors) || neighbors.Count == 0)
                {
                    continue;
                }

                var orderedNeighbors = neighbors
                    .OrderBy(_ => random.Next())
                    .ToList();

                foreach (var neighbor in orderedNeighbors.Where(visited.Add))
                {
                    queue.Enqueue(neighbor);
                }
            }

            components.Add(component);
        }

        return components;
    }

    private static List<List<string>> BuildUsingLabelPropagation(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships,
        ClusterGraphConfig config)
    {
        var assignments = FastLabelPropagationCommunityDetector.AssignLabels(entities, relationships, config);
        if (assignments.Count == 0)
        {
            return new List<List<string>>();
        }

        var groups = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);

        foreach (var pair in assignments)
        {
            if (!groups.TryGetValue(pair.Value, out var members))
            {
                members = new List<string>();
                groups[pair.Value] = members;
            }

            members.Add(pair.Key);
        }

        return groups.Values
            .Select(list => list
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .OrderBy(title => title, StringComparer.OrdinalIgnoreCase)
                .ToList())
            .Where(list => list.Count > 0)
            .ToList();
    }

    private static Dictionary<string, HashSet<string>> BuildAdjacency(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships)
    {
        var adjacency = new Dictionary<string, HashSet<string>>(StringComparer.OrdinalIgnoreCase);

        foreach (var entity in entities)
        {
            adjacency.TryAdd(entity.Title, new HashSet<string>(StringComparer.OrdinalIgnoreCase));
        }

        foreach (var relationship in relationships)
        {
            if (!adjacency.TryGetValue(relationship.Source, out var sourceNeighbors))
            {
                sourceNeighbors = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                adjacency[relationship.Source] = sourceNeighbors;
            }

            if (!adjacency.TryGetValue(relationship.Target, out var targetNeighbors))
            {
                targetNeighbors = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                adjacency[relationship.Target] = targetNeighbors;
            }

            sourceNeighbors.Add(relationship.Target);
            targetNeighbors.Add(relationship.Source);
        }

        return adjacency;
    }

    private static IEnumerable<List<string>> SplitComponent(List<string> component, int maxClusterSize)
    {
        if (component.Count == 0)
        {
            yield break;
        }

        if (maxClusterSize <= 0 || component.Count <= maxClusterSize)
        {
            yield return component;
            yield break;
        }

        for (var index = 0; index < component.Count; index += maxClusterSize)
        {
            var length = Math.Min(maxClusterSize, component.Count - index);
            yield return component.GetRange(index, length);
        }
    }
}
