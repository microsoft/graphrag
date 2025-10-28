using System.Diagnostics;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Postgres;

public sealed class PostgresGraphIngestionBenchmark(PostgresGraphStore graphStore, ILogger<PostgresGraphIngestionBenchmark> logger)
{
    private readonly PostgresGraphStore _graphStore = graphStore ?? throw new ArgumentNullException(nameof(graphStore));
    private readonly ILogger<PostgresGraphIngestionBenchmark> _logger = logger ?? throw new ArgumentNullException(nameof(logger));

    public async Task<PostgresIngestionBenchmarkResult> RunAsync(Stream csvStream, PostgresIngestionBenchmarkOptions options, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(csvStream);
        ArgumentNullException.ThrowIfNull(options);

        if (!csvStream.CanRead)
        {
            throw new InvalidOperationException("Benchmark input stream must be readable.");
        }

        using var reader = new StreamReader(csvStream, leaveOpen: true);
        var headerLine = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
        if (string.IsNullOrWhiteSpace(headerLine))
        {
            return new PostgresIngestionBenchmarkResult(0, 0, TimeSpan.Zero, options.EnsurePropertyIndexes);
        }

        var headers = ParseCsvLine(headerLine);
        var columnLookup = BuildColumnLookup(headers);

        var sourceIndex = GetColumnIndex(columnLookup, options.SourceIdColumn);
        var targetIndex = GetColumnIndex(columnLookup, options.TargetIdColumn);

        var propertyColumnIndexes = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        foreach (var (propertyName, columnName) in options.EdgePropertyColumns)
        {
            propertyColumnIndexes[propertyName] = GetColumnIndex(columnLookup, columnName);
        }

        if (options.EnsurePropertyIndexes)
        {
            foreach (var propertyName in propertyColumnIndexes.Keys)
            {
                await _graphStore.EnsurePropertyKeyIndexAsync(options.EdgeLabel, propertyName, isEdge: true, cancellationToken).ConfigureAwait(false);
            }
        }

        var stopwatch = Stopwatch.StartNew();
        var nodeCache = new HashSet<(string Label, string Id)>(1000, StringTupleComparer.Instance);
        var nodesWritten = 0;
        var relationshipsWritten = 0;

        string? line;
        while ((line = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false)) is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            var columns = ParseCsvLine(line);
            if (columns.Length != headers.Length)
            {
                continue;
            }

            var sourceId = columns[sourceIndex];
            var targetId = columns[targetIndex];

            if (nodeCache.Add((options.SourceLabel, sourceId)))
            {
                await _graphStore.UpsertNodeAsync(sourceId, options.SourceLabel, EmptyProperties.Value, cancellationToken).ConfigureAwait(false);
                nodesWritten++;
            }

            if (nodeCache.Add((options.TargetLabel, targetId)))
            {
                await _graphStore.UpsertNodeAsync(targetId, options.TargetLabel, EmptyProperties.Value, cancellationToken).ConfigureAwait(false);
                nodesWritten++;
            }

            var relationshipProps = BuildEdgeProperties(columns, propertyColumnIndexes);
            await _graphStore.UpsertRelationshipAsync(sourceId, targetId, options.EdgeLabel, relationshipProps, cancellationToken).ConfigureAwait(false);
            relationshipsWritten++;
        }

        stopwatch.Stop();

        var result = new PostgresIngestionBenchmarkResult(nodesWritten, relationshipsWritten, stopwatch.Elapsed, options.EnsurePropertyIndexes);
        _logger.LogInformation("Ingested {Relationships} relationships in {Duration} (indexes: {IndexesEnabled}).", relationshipsWritten, stopwatch.Elapsed, options.EnsurePropertyIndexes);
        return result;
    }

    private static Dictionary<string, int> BuildColumnLookup(string[] headers)
    {
        var lookup = new Dictionary<string, int>(headers.Length, StringComparer.OrdinalIgnoreCase);
        for (var i = 0; i < headers.Length; i++)
        {
            if (!string.IsNullOrWhiteSpace(headers[i]))
            {
                lookup[headers[i].Trim()] = i;
            }
        }

        return lookup;
    }

    private static int GetColumnIndex(Dictionary<string, int> lookup, string columnName)
    {
        if (!lookup.TryGetValue(columnName, out var index))
        {
            throw new KeyNotFoundException($"Column '{columnName}' was not found in the benchmark input.");
        }

        return index;
    }

    private static Dictionary<string, object?> BuildEdgeProperties(string[] row, Dictionary<string, int> propertyIndexes)
    {
        if (propertyIndexes.Count == 0)
        {
            return EmptyProperties.Value;
        }

        var properties = new Dictionary<string, object?>(propertyIndexes.Count, StringComparer.OrdinalIgnoreCase);
        foreach (var (property, index) in propertyIndexes)
        {
            properties[property] = index < row.Length ? row[index] : null;
        }

        return properties;
    }

    private static string[] ParseCsvLine(string line)
    {
        // Simple CSV splitter sufficient for benchmark scenarios (no embedded commas)
        return line.Split(',', StringSplitOptions.TrimEntries);
    }

    private sealed class StringTupleComparer : IEqualityComparer<(string Label, string Id)>
    {
        public static readonly StringTupleComparer Instance = new();

        public bool Equals((string Label, string Id) x, (string Label, string Id) y)
        {
            return string.Equals(x.Label, y.Label, StringComparison.OrdinalIgnoreCase)
                && string.Equals(x.Id, y.Id, StringComparison.Ordinal);
        }

        public int GetHashCode((string Label, string Id) obj)
        {
            var labelHash = obj.Label?.ToLowerInvariant().GetHashCode(StringComparison.Ordinal) ?? 0;
            var idHash = obj.Id?.GetHashCode(StringComparison.Ordinal) ?? 0;
            return HashCode.Combine(labelHash, idHash);
        }
    }

    private sealed class EmptyProperties
    {
        public static readonly Dictionary<string, object?> Value = new(StringComparer.OrdinalIgnoreCase);
    }
}
