using GraphRag.Config;
using GraphRag.Data;
using GraphRag.Entities;
using GraphRag.Relationships;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Heuristics;

internal static class GraphExtractionHeuristics
{
    public static (IReadOnlyList<EntitySeed> Entities, IReadOnlyList<RelationshipSeed> Relationships) Apply(
        IReadOnlyList<EntitySeed> entities,
        IReadOnlyList<RelationshipSeed> relationships,
        IReadOnlyList<TextUnitRecord> textUnits,
        HeuristicMaintenanceConfig heuristics,
        ILogger? logger)
    {
        if (entities.Count == 0)
        {
            return (entities, relationships);
        }

        var enhancedRelationships = heuristics.EnhanceRelationships
            ? EnhanceRelationships(relationships, heuristics)
            : relationships.ToList();

        if (heuristics.LinkOrphanEntities)
        {
            enhancedRelationships = LinkOrphanEntities(entities, enhancedRelationships, textUnits, heuristics, logger);
        }

        return (entities, enhancedRelationships);
    }

    private static List<RelationshipSeed> EnhanceRelationships(
        IReadOnlyList<RelationshipSeed> relationships,
        HeuristicMaintenanceConfig heuristics)
    {
        if (relationships.Count == 0)
        {
            return new List<RelationshipSeed>();
        }

        var aggregator = new Dictionary<string, RelationshipAggregation>(StringComparer.OrdinalIgnoreCase);

        foreach (var relationship in relationships)
        {
            var key = BuildRelationshipKey(relationship.Source, relationship.Target, relationship.Type, relationship.Bidirectional);
            if (!aggregator.TryGetValue(key, out var aggregation))
            {
                aggregation = new RelationshipAggregation(relationship.Source, relationship.Target, relationship.Type, relationship.Bidirectional);
                aggregator[key] = aggregation;
            }

            aggregation.Add(relationship);
        }

        return aggregator.Values
            .Select(aggregation => aggregation.ToSeed(heuristics))
            .OrderBy(seed => seed.Source, StringComparer.OrdinalIgnoreCase)
            .ThenBy(seed => seed.Target, StringComparer.OrdinalIgnoreCase)
            .ThenBy(seed => seed.Type, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    private static List<RelationshipSeed> LinkOrphanEntities(
        IReadOnlyList<EntitySeed> entities,
        IReadOnlyList<RelationshipSeed> relationships,
        IReadOnlyList<TextUnitRecord> textUnits,
        HeuristicMaintenanceConfig heuristics,
        ILogger? logger)
    {
        var relationshipMap = new Dictionary<string, HashSet<string>>(StringComparer.OrdinalIgnoreCase);
        var textUnitIndex = textUnits
            .GroupBy(unit => unit.Id, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.OrdinalIgnoreCase);

        foreach (var relationship in relationships)
        {
            Register(relationship.Source, relationship.Target);
            Register(relationship.Target, relationship.Source);
        }

        var textUnitLookup = entities
            .ToDictionary(entity => entity.Title, entity => new HashSet<string>(entity.TextUnitIds, StringComparer.OrdinalIgnoreCase), StringComparer.OrdinalIgnoreCase);

        var orphanEntities = entities
            .Where(entity => !relationshipMap.TryGetValue(entity.Title, out var edges) || edges.Count == 0)
            .ToList();

        if (orphanEntities.Count == 0)
        {
            return relationships.ToList();
        }

        var updatedRelationships = relationships.ToList();
        var existingKeys = new HashSet<string>(updatedRelationships
            .Select(rel => BuildRelationshipKey(rel.Source, rel.Target, rel.Type, rel.Bidirectional)), StringComparer.OrdinalIgnoreCase);

        foreach (var orphan in orphanEntities)
        {
            if (!textUnitLookup.TryGetValue(orphan.Title, out var orphanUnits) || orphanUnits.Count == 0)
            {
                continue;
            }

            EntitySeed? bestMatch = null;
            double bestScore = 0;

            foreach (var candidate in entities)
            {
                if (string.Equals(candidate.Title, orphan.Title, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                if (!textUnitLookup.TryGetValue(candidate.Title, out var candidateUnits) || candidateUnits.Count == 0)
                {
                    continue;
                }

                var overlap = orphanUnits.Intersect(candidateUnits, StringComparer.OrdinalIgnoreCase).Count();
                if (overlap == 0)
                {
                    continue;
                }

                var overlapRatio = overlap / (double)Math.Min(orphanUnits.Count, candidateUnits.Count);
                if (overlapRatio < heuristics.OrphanLinkMinimumOverlap)
                {
                    continue;
                }

                if (overlapRatio > bestScore)
                {
                    bestScore = overlapRatio;
                    bestMatch = candidate;
                }
            }

            if (bestMatch is null)
            {
                continue;
            }

            var sharedUnits = orphanUnits.Intersect(textUnitLookup[bestMatch.Title], StringComparer.OrdinalIgnoreCase)
                .Select(id => (Id: id, Tokens: textUnitIndex.TryGetValue(id, out var record) ? record.TokenCount : 0))
                .OrderByDescending(tuple => tuple.Tokens)
                .Select(tuple => tuple.Id)
                .Take(heuristics.MaxTextUnitsPerRelationship > 0 ? heuristics.MaxTextUnitsPerRelationship : int.MaxValue)
                .ToArray();

            var fallbackUnits = orphanUnits
                .Select(id => (Id: id, Tokens: textUnitIndex.TryGetValue(id, out var record) ? record.TokenCount : 0))
                .OrderByDescending(tuple => tuple.Tokens)
                .Select(tuple => tuple.Id)
                .Take(heuristics.MaxTextUnitsPerRelationship > 0 ? heuristics.MaxTextUnitsPerRelationship : orphanUnits.Count)
                .ToArray();

            var synthetic = new RelationshipSeed(
                orphan.Title,
                bestMatch.Title,
                $"{orphan.Title} relates to {bestMatch.Title}",
                heuristics.OrphanLinkWeight,
                sharedUnits.Length > 0 ? sharedUnits : fallbackUnits)
            {
                Bidirectional = true
            };

            var key = BuildRelationshipKey(synthetic.Source, synthetic.Target, synthetic.Type, synthetic.Bidirectional);
            if (existingKeys.Add(key))
            {
                updatedRelationships.Add(synthetic);
                Register(synthetic.Source, synthetic.Target);
                Register(synthetic.Target, synthetic.Source);
                logger?.LogDebug(
                    "Linked orphan entity {Orphan} with {Target} using {Overlap} shared text units.",
                    orphan.Title,
                    bestMatch.Title,
                    sharedUnits.Length);
            }
        }

        return updatedRelationships;

        void Register(string source, string target)
        {
            if (string.IsNullOrWhiteSpace(source) || string.IsNullOrWhiteSpace(target))
            {
                return;
            }

            if (!relationshipMap.TryGetValue(source, out var neighbors))
            {
                neighbors = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                relationshipMap[source] = neighbors;
            }

            neighbors.Add(target);
        }
    }

    private static string BuildRelationshipKey(string source, string target, string? type, bool bidirectional)
    {
        var relationshipType = string.IsNullOrWhiteSpace(type) ? "related_to" : type;
        if (bidirectional && string.Compare(source, target, StringComparison.OrdinalIgnoreCase) > 0)
        {
            (source, target) = (target, source);
        }

        return $"{source}::{target}::{relationshipType}";
    }

    private sealed class RelationshipAggregation(string source, string target, string? type, bool bidirectional)
    {
        private readonly string _source = source;
        private readonly string _target = target;
        private readonly string _type = string.IsNullOrWhiteSpace(type) ? "related_to" : type!;
        private readonly bool _bidirectional = bidirectional;
        private readonly HashSet<string> _textUnits = new(StringComparer.OrdinalIgnoreCase);

        private double _weightSum;
        private int _count;
        private string? _description;

        public void Add(RelationshipSeed seed)
        {
            _weightSum += seed.Weight;
            _count++;
            _description = SelectDescription(_description, seed.Description);

            foreach (var textUnit in seed.TextUnitIds)
            {
                if (!string.IsNullOrWhiteSpace(textUnit))
                {
                    _textUnits.Add(textUnit);
                }
            }
        }

        public RelationshipSeed ToSeed(HeuristicMaintenanceConfig heuristics)
        {
            var weight = _count > 0 ? _weightSum / _count : heuristics.RelationshipConfidenceFloor;
            if (weight < heuristics.RelationshipConfidenceFloor)
            {
                weight = heuristics.RelationshipConfidenceFloor;
            }

            var textUnits = _textUnits
                .OrderBy(id => id, StringComparer.OrdinalIgnoreCase)
                .ToList();

            if (heuristics.MaxTextUnitsPerRelationship > 0 && textUnits.Count > heuristics.MaxTextUnitsPerRelationship)
            {
                textUnits = textUnits.Take(heuristics.MaxTextUnitsPerRelationship).ToList();
            }

            return new RelationshipSeed(
                _source,
                _target,
                _description ?? $"{_source} relates to {_target}",
                weight,
                textUnits)
            {
                Type = _type,
                Bidirectional = _bidirectional
            };
        }

        private static string? SelectDescription(string? existing, string? incoming)
        {
            if (string.IsNullOrWhiteSpace(incoming))
            {
                return existing;
            }

            if (string.IsNullOrWhiteSpace(existing))
            {
                return incoming;
            }

            return incoming.Length < existing.Length ? incoming : existing;
        }
    }
}
