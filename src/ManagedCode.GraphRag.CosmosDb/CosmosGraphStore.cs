using System.Net;
using System.Runtime.CompilerServices;
using GraphRag.Graphs;
using Microsoft.Azure.Cosmos;
using Microsoft.Azure.Cosmos.Linq;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Cosmos;

public sealed class CosmosGraphStore(CosmosClient client, string databaseId, string nodesContainerId, string edgesContainerId, ILogger<CosmosGraphStore> logger) : IGraphStore
{
    private readonly CosmosClient _client = client ?? throw new ArgumentNullException(nameof(client));
    private readonly string _databaseId = databaseId ?? throw new ArgumentNullException(nameof(databaseId));
    private readonly string _nodesContainerId = nodesContainerId ?? throw new ArgumentNullException(nameof(nodesContainerId));
    private readonly string _edgesContainerId = edgesContainerId ?? throw new ArgumentNullException(nameof(edgesContainerId));
    private readonly ILogger<CosmosGraphStore> _logger = logger ?? throw new ArgumentNullException(nameof(logger));

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        var database = await _client.CreateDatabaseIfNotExistsAsync(_databaseId, cancellationToken: cancellationToken);
        await database.Database.CreateContainerIfNotExistsAsync(_nodesContainerId, "/id", cancellationToken: cancellationToken);
        await database.Database.CreateContainerIfNotExistsAsync(_edgesContainerId, "/sourceId", cancellationToken: cancellationToken);
        _logger.LogInformation("Cosmos DB database {Database} initialised", _databaseId);
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);

        var container = _client.GetContainer(_databaseId, _nodesContainerId);
        var document = new NodeDocument(id, label, new Dictionary<string, object?>(properties));
        await container.UpsertItemAsync(document, new PartitionKey(document.Id), cancellationToken: cancellationToken);
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

        var container = _client.GetContainer(_databaseId, _edgesContainerId);
        var document = new EdgeDocument($"{sourceId}:{type}:{targetId}", sourceId, targetId, type, new Dictionary<string, object?>(properties));
        await container.UpsertItemAsync(document, new PartitionKey(document.SourceId), cancellationToken: cancellationToken);
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

        var container = _client.GetContainer(_databaseId, _nodesContainerId);
        foreach (var batch in nodeIds.Chunk(32))
        {
            var deletions = batch.Select(id => DeleteItemIfExistsAsync(container, id, new PartitionKey(id), cancellationToken));
            await Task.WhenAll(deletions).ConfigureAwait(false);
        }
    }

    public async Task DeleteRelationshipsAsync(IReadOnlyCollection<GraphRelationshipKey> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);
        if (relationships.Count == 0)
        {
            return;
        }

        var container = _client.GetContainer(_databaseId, _edgesContainerId);
        foreach (var batch in relationships.Chunk(32))
        {
            var deletions = batch.Select(rel =>
            {
                var id = BuildEdgeId(rel.SourceId, rel.Type, rel.TargetId);
                return DeleteItemIfExistsAsync(container, id, new PartitionKey(rel.SourceId), cancellationToken);
            });

            await Task.WhenAll(deletions).ConfigureAwait(false);
        }
    }

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        return Fetch(cancellationToken);

        async IAsyncEnumerable<GraphRelationship> Fetch([EnumeratorCancellation] CancellationToken token = default)
        {
            var container = _client.GetContainer(_databaseId, _edgesContainerId);
            using var iterator = container.GetItemLinqQueryable<EdgeDocument>(allowSynchronousQueryExecution: false)
                .Where(edge => edge.SourceId == sourceId)
                .ToFeedIterator();

            while (iterator.HasMoreResults)
            {
                var response = await iterator.ReadNextAsync(token);
                foreach (var edge in response)
                {
                    yield return new GraphRelationship(edge.SourceId, edge.TargetId, edge.Type, edge.Properties);
                }
            }
        }
    }

    private sealed record NodeDocument(string Id, string Label, Dictionary<string, object?> Properties);

    private sealed record EdgeDocument(string Id, string SourceId, string TargetId, string Type, Dictionary<string, object?> Properties);

    private static async Task DeleteItemIfExistsAsync(Container container, string id, PartitionKey partitionKey, CancellationToken cancellationToken)
    {
        try
        {
            await container.DeleteItemStreamAsync(id, partitionKey, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            // Item already removed; ignore.
        }
    }

    private static string BuildEdgeId(string sourceId, string type, string targetId) => $"{sourceId}:{type}:{targetId}";

    public IAsyncEnumerable<GraphNode> GetNodesAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default)
    {
        options?.Validate();
        return Fetch(options, cancellationToken);

        async IAsyncEnumerable<GraphNode> Fetch(GraphTraversalOptions? traversalOptions, [EnumeratorCancellation] CancellationToken token = default)
        {
            var container = _client.GetContainer(_databaseId, _nodesContainerId);
            IQueryable<NodeDocument> queryable = container.GetItemLinqQueryable<NodeDocument>(allowSynchronousQueryExecution: false);
            queryable = queryable.OrderBy(node => node.Id);

            if (traversalOptions?.Skip is > 0 and var skip)
            {
                queryable = queryable.Skip(skip);
            }

            if (traversalOptions?.Take is { } take)
            {
                queryable = queryable.Take(take);
            }

            using var iterator = queryable.ToFeedIterator();

            while (iterator.HasMoreResults)
            {
                var response = await iterator.ReadNextAsync(token);
                foreach (var node in response)
                {
                    yield return new GraphNode(node.Id, node.Label, node.Properties);
                }
            }
        }
    }

    public IAsyncEnumerable<GraphRelationship> GetRelationshipsAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default)
    {
        options?.Validate();
        return FetchEdges(options, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchEdges(GraphTraversalOptions? traversalOptions, [EnumeratorCancellation] CancellationToken token = default)
        {
            var container = _client.GetContainer(_databaseId, _edgesContainerId);
            IQueryable<EdgeDocument> queryable = container.GetItemLinqQueryable<EdgeDocument>(allowSynchronousQueryExecution: false);
            queryable = queryable.OrderBy(edge => edge.SourceId).ThenBy(edge => edge.TargetId);

            if (traversalOptions?.Skip is > 0 and var skip)
            {
                queryable = queryable.Skip(skip);
            }

            if (traversalOptions?.Take is { } take)
            {
                queryable = queryable.Take(take);
            }

            using var iterator = queryable.ToFeedIterator();

            while (iterator.HasMoreResults)
            {
                var response = await iterator.ReadNextAsync(token);
                foreach (var edge in response)
                {
                    yield return new GraphRelationship(edge.SourceId, edge.TargetId, edge.Type, edge.Properties);
                }
            }
        }
    }
}
