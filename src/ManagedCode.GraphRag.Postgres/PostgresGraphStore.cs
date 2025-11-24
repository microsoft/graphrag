using System.Collections;
using System.Collections.Concurrent;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using GraphRag.Constants;
using GraphRag.Graphs;
using GraphRag.Storage.Postgres.ApacheAge;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Npgsql;

namespace GraphRag.Storage.Postgres;

public class PostgresGraphStore : IGraphStore, IAsyncDisposable
{
    private readonly string _graphName;
    private readonly string _graphNameLiteral;
    private readonly bool _autoCreateIndexes;
    private readonly ILogger<PostgresGraphStore> _logger;
    private readonly ConcurrentDictionary<string, bool> _indexedLabels = new(StringComparer.OrdinalIgnoreCase);
    private readonly ConcurrentDictionary<string, bool> _propertyIndexes = new(StringComparer.OrdinalIgnoreCase);
    private readonly IReadOnlyDictionary<string, string[]> _vertexPropertyIndexConfig;
    private readonly IReadOnlyDictionary<string, string[]> _edgePropertyIndexConfig;
    private readonly IAgeClientFactory _ageClientFactory;
    private readonly IAgeConnectionManager? _ownedConnectionManager;
    private static readonly IReadOnlyDictionary<string, object?> EmptyProperties =
        new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>());

    public PostgresGraphStore(string connectionString, string graphName, ILogger<PostgresGraphStore> logger, ILoggerFactory? loggerFactory = null)
        : this(new PostgresGraphStoreOptions
        {
            ConnectionString = connectionString,
            GraphName = graphName
        }, logger, loggerFactory, null)
    {
    }

    public PostgresGraphStore(
        [FromKeyedServices] PostgresGraphStoreOptions options,
        ILogger<PostgresGraphStore> logger,
        ILoggerFactory? loggerFactory = null,
        [FromKeyedServices] IAgeClientFactory? ageClientFactory = null)
    {
        ArgumentNullException.ThrowIfNull(options);

        var connectionString = options.ConnectionString;
        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new ArgumentException("ConnectionString cannot be null or whitespace.", nameof(options));
        }

        var graphName = options.GraphName;
        if (string.IsNullOrWhiteSpace(graphName))
        {
            throw new ArgumentException("GraphName cannot be null or whitespace.", nameof(options));
        }

        _graphName = graphName;
        _graphNameLiteral = BuildGraphNameLiteral(_graphName);
        _autoCreateIndexes = options.AutoCreateIndexes;
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        _vertexPropertyIndexConfig = NormalizeIndexMap(options.VertexPropertyIndexes);
        _edgePropertyIndexConfig = NormalizeIndexMap(options.EdgePropertyIndexes);
        if (ageClientFactory is not null)
        {
            _ageClientFactory = ageClientFactory;
        }
        else
        {
            var factory = loggerFactory ?? NullLoggerFactory.Instance;
            var connectionManagerLogger = factory.CreateLogger<AgeConnectionManager>();
            var connectionManager = new AgeConnectionManager(options, connectionManagerLogger);
            _ownedConnectionManager = connectionManager;
            _ageClientFactory = new AgeClientFactory(connectionManager, factory);
        }
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        await using var client = _ageClientFactory.CreateUnscopedClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await client.CreateGraphAsync(_graphName, cancellationToken).ConfigureAwait(false);
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);

        _logger.LogInformation("Apache AGE graph {GraphName} initialised.", _graphName);
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentNullException.ThrowIfNull(properties);

        await using var client = _ageClientFactory.CreateClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        var normalized = NormalizeProperties(properties);
        var (writes, removes) = SplitProperties(normalized);
        await UpsertNodeInternalAsync(client, id, label, writes, cancellationToken).ConfigureAwait(false);
        if (removes.Count > 0)
        {
            await RemoveNodePropertiesAsync(client, id, label, removes, cancellationToken).ConfigureAwait(false);
        }
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task UpsertNodesAsync(IReadOnlyCollection<GraphNodeUpsert> nodes, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(nodes);
        if (nodes.Count == 0)
        {
            return;
        }

        await using var client = _ageClientFactory.CreateClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        foreach (var node in nodes)
        {
            ArgumentException.ThrowIfNullOrWhiteSpace(node.Id);
            ArgumentException.ThrowIfNullOrWhiteSpace(node.Label);
            var normalized = NormalizeProperties(node.Properties);
            var (writes, removes) = SplitProperties(normalized);
            await UpsertNodeInternalAsync(client, node.Id, node.Label, writes, cancellationToken).ConfigureAwait(false);
            if (removes.Count > 0)
            {
                await RemoveNodePropertiesAsync(client, node.Id, node.Label, removes, cancellationToken).ConfigureAwait(false);
            }
        }

        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Bulk upserted {Count} nodes into graph {GraphName}.", nodes.Count, _graphName);
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);
        ArgumentNullException.ThrowIfNull(properties);

        await using var client = _ageClientFactory.CreateClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        var normalized = NormalizeProperties(properties);
        var (writes, removes) = SplitProperties(normalized);
        await UpsertRelationshipInternalAsync(client, sourceId, targetId, type, writes, cancellationToken).ConfigureAwait(false);
        if (removes.Count > 0)
        {
            await RemoveRelationshipPropertiesAsync(client, sourceId, targetId, type, removes, cancellationToken).ConfigureAwait(false);
        }
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task UpsertRelationshipsAsync(IReadOnlyCollection<GraphRelationshipUpsert> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);
        if (relationships.Count == 0)
        {
            return;
        }

        var expanded = ExpandRelationships(relationships).ToList();
        if (expanded.Count == 0)
        {
            return;
        }

        await using var client = _ageClientFactory.CreateClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        foreach (var relationship in expanded)
        {
            ArgumentException.ThrowIfNullOrWhiteSpace(relationship.SourceId);
            ArgumentException.ThrowIfNullOrWhiteSpace(relationship.TargetId);
            ArgumentException.ThrowIfNullOrWhiteSpace(relationship.Type);

            var normalized = NormalizeProperties(relationship.Properties);
            var (writes, removes) = SplitProperties(normalized);

            await UpsertRelationshipInternalAsync(
                client,
                relationship.SourceId,
                relationship.TargetId,
                relationship.Type,
                writes,
                cancellationToken).ConfigureAwait(false);

            if (removes.Count > 0)
            {
                await RemoveRelationshipPropertiesAsync(
                    client,
                    relationship.SourceId,
                    relationship.TargetId,
                    relationship.Type,
                    removes,
                    cancellationToken).ConfigureAwait(false);
            }
        }

        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Bulk upserted {Count} relationships into graph {GraphName}.", expanded.Count, _graphName);
    }

    public async Task DeleteNodesAsync(IReadOnlyCollection<string> nodeIds, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(nodeIds);
        if (nodeIds.Count == 0)
        {
            return;
        }

        await using var client = _ageClientFactory.CreateClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        foreach (var batch in nodeIds.Chunk(128))
        {
            var parameters = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                [GraphQueryParameters.NodeIds] = batch
            };

            const string query = @"
                MATCH (n)
                WHERE n.id IN $" + GraphQueryParameters.NodeIds + @"
                DETACH DELETE n";

            await ExecuteCypherAsync(client, query, parameters, cancellationToken).ConfigureAwait(false);
        }

        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Deleted {Count} nodes from graph {GraphName}.", nodeIds.Count, _graphName);
    }

    public async Task DeleteRelationshipsAsync(IReadOnlyCollection<GraphRelationshipKey> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);
        if (relationships.Count == 0)
        {
            return;
        }

        await using var client = _ageClientFactory.CreateClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        foreach (var batch in relationships.Chunk(64))
        {
            var payload = batch
                .Select(rel => new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
                {
                    [GraphQueryParameters.SourceId] = rel.SourceId,
                    [GraphQueryParameters.TargetId] = rel.TargetId,
                    [GraphQueryParameters.RelationshipType] = rel.Type
                })
                .ToArray();

            var parameters = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                [GraphQueryParameters.Relationships] = payload
            };

            const string query = @"
                UNWIND $" + GraphQueryParameters.Relationships + @" AS rel
                MATCH (source { id: rel." + GraphQueryParameters.SourceId + @" })-[edge]->(target { id: rel." + GraphQueryParameters.TargetId + @" })
                WHERE type(edge) = rel." + GraphQueryParameters.RelationshipType + @"
                DELETE edge";

            await ExecuteCypherAsync(client, query, parameters, cancellationToken).ConfigureAwait(false);
        }

        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Deleted {Count} relationships from graph {GraphName}.", relationships.Count, _graphName);
    }

    private async Task UpsertNodeInternalAsync(IAgeClient client, string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken)
    {
        var parameters = new Dictionary<string, object?>
        {
            [CypherParameterNames.NodeId] = id
        };

        var propertyAssignments = BuildPropertyAssignments("n", ConvertProperties(properties), parameters, "node_prop");

        var queryBuilder = new StringBuilder();
        queryBuilder.Append("MERGE (n:");
        queryBuilder.Append(EscapeLabel(label));
        queryBuilder.Append(" { id: $");
        queryBuilder.Append(CypherParameterNames.NodeId);
        queryBuilder.Append(" })");

        if (propertyAssignments.Count > 0)
        {
            queryBuilder.AppendLine();
            queryBuilder.Append("SET ");
            queryBuilder.Append(string.Join(", ", propertyAssignments));
        }

        queryBuilder.AppendLine();
        queryBuilder.Append("RETURN n");

        await EnsureLabelIndexesAsync(client, label, isEdge: false, cancellationToken).ConfigureAwait(false);
        await ExecuteCypherAsync(client, queryBuilder.ToString(), parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted node {Id} ({Label}) into graph {GraphName}.", id, label, _graphName);
    }

    private async Task UpsertRelationshipInternalAsync(IAgeClient client, string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken)
    {
        var parameters = new Dictionary<string, object?>
        {
            [CypherParameterNames.SourceId] = sourceId,
            [CypherParameterNames.TargetId] = targetId
        };

        var propertyAssignments = BuildPropertyAssignments("rel", ConvertProperties(properties), parameters, "rel_prop");

        var queryBuilder = new StringBuilder();
        queryBuilder.Append("MATCH (source { id: $");
        queryBuilder.Append(CypherParameterNames.SourceId);
        queryBuilder.Append(" }), (target { id: $");
        queryBuilder.Append(CypherParameterNames.TargetId);
        queryBuilder.Append(" })");
        queryBuilder.AppendLine();
        queryBuilder.Append("MERGE (source)-[rel:");
        queryBuilder.Append(EscapeLabel(type));
        queryBuilder.Append("]->(target)");

        if (propertyAssignments.Count > 0)
        {
            queryBuilder.AppendLine();
            queryBuilder.Append("SET ");
            queryBuilder.Append(string.Join(", ", propertyAssignments));
        }

        queryBuilder.AppendLine();
        queryBuilder.Append("RETURN rel");

        await EnsureLabelIndexesAsync(client, type, isEdge: true, cancellationToken).ConfigureAwait(false);
        await ExecuteCypherAsync(client, queryBuilder.ToString(), parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted relationship {Source}-[{Type}]->{Target} in graph {GraphName}.", sourceId, type, targetId, _graphName);
    }

    public Task EnsurePropertyKeyIndexAsync(string label, string propertyKey, bool isEdge, CancellationToken cancellationToken = default) =>
        EnsurePropertyKeyIndexInternalAsync(label, propertyKey, isEdge, relation: null, cancellationToken);

    public async Task<IReadOnlyList<string>> ExplainAsync(string cypherQuery, IReadOnlyDictionary<string, object?>? parameters = null, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(cypherQuery);

        var explainQuery = $"EXPLAIN\n{cypherQuery}";
        var parameterJson = SerializeParameters(parameters);

        return await ExecuteExplainAsync(explainQuery, parameterJson, cancellationToken).ConfigureAwait(false);
    }

    private async Task EnsurePropertyKeyIndexInternalAsync(IAgeClient client, string label, string propertyKey, bool isEdge, string? relation, CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentException.ThrowIfNullOrWhiteSpace(propertyKey);

        var cacheKey = BuildPropertyIndexCacheKey(label, propertyKey, isEdge);
        if (!_propertyIndexes.TryAdd(cacheKey, true))
        {
            return;
        }

        relation ??= await ResolveLabelRelationAsync(client, label, isEdge, cancellationToken).ConfigureAwait(false);
        if (string.IsNullOrEmpty(relation))
        {
            _propertyIndexes.TryRemove(cacheKey, out _);
            return;
        }

        var indexNameSuffix = $"prop_{SanitizeIdentifier(propertyKey)}";
        var indexName = BuildIndexName(relation, indexNameSuffix);
        var columnExpression = $"agtype_access_operator(VARIADIC ARRAY[properties, '\"{propertyKey}\"'::agtype])";
        var command = $"CREATE INDEX IF NOT EXISTS {indexName} ON {relation} USING BTREE ({columnExpression});";

        await ExecuteIndexCommandsAsync(client, new[] { command }, cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Ensured targeted index {Index} on {Relation} for property {Property}.", indexName, relation, propertyKey);
    }

    private async Task EnsurePropertyKeyIndexInternalAsync(string label, string propertyKey, bool isEdge, string? relation, CancellationToken cancellationToken)
    {
        await using var client = _ageClientFactory.CreateUnscopedClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await EnsurePropertyKeyIndexInternalAsync(client, label, propertyKey, isEdge, relation, cancellationToken).ConfigureAwait(false);
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
    }

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        return FetchAsync(sourceId, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchAsync(string nodeId, [EnumeratorCancellation] CancellationToken token)
        {
            await using var client = _ageClientFactory.CreateUnscopedClient();
            await client.OpenConnectionAsync(token).ConfigureAwait(false);

            await using var command = client.Connection.CreateCommand();
            var payload = JsonSerializer.Serialize(new Dictionary<string, object?>
            {
                [CypherParameterNames.NodeId] = nodeId
            });
            command.CommandText = string.Concat(
                "SELECT ",
                "\n    source_id::text,",
                "\n    target_id::text,",
                "\n    edge_type::text,",
                "\n    edge_props::text",
                "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", $$",
                "\n    MATCH (source { id: $node_id })-[rel]->(target)",
                "\n    RETURN source.id AS source_id, target.id AS target_id, type(rel) AS edge_type, properties(rel) AS edge_props",
                "\n$$, @params) AS (source_id agtype, target_id agtype, edge_type agtype, edge_props agtype);");
            command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, payload));
            await using var reader = await command.ExecuteReaderAsync(token).ConfigureAwait(false);
            while (await reader.ReadAsync(token).ConfigureAwait(false))
            {
                var source = NormalizeAgTypeText(reader.GetString(0));
                var target = NormalizeAgTypeText(reader.GetString(1));
                var relationshipType = NormalizeAgTypeText(reader.GetString(2));
                var propertiesJson = reader.IsDBNull(3) ? "{}" : reader.GetString(3);
                var properties = ParseProperties(propertiesJson);

                yield return new GraphRelationship(source, target, relationshipType, properties);
            }

            await client.CloseConnectionAsync(token).ConfigureAwait(false);
        }
    }

    public IAsyncEnumerable<GraphRelationship> GetRelationshipsAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default)
    {
        options?.Validate();
        return FetchRelationships(options, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchRelationships(GraphTraversalOptions? traversalOptions, [EnumeratorCancellation] CancellationToken token)
        {
            await using var client = _ageClientFactory.CreateUnscopedClient();
            await client.OpenConnectionAsync(token).ConfigureAwait(false);

            await using var command = client.Connection.CreateCommand();
            var pagination = BuildPaginationClause(traversalOptions);
            var parametersJson = SerializeParameters(null);
            command.CommandText = string.Concat(
                "SELECT ",
                "\n    source_id::text,",
                "\n    target_id::text,",
                "\n    edge_type::text,",
                "\n    edge_props::text",
                "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", $$",
                "\n    MATCH (source)-[rel]->(target)",
                "\n    RETURN source.id AS source_id, target.id AS target_id, type(rel) AS edge_type, properties(rel) AS edge_props",
                "\n    ORDER BY source.id, target.id, type(rel)",
                pagination,
                "\n$$, @params) AS (source_id agtype, target_id agtype, edge_type agtype, edge_props agtype);");
            command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, parametersJson));
            await using var reader = await command.ExecuteReaderAsync(token).ConfigureAwait(false);
            while (await reader.ReadAsync(token).ConfigureAwait(false))
            {
                var source = NormalizeAgTypeText(reader.GetString(0));
                var target = NormalizeAgTypeText(reader.GetString(1));
                var relationshipType = NormalizeAgTypeText(reader.GetString(2));
                var propertiesJson = reader.IsDBNull(3) ? "{}" : reader.GetString(3);
                var properties = ParseProperties(propertiesJson);

                yield return new GraphRelationship(source, target, relationshipType, properties);
            }

            await client.CloseConnectionAsync(token).ConfigureAwait(false);
        }
    }

    public IAsyncEnumerable<GraphNode> GetNodesAsync(GraphTraversalOptions? options = null, CancellationToken cancellationToken = default)
    {
        options?.Validate();
        return FetchNodes(options, cancellationToken);

        async IAsyncEnumerable<GraphNode> FetchNodes(GraphTraversalOptions? traversalOptions, [EnumeratorCancellation] CancellationToken token)
        {
            await using var client = _ageClientFactory.CreateUnscopedClient();
            await client.OpenConnectionAsync(token).ConfigureAwait(false);

            await using var command = client.Connection.CreateCommand();
            var pagination = BuildPaginationClause(traversalOptions);
            var parametersJson = SerializeParameters(null);
            command.CommandText = string.Concat(
                "SELECT ",
                "\n    node_label::text,",
                "\n    node_id::text,",
                "\n    node_props::text",
                "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", $$",
                "\n    MATCH (n)",
                "\n    RETURN head(labels(n)) AS node_label, n.id AS node_id, properties(n) AS node_props",
                "\n    ORDER BY n.id",
                pagination,
                "\n$$, @params) AS (node_label agtype, node_id agtype, node_props agtype);");
            command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, parametersJson));
            await using var reader = await command.ExecuteReaderAsync(token).ConfigureAwait(false);
            while (await reader.ReadAsync(token).ConfigureAwait(false))
            {
                var label = NormalizeAgTypeText(reader.GetString(0));
                var id = NormalizeAgTypeText(reader.GetString(1));
                var propsJson = reader.IsDBNull(2) ? "{}" : reader.GetString(2);
                var props = ParseProperties(propsJson);
                yield return new GraphNode(id, label, props);
            }

            await client.CloseConnectionAsync(token).ConfigureAwait(false);
        }
    }

    protected virtual async Task ExecuteCypherAsync(string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
    {
        await using var client = _ageClientFactory.CreateUnscopedClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await ExecuteCypherAsync(client, query, parameters, cancellationToken).ConfigureAwait(false);
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
    }

    private async Task ExecuteCypherAsync(IAgeClient client, string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
    {
        var queryLiteral = WrapInDollarQuotes(query);
        var payload = SerializeParameters(parameters);
        var commandText = string.Concat(
            "SELECT *",
            "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", ", queryLiteral, "::cstring, @params) AS (result agtype);");

        for (var attempt = 0; attempt < 2; attempt++)
        {
            await using var command = client.Connection.CreateCommand();
            command.CommandText = commandText;
            command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, payload));
            try
            {
                await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
                return;
            }
            catch (PostgresException ex) when (ShouldRetryOnLabelCreationRace(ex) && attempt == 0)
            {
                continue;
            }
        }
    }

    private static bool ShouldRetryOnLabelCreationRace(PostgresException exception) =>
        exception.SqlState is PostgresErrorCodes.DuplicateTable or
            PostgresErrorCodes.DuplicateObject or
            PostgresErrorCodes.UniqueViolation;

    private static (IReadOnlyDictionary<string, object?> Writes, IReadOnlyCollection<string> Removes) SplitProperties(IReadOnlyDictionary<string, object?> properties)
    {
        if (properties.Count == 0)
        {
            return (EmptyProperties, Array.Empty<string>());
        }

        var writes = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        var removes = new List<string>();

        foreach (var (key, value) in properties)
        {
            if (value is null)
            {
                removes.Add(key);
                continue;
            }

            writes[key] = value;
        }

        var writeResult = writes.Count == 0 ? EmptyProperties : writes;
        IReadOnlyCollection<string> removeResult = removes.Count == 0 ? Array.Empty<string>() : removes;
        return (writeResult, removeResult);
    }

    private async Task RemoveNodePropertiesAsync(IAgeClient client, string id, string label, IReadOnlyCollection<string> propertyKeys, CancellationToken cancellationToken)
    {
        if (propertyKeys.Count == 0)
        {
            return;
        }

        var parameters = new Dictionary<string, object?>
        {
            [CypherParameterNames.NodeId] = id
        };

        var builder = new StringBuilder();
        builder.Append("MATCH (n:");
        builder.Append(EscapeLabel(label));
        builder.Append(" { id: $");
        builder.Append(CypherParameterNames.NodeId);
        builder.Append(" })");

        foreach (var key in propertyKeys)
        {
            builder.AppendLine();
            builder.Append("REMOVE n.`");
            builder.Append(EscapePropertyName(key));
            builder.Append('`');
        }

        await ExecuteCypherAsync(client, builder.ToString(), parameters, cancellationToken).ConfigureAwait(false);
    }

    private async Task RemoveRelationshipPropertiesAsync(IAgeClient client, string sourceId, string targetId, string type, IReadOnlyCollection<string> propertyKeys, CancellationToken cancellationToken)
    {
        if (propertyKeys.Count == 0)
        {
            return;
        }

        var parameters = new Dictionary<string, object?>
        {
            [CypherParameterNames.SourceId] = sourceId,
            [CypherParameterNames.TargetId] = targetId
        };

        var builder = new StringBuilder();
        builder.Append("MATCH (source { id: $");
        builder.Append(CypherParameterNames.SourceId);
        builder.Append(" })-[rel:");
        builder.Append(EscapeLabel(type));
        builder.Append("]->(target { id: $");
        builder.Append(CypherParameterNames.TargetId);
        builder.Append(" })");

        foreach (var key in propertyKeys)
        {
            builder.AppendLine();
            builder.Append("REMOVE rel.`");
            builder.Append(EscapePropertyName(key));
            builder.Append('`');
        }

        await ExecuteCypherAsync(client, builder.ToString(), parameters, cancellationToken).ConfigureAwait(false);
    }

    private static string EscapeLabel(string label)
    {
        if (string.IsNullOrWhiteSpace(label))
        {
            throw new ArgumentException("Label cannot be null or whitespace.", nameof(label));
        }

        foreach (var ch in label)
        {
            if (!char.IsLetterOrDigit(ch) && ch != '_' && ch != ':')
            {
                throw new ArgumentException($"Invalid character '{ch}' in label '{label}'.", nameof(label));
            }
        }

        return label;
    }

    private static IDictionary<string, object?> ConvertProperties(IReadOnlyDictionary<string, object?> properties)
    {
        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);

        foreach (var (key, value) in properties)
        {
            if (value is null || string.Equals(key, EntityPropertyNames.Id, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            result[key] = NormalizeValue(value);
        }

        return result;
    }

    private static object? NormalizeValue(object? value)
    {
        return value switch
        {
            null => null,
            JsonElement jsonElement => NormalizeJsonElement(jsonElement),
            string s => s,
            bool b => b,
            int or long or short or byte or sbyte or uint or ushort or ulong => Convert.ToInt64(value, CultureInfo.InvariantCulture),
            float or double or decimal => Convert.ToDouble(value, CultureInfo.InvariantCulture),
            DateTime dt => dt.ToUniversalTime(),
            DateTimeOffset dto => dto.UtcDateTime,
            Guid guid => guid.ToString(),
            byte[] bytes => Convert.ToBase64String(bytes),
            IDictionary<string, object?> dictionary => dictionary.ToDictionary(
                static kvp => kvp.Key,
                kvp => NormalizeValue(kvp.Value),
                StringComparer.OrdinalIgnoreCase),
            IReadOnlyDictionary<string, object?> readOnlyDictionary => readOnlyDictionary.ToDictionary(
                static kvp => kvp.Key,
                kvp => NormalizeValue(kvp.Value),
                StringComparer.OrdinalIgnoreCase),
            IEnumerable<KeyValuePair<string, object?>> pairs => ConvertKeyValueEnumerable(pairs),
            IEnumerable enumerable when value is not string => ConvertSequence(enumerable),
            _ => value.ToString()
        };
    }

    private static IDictionary<string, object?> ConvertKeyValueEnumerable(IEnumerable<KeyValuePair<string, object?>> pairs)
    {
        var dictionary = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var (key, val) in pairs)
        {
            dictionary[key] = NormalizeValue(val);
        }

        return dictionary;
    }

    private static List<object?> ConvertSequence(IEnumerable enumerable)
    {
        var list = new List<object?>();
        foreach (var item in enumerable)
        {
            list.Add(NormalizeValue(item));
        }

        return list;
    }

    private static object? NormalizeJsonElement(JsonElement element)
    {
        return element.ValueKind switch
        {
            JsonValueKind.Object => element.EnumerateObject()
                .ToDictionary(
                    property => property.Name,
                    property => NormalizeJsonElement(property.Value),
                    StringComparer.OrdinalIgnoreCase),
            JsonValueKind.Array => element.EnumerateArray()
                .Select(NormalizeJsonElement)
                .ToList(),
            JsonValueKind.String => element.GetString(),
            JsonValueKind.Number => element.TryGetInt64(out var i64) ? i64 : element.GetDouble(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => null,
            _ => element.GetRawText()
        };
    }

    private async Task EnsureLabelIndexesAsync(IAgeClient client, string label, bool isEdge, CancellationToken cancellationToken)
    {
        if (!_autoCreateIndexes)
        {
            return;
        }

        var cacheKey = BuildLabelCacheKey(label, isEdge);
        if (!_indexedLabels.TryAdd(cacheKey, true))
        {
            return;
        }

        var relation = await ResolveLabelRelationAsync(client, label, isEdge, cancellationToken).ConfigureAwait(false);
        if (string.IsNullOrEmpty(relation))
        {
            _indexedLabels.TryRemove(cacheKey, out _);
            return;
        }

        var commands = BuildDefaultIndexCommands(relation, isEdge).ToArray();
        if (commands.Length > 0)
        {
            await ExecuteIndexCommandsAsync(client, commands, cancellationToken).ConfigureAwait(false);
            _logger.LogInformation("Ensured AGE default indexes on {Relation} ({LabelType}).", relation, isEdge ? "edge" : "vertex");
        }

        await EnsureConfiguredPropertyIndexesAsync(client, label, relation, isEdge, cancellationToken).ConfigureAwait(false);
    }

    private async Task EnsureConfiguredPropertyIndexesAsync(IAgeClient client, string label, string relation, bool isEdge, CancellationToken cancellationToken)
    {
        var propertyMap = isEdge ? _edgePropertyIndexConfig : _vertexPropertyIndexConfig;
        if (!propertyMap.TryGetValue(label, out var properties) || properties.Length == 0)
        {
            return;
        }

        foreach (var property in properties)
        {
            await EnsurePropertyKeyIndexInternalAsync(client, label, property, isEdge, relation, cancellationToken).ConfigureAwait(false);
        }
    }

    protected virtual async Task<string?> ResolveLabelRelationAsync(string label, bool isEdge, CancellationToken cancellationToken)
    {
        await using var client = _ageClientFactory.CreateUnscopedClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        var relation = await ResolveLabelRelationAsync(client, label, isEdge, cancellationToken).ConfigureAwait(false);
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
        return relation;
    }

    protected virtual async Task<string?> ResolveLabelRelationAsync(IAgeClient client, string label, bool isEdge, CancellationToken cancellationToken)
    {
        await using var command = client.Connection.CreateCommand();
        const string sql = @"
SELECT quote_ident(n.nspname) || '.' || quote_ident(c.relname)
FROM ag_catalog.ag_label l
JOIN ag_catalog.ag_graph g ON g.graphid = l.graph
JOIN pg_class c ON c.oid = l.relation
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE g.name = @graph_name AND l.name = @label_name AND l.kind = @label_kind
LIMIT 1;";

        command.CommandText = sql;
        command.Parameters.AddWithValue("graph_name", _graphName);
        command.Parameters.AddWithValue("label_name", label);
        command.Parameters.AddWithValue("label_kind", isEdge ? "e" : "v");

        var result = await command.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);
        return result as string;
    }

    protected virtual async Task ExecuteIndexCommandsAsync(IEnumerable<string> commands, CancellationToken cancellationToken)
    {
        await using var client = _ageClientFactory.CreateUnscopedClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await ExecuteIndexCommandsAsync(client, commands, cancellationToken).ConfigureAwait(false);
        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
    }

    protected virtual async Task ExecuteIndexCommandsAsync(IAgeClient client, IEnumerable<string> commands, CancellationToken cancellationToken)
    {
        foreach (var commandText in commands)
        {
            await using var command = client.Connection.CreateCommand();
            command.CommandText = commandText;
            try
            {
                await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (PostgresException ex) when (IsDuplicateSchemaObject(ex))
            {
                continue;
            }
        }
    }

    protected virtual async Task<IReadOnlyList<string>> ExecuteExplainAsync(string explainQuery, string parameterJson, CancellationToken cancellationToken)
    {
        await using var client = _ageClientFactory.CreateUnscopedClient();
        await client.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using var command = client.Connection.CreateCommand();
        var explainLiteral = WrapInDollarQuotes(explainQuery);
        command.CommandText = string.Concat(
            "SELECT plan",
            "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", ", explainLiteral, "::cstring, @params) AS (plan text);");
        command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, parameterJson));

        var plan = new List<string>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            plan.Add(reader.GetString(0));
        }

        await client.CloseConnectionAsync(cancellationToken).ConfigureAwait(false);
        return plan;
    }

    private static string BuildGraphNameLiteral(string graphName)
    {
        if (string.IsNullOrWhiteSpace(graphName))
        {
            throw new ArgumentException("Graph name cannot be null or whitespace.", nameof(graphName));
        }

        foreach (var ch in graphName)
        {
            if (!char.IsLetterOrDigit(ch) && ch != '_')
            {
                throw new ArgumentException($"Invalid character '{ch}' in graph name '{graphName}'.", nameof(graphName));
            }
        }

        return $"'{graphName}'::name";
    }

    private static NpgsqlParameter CreateAgTypeParameter(string name, string jsonPayload)
    {
        ArgumentNullException.ThrowIfNull(jsonPayload);

        var agtype = new Agtype(jsonPayload);
        return new NpgsqlParameter<Agtype>(name, agtype)
        {
            DataTypeName = "ag_catalog.agtype"
        };
    }

    private static IReadOnlyList<string> BuildPropertyAssignments(string alias, IDictionary<string, object?> properties, IDictionary<string, object?> parameters, string parameterPrefix)
    {
        if (properties.Count == 0)
        {
            return Array.Empty<string>();
        }

        var assignments = new List<string>(properties.Count);
        var usedParameterNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var (key, value) in properties)
        {
            var escapedProperty = EscapePropertyName(key);
            var parameterName = $"{parameterPrefix}_{escapedProperty}";

            var suffix = 0;
            while (!usedParameterNames.Add(parameterName) || parameters.ContainsKey(parameterName))
            {
                parameterName = $"{parameterPrefix}_{escapedProperty}_{++suffix}";
            }

            parameters[parameterName] = value;
            assignments.Add($"{alias}.`{escapedProperty}` = ${parameterName}");
        }

        return assignments;
    }

    private static string EscapePropertyName(string propertyName)
    {
        if (string.IsNullOrWhiteSpace(propertyName))
        {
            throw new ArgumentException("Property name cannot be null or whitespace.", nameof(propertyName));
        }

        foreach (var ch in propertyName)
        {
            if (!char.IsLetterOrDigit(ch) && ch != '_')
            {
                throw new ArgumentException($"Invalid character '{ch}' in property name '{propertyName}'.", nameof(propertyName));
            }
        }

        return propertyName;
    }

    private static string WrapInDollarQuotes(string value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var delimiter = "$graphrag$";
        while (value.Contains(delimiter, StringComparison.Ordinal))
        {
            delimiter = $"${Guid.NewGuid():N}$";
        }

        return $"{delimiter}{value}{delimiter}";
    }

    private static IEnumerable<string> BuildDefaultIndexCommands(string relation, bool isEdge)
    {
        var commands = new List<string>
        {
            $"CREATE INDEX IF NOT EXISTS {BuildIndexName(relation, "id")} ON {relation} USING BTREE (id);",
            $"CREATE INDEX IF NOT EXISTS {BuildIndexName(relation, "props")} ON {relation} USING GIN (properties);"
        };

        if (isEdge)
        {
            commands.Add($"CREATE INDEX IF NOT EXISTS {BuildIndexName(relation, "start_id")} ON {relation} USING BTREE (start_id);");
            commands.Add($"CREATE INDEX IF NOT EXISTS {BuildIndexName(relation, "end_id")} ON {relation} USING BTREE (end_id);");
        }

        return commands;
    }

    private static IReadOnlyDictionary<string, string[]> NormalizeIndexMap(Dictionary<string, string[]>? source)
    {
        if (source is null || source.Count == 0)
        {
            return new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase);
        }

        var result = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase);
        foreach (var (label, properties) in source)
        {
            if (string.IsNullOrWhiteSpace(label) || properties is null)
            {
                continue;
            }

            var cleaned = properties
                .Where(static p => !string.IsNullOrWhiteSpace(p))
                .Select(static p => p!.Trim())
                .Where(static p => p.Length > 0)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToArray();

            if (cleaned.Length > 0)
            {
                result[label] = cleaned;
            }
        }

        return result;
    }

    private static string BuildIndexName(string relation, string suffix)
    {
        var normalizedRelation = relation.Replace("\"", string.Empty).Replace('.', '_');
        var safeSuffix = SanitizeIdentifier(suffix);
        var candidate = $"idx_{SanitizeIdentifier(normalizedRelation)}_{safeSuffix}";
        return candidate;
    }

    private static string SanitizeIdentifier(string value)
    {
        if (string.IsNullOrEmpty(value))
        {
            return "value";
        }

        var builder = new StringBuilder(value.Length);
        foreach (var ch in value)
        {
            if (char.IsLetterOrDigit(ch))
            {
                builder.Append(char.ToLowerInvariant(ch));
            }
            else
            {
                builder.Append('_');
            }
        }

        var sanitized = builder.ToString().Trim('_');
        return string.IsNullOrEmpty(sanitized) ? "value" : sanitized;
    }

    private static string BuildLabelCacheKey(string label, bool isEdge)
    {
        return $"{label}|{(isEdge ? "edge" : "vertex")}";
    }

    private static string BuildPropertyIndexCacheKey(string label, string propertyKey, bool isEdge)
    {
        return $"{label}|{propertyKey}|{(isEdge ? "edge" : "vertex")}";
    }

    private static string SerializeParameters(IReadOnlyDictionary<string, object?>? parameters)
    {
        if (parameters is null || parameters.Count == 0)
        {
            return "{}";
        }

        return JsonSerializer.Serialize(parameters);
    }

    private static string BuildPaginationClause(GraphTraversalOptions? options)
    {
        if (options is null)
        {
            return string.Empty;
        }

        var builder = new StringBuilder();
        if (options.Skip is > 0 and var skip)
        {
            builder.AppendLine();
            builder.Append("    SKIP ");
            builder.Append(skip);
        }

        if (options.Take is { } take)
        {
            builder.AppendLine();
            builder.Append("    LIMIT ");
            builder.Append(take);
        }

        return builder.ToString();
    }

    private static string NormalizeAgTypeText(string value) => value.Trim('"');

    private static IReadOnlyDictionary<string, object?> ParseProperties(string json)
    {
        try
        {
            using var document = JsonDocument.Parse(json);
            var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
            foreach (var property in document.RootElement.EnumerateObject())
            {
                result[property.Name] = property.Value.ValueKind switch
                {
                    JsonValueKind.String => property.Value.GetString(),
                    JsonValueKind.Number => property.Value.TryGetInt64(out var i64) ? i64 : property.Value.GetDouble(),
                    JsonValueKind.True => true,
                    JsonValueKind.False => false,
                    JsonValueKind.Null => null,
                    _ => property.Value.GetRawText()
                };
            }

            return result;
        }
        catch
        {
            return new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        }
    }

    private static IReadOnlyDictionary<string, object?> NormalizeProperties(IReadOnlyDictionary<string, object?>? properties) =>
        properties ?? EmptyProperties;

    private static IEnumerable<GraphRelationshipUpsert> ExpandRelationships(IEnumerable<GraphRelationshipUpsert> relationships)
    {
        foreach (var relationship in relationships)
        {
            yield return relationship;

            if (relationship.Bidirectional)
            {
                yield return relationship with
                {
                    SourceId = relationship.TargetId,
                    TargetId = relationship.SourceId,
                    Bidirectional = false
                };
            }
        }
    }

    private static bool IsDuplicateSchemaObject(PostgresException exception) =>
        exception.SqlState is PostgresErrorCodes.DuplicateTable or
            PostgresErrorCodes.DuplicateObject or
            PostgresErrorCodes.UniqueViolation;

    public async ValueTask DisposeAsync()
    {
        if (_ownedConnectionManager is not null)
        {
            await _ownedConnectionManager.DisposeAsync().ConfigureAwait(false);
        }
    }
}
