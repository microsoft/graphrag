using GraphRag.Config;
using GraphRag.Data;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Heuristics;

internal static class TextUnitHeuristicProcessor
{
    public static async Task<IReadOnlyList<TextUnitRecord>> ApplyAsync(
        GraphRagConfig config,
        IReadOnlyList<TextUnitRecord> textUnits,
        IServiceProvider services,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        if (textUnits.Count == 0)
        {
            return Array.Empty<TextUnitRecord>();
        }

        var heuristics = config.Heuristics ?? new HeuristicMaintenanceConfig();

        var filtered = ApplyTokenBudgets(textUnits, heuristics);
        if (filtered.Count == 0)
        {
            return filtered;
        }

        if (!heuristics.EnableSemanticDeduplication)
        {
            return filtered;
        }

        var generator = ResolveEmbeddingGenerator(services, heuristics, config, logger);
        if (generator is null)
        {
            logger?.LogWarning("Semantic deduplication skipped because no text embedding generator is registered.");
            return filtered;
        }

        try
        {
            return await DeduplicateAsync(filtered, generator, heuristics, cancellationToken).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            logger?.LogWarning(ex, "Failed to execute semantic deduplication heuristics. Retaining filtered text units only.");
            return filtered;
        }
    }

    private static List<TextUnitRecord> ApplyTokenBudgets(
        IReadOnlyList<TextUnitRecord> textUnits,
        HeuristicMaintenanceConfig heuristics)
    {
        var result = new List<TextUnitRecord>(textUnits.Count);
        Dictionary<string, int>? documentBudgets = null;

        if (heuristics.MaxDocumentTokenBudget > 0)
        {
            documentBudgets = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        }

        foreach (var unit in textUnits.OrderBy(static unit => unit.Id, StringComparer.Ordinal))
        {
            if (heuristics.MaxTokensPerTextUnit > 0 && unit.TokenCount > heuristics.MaxTokensPerTextUnit)
            {
                continue;
            }

            if (documentBudgets is null)
            {
                result.Add(unit);
                continue;
            }

            var allowedDocs = new List<string>();
            foreach (var documentId in unit.DocumentIds)
            {
                if (string.IsNullOrWhiteSpace(documentId))
                {
                    continue;
                }

                documentBudgets.TryGetValue(documentId, out var usedTokens);
                if (usedTokens + unit.TokenCount > heuristics.MaxDocumentTokenBudget)
                {
                    continue;
                }

                allowedDocs.Add(documentId);
            }

            if (allowedDocs.Count == 0)
            {
                continue;
            }

            foreach (var documentId in allowedDocs)
            {
                documentBudgets[documentId] = documentBudgets.GetValueOrDefault(documentId) + unit.TokenCount;
            }

            var dedupedDocs = DeduplicatePreservingOrder(allowedDocs);

            if (dedupedDocs.Count == unit.DocumentIds.Count && unit.DocumentIds.SequenceEqual(dedupedDocs, StringComparer.OrdinalIgnoreCase))
            {
                result.Add(unit);
            }
            else
            {
                result.Add(unit with { DocumentIds = dedupedDocs.ToArray() });
            }
        }

        return result;
    }

    private static async Task<IReadOnlyList<TextUnitRecord>> DeduplicateAsync(
        IReadOnlyList<TextUnitRecord> textUnits,
        IEmbeddingGenerator<string, Embedding<float>> generator,
        HeuristicMaintenanceConfig heuristics,
        CancellationToken cancellationToken)
    {
        var clusters = new List<DeduplicationCluster>(textUnits.Count);

        foreach (var unit in textUnits)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var embedding = await generator.GenerateVectorAsync(unit.Text, cancellationToken: cancellationToken).ConfigureAwait(false);
            var vector = embedding.Length > 0 ? embedding.ToArray() : Array.Empty<float>();

            DeduplicationCluster? match = null;
            double bestSimilarity = 0;

            foreach (var cluster in clusters)
            {
                if (cluster.Vector.Length == 0 || vector.Length == 0)
                {
                    continue;
                }

                var similarity = CosineSimilarity(cluster.Vector, vector);
                if (similarity >= heuristics.SemanticDeduplicationThreshold && similarity > bestSimilarity)
                {
                    bestSimilarity = similarity;
                    match = cluster;
                }
            }

            if (match is null)
            {
                clusters.Add(new DeduplicationCluster(unit, vector));
                continue;
            }

            match.Update(unit);
        }

        return clusters
            .Select(static cluster => cluster.Record)
            .OrderBy(static record => record.Id, StringComparer.Ordinal)
            .ToArray();
    }

    private static double CosineSimilarity(IReadOnlyList<float> left, IReadOnlyList<float> right)
    {
        var length = Math.Min(left.Count, right.Count);
        if (length == 0)
        {
            return 0;
        }

        double dot = 0;
        double leftMagnitude = 0;
        double rightMagnitude = 0;

        for (var index = 0; index < length; index++)
        {
            var l = left[index];
            var r = right[index];
            dot += l * r;
            leftMagnitude += l * l;
            rightMagnitude += r * r;
        }

        if (leftMagnitude <= 0 || rightMagnitude <= 0)
        {
            return 0;
        }

        return dot / (Math.Sqrt(leftMagnitude) * Math.Sqrt(rightMagnitude));
    }

    private static List<string> DeduplicatePreservingOrder(IEnumerable<string> source)
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        return source
            .Where(seen.Add)
            .ToList();
    }

    private static IEmbeddingGenerator<string, Embedding<float>>? ResolveEmbeddingGenerator(
        IServiceProvider services,
        HeuristicMaintenanceConfig heuristics,
        GraphRagConfig config,
        ILogger? logger)
    {
        IEmbeddingGenerator<string, Embedding<float>>? generator = null;

        var modelId = heuristics.EmbeddingModelId;
        if (string.IsNullOrWhiteSpace(modelId))
        {
            modelId = config.EmbedText.ModelId;
        }

        if (!string.IsNullOrWhiteSpace(modelId))
        {
            generator = services.GetKeyedService<IEmbeddingGenerator<string, Embedding<float>>>(modelId);
            if (generator is null)
            {
                logger?.LogWarning(
                    "GraphRAG could not resolve keyed embedding generator '{ModelId}'. Falling back to the default registration.",
                    modelId);
            }
        }

        return generator ?? services.GetService<IEmbeddingGenerator<string, Embedding<float>>>();
    }

    private sealed class DeduplicationCluster(TextUnitRecord record, float[] vector)
    {
        public TextUnitRecord Record { get; private set; } = record;

        public float[] Vector { get; } = vector ?? Array.Empty<float>();

        public void Update(TextUnitRecord incoming)
        {
            var mergedDocuments = MergeLists(Record.DocumentIds, incoming.DocumentIds);
            // Sum token counts so merged records reflect their combined budget.
            var tokenCount = (int)Math.Min((long)Record.TokenCount + incoming.TokenCount, int.MaxValue);

            Record = Record with
            {
                DocumentIds = mergedDocuments,
                TokenCount = tokenCount
            };
        }

        private static string[] MergeLists(IReadOnlyList<string> first, IReadOnlyList<string> second)
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            return first
                .Concat(second)
                .Where(seen.Add)
                .ToArray();
        }
    }
}
