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

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);

        var container = _client.GetContainer(_databaseId, _edgesContainerId);
        var document = new EdgeDocument($"{sourceId}:{type}:{targetId}", sourceId, targetId, type, new Dictionary<string, object?>(properties));
        await container.UpsertItemAsync(document, new PartitionKey(document.SourceId), cancellationToken: cancellationToken);
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
}
