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

    public async Task UpsertNodesAsync(IReadOnlyCollection<GraphNodeUpsert> nodes, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(nodes);

        foreach (var node in nodes)
        {
            await UpsertNodeAsync(node.Id, node.Label, node.Properties, cancellationToken).ConfigureAwait(false);
        }
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

    public async Task UpsertRelationshipsAsync(IReadOnlyCollection<GraphRelationshipUpsert> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);

        foreach (var relationship in relationships)
        {
            await UpsertRelationshipAsync(
                relationship.SourceId,
                relationship.TargetId,
                relationship.Type,
                relationship.Properties,
                cancellationToken).ConfigureAwait(false);

            if (relationship.Bidirectional)
            {
                await UpsertRelationshipAsync(
                    relationship.TargetId,
                    relationship.SourceId,
                    relationship.Type,
                    relationship.Properties,
                    cancellationToken).ConfigureAwait(false);
            }
        }
    }

    public async Task DeleteNodesAsync(IReadOnlyCollection<string> nodeIds, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(nodeIds);
        if (nodeIds.Count == 0)
        {
            return;
        }

        cancellationToken.ThrowIfCancellationRequested();
        await using var session = _driver.AsyncSession();
        const string cypher = "MATCH (n) WHERE n.id IN $ids DETACH DELETE n";
        await session.ExecuteWriteAsync(tx => tx.RunAsync(cypher, new { ids = nodeIds }));
    }

    public async Task DeleteRelationshipsAsync(IReadOnlyCollection<GraphRelationshipKey> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);
        if (relationships.Count == 0)
        {
            return;
        }

        cancellationToken.ThrowIfCancellationRequested();
        var payload = relationships
            .Select(rel => new { rel.SourceId, rel.TargetId, rel.Type })
            .ToArray();

        const string cypher = @"
UNWIND $rels AS rel
MATCH (source {id: rel.SourceId})-[edge]->(target {id: rel.TargetId})
WHERE type(edge) = rel.Type
DELETE edge";

        await using var session = _driver.AsyncSession();
        await session.ExecuteWriteAsync(tx => tx.RunAsync(cypher, new { rels = payload }));
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

    public IAsyncEnumerable<GraphRelationship> GetRelationshipsAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default)
    {
        options?.Validate();
        cancellationToken.ThrowIfCancellationRequested();
        return FetchAll(options, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchAll(GraphTraversalOptions? traversalOptions, [EnumeratorCancellation] CancellationToken token = default)
        {
            await using var session = _driver.AsyncSession();
            var parameters = new Dictionary<string, object>();
            var pagination = BuildNeo4jPaginationClause(traversalOptions, parameters, orderBy: "source.id, target.id, type(rel)");
            var cursor = await session.RunAsync(
                @"MATCH (source)-[rel]->(target)
                  RETURN source.id AS SourceId, target.id AS TargetId, type(rel) AS Type, properties(rel) AS Properties" + pagination,
                parameters);

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

    public IAsyncEnumerable<GraphNode> GetNodesAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default)
    {
        options?.Validate();
        cancellationToken.ThrowIfCancellationRequested();
        return FetchNodes(options, cancellationToken);

        async IAsyncEnumerable<GraphNode> FetchNodes(GraphTraversalOptions? traversalOptions, [EnumeratorCancellation] CancellationToken token = default)
        {
            await using var session = _driver.AsyncSession();
            var parameters = new Dictionary<string, object>();
            var pagination = BuildNeo4jPaginationClause(traversalOptions, parameters, orderBy: "n.id");
            var cursor = await session.RunAsync(
                @"MATCH (n)
                  RETURN head(labels(n)) AS Label, n.id AS Id, properties(n) AS Properties" + pagination,
                parameters);

            while (await cursor.FetchAsync())
            {
                token.ThrowIfCancellationRequested();
                var record = cursor.Current;
                var properties = record["Properties"].As<IDictionary<string, object?>>();
                yield return new GraphNode(
                    record["Id"].As<string>(),
                    record["Label"].As<string>(),
                    properties.ToDictionary(kvp => kvp.Key, kvp => kvp.Value));
            }
        }
    }

    private static string BuildNeo4jPaginationClause(GraphTraversalOptions? options, IDictionary<string, object> parameters, string orderBy)
    {
        var clause = $" ORDER BY {orderBy}";
        if (options is null)
        {
            return clause;
        }

        if (options.Skip is > 0 and var skip)
        {
            parameters["skip"] = skip;
            clause += " SKIP $skip";
        }

        if (options.Take is { } take)
        {
            parameters["limit"] = take;
            clause += " LIMIT $limit";
        }

        return clause;
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
