using System.Runtime.CompilerServices;
using GraphRag.Graphs;
using Microsoft.Extensions.Logging;
using Neo4j.Driver;

namespace GraphRag.Storage.Neo4j;

public sealed class Neo4jGraphStore(IDriver driver, ILogger<Neo4jGraphStore> logger) : IGraphStore, IAsyncDisposable
{
    private readonly IDriver _driver = driver ?? throw new ArgumentNullException(nameof(driver));
    private readonly ILogger<Neo4jGraphStore> _logger = logger ?? throw new ArgumentNullException(nameof(logger));

    public Neo4jGraphStore(string uri, string username, string password, ILogger<Neo4jGraphStore> logger)
        : this(GraphDatabase.Driver(uri, AuthTokens.Basic(username, password)), logger)
    {
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        await _driver.VerifyConnectivityAsync();
        _logger.LogInformation("Connected to Neo4j");
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        cancellationToken.ThrowIfCancellationRequested();

        var cypher = $"MERGE (n:{EscapeLabel(label)} {{id: $id}}) SET n += $props";
        await using var session = _driver.AsyncSession();
        await session.ExecuteWriteAsync(tx => tx.RunAsync(cypher, new { id, props = properties }));
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);
        cancellationToken.ThrowIfCancellationRequested();

        var cypher = $@"MATCH (source {{id: $sourceId}})
MATCH (target {{id: $targetId}})
MERGE (source)-[r:{EscapeLabel(type)}]->(target)
SET r += $props";

        await using var session = _driver.AsyncSession();
        await session.ExecuteWriteAsync(tx => tx.RunAsync(cypher, new { sourceId, targetId, props = properties }));
    }

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        cancellationToken.ThrowIfCancellationRequested();
        return Fetch(cancellationToken);

        async IAsyncEnumerable<GraphRelationship> Fetch([EnumeratorCancellation] CancellationToken token = default)
        {
            await using var session = _driver.AsyncSession();
            var cursor = await session.RunAsync(
                @"MATCH (source {id: $sourceId})-[rel]->(target)
                  RETURN source.id AS SourceId, target.id AS TargetId, type(rel) AS Type, properties(rel) AS Properties",
                new { sourceId });

            while (await cursor.FetchAsync())
            {
                token.ThrowIfCancellationRequested();
                var record = cursor.Current;
                var properties = record["Properties"].As<IDictionary<string, object?>>();
                yield return new GraphRelationship(
                    record["SourceId"].As<string>(),
                    record["TargetId"].As<string>(),
                    record["Type"].As<string>(),
                    properties.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));
            }
        }
    }

    private static string EscapeLabel(string value)
    {
        if (value.Any(ch => !char.IsLetterOrDigit(ch) && ch != '_' && ch != ':'))
        {
            throw new ArgumentException($"Invalid Neo4j label '{value}'.", nameof(value));
        }

        return value;
    }

    public async ValueTask DisposeAsync()
    {
        await _driver.DisposeAsync();
    }
}
