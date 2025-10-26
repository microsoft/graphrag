using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using GraphRag.Constants;
using GraphRag.Graphs;
using Microsoft.Extensions.Logging;
using Npgsql;
using NpgsqlTypes;

namespace GraphRag.Storage.Postgres;

public class PostgresGraphStore : IGraphStore, IAsyncDisposable
{
    private readonly string _connectionString;
    private readonly string _graphName;
    private readonly bool _autoCreateIndexes;
    private readonly ILogger<PostgresGraphStore> _logger;
    private readonly ConcurrentDictionary<string, bool> _indexedLabels = new(StringComparer.OrdinalIgnoreCase);
    private readonly ConcurrentDictionary<string, bool> _propertyIndexes = new(StringComparer.OrdinalIgnoreCase);

    public PostgresGraphStore(string connectionString, string graphName, ILogger<PostgresGraphStore> logger)
        : this(new PostgresGraphStoreOptions
        {
            ConnectionString = connectionString,
            GraphName = graphName
        }, logger)
    {
    }

    public PostgresGraphStore(PostgresGraphStoreOptions options, ILogger<PostgresGraphStore> logger)
    {
        ArgumentNullException.ThrowIfNull(options);

        _connectionString = options.ConnectionString ?? throw new ArgumentNullException(nameof(options.ConnectionString));
        _graphName = options.GraphName ?? throw new ArgumentNullException(nameof(options.GraphName));
        _autoCreateIndexes = options.AutoCreateIndexes;
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await ExecuteNonQueryAsync(connection, "CREATE EXTENSION IF NOT EXISTS age;", cancellationToken);
        await ApplySessionConfigurationAsync(connection, cancellationToken);

        await using var ensureGraph = connection.CreateCommand();
        ensureGraph.CommandText = @"
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = @graphName) THEN
        PERFORM ag_catalog.create_graph(@graphName);
    END IF;
END $$;";
        ensureGraph.Parameters.AddWithValue("graphName", _graphName);
        await ensureGraph.ExecuteNonQueryAsync(cancellationToken);

        _logger.LogInformation("Apache AGE graph {GraphName} initialised.", _graphName);
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentNullException.ThrowIfNull(properties);

        var query = $"MERGE (n:{EscapeLabel(label)} {{ id: ${CypherParameterNames.NodeId} }}) SET n += ${CypherParameterNames.Properties} RETURN n";
        var parameters = new Dictionary<string, object?>
        {
            [CypherParameterNames.NodeId] = id,
            [CypherParameterNames.Properties] = ConvertProperties(properties)
        };

        await EnsureLabelIndexesAsync(label, isEdge: false, cancellationToken).ConfigureAwait(false);
        await ExecuteCypherAsync(query, parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted node {Id} ({Label}) into graph {GraphName}.", id, label, _graphName);
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);
        ArgumentNullException.ThrowIfNull(properties);

        var query = $"MATCH (source {{ id: ${CypherParameterNames.SourceId} }}), (target {{ id: ${CypherParameterNames.TargetId} }}) MERGE (source)-[rel:{EscapeLabel(type)}]->(target) SET rel += ${CypherParameterNames.Properties} RETURN rel";
        var parameters = new Dictionary<string, object?>
        {
            [CypherParameterNames.SourceId] = sourceId,
            [CypherParameterNames.TargetId] = targetId,
            [CypherParameterNames.Properties] = ConvertProperties(properties)
        };

        await EnsureLabelIndexesAsync(type, isEdge: true, cancellationToken).ConfigureAwait(false);
        await ExecuteCypherAsync(query, parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted relationship {Source}-[{Type}]->{Target} in graph {GraphName}.", sourceId, type, targetId, _graphName);
    }

    public async Task EnsurePropertyKeyIndexAsync(string label, string propertyKey, bool isEdge, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentException.ThrowIfNullOrWhiteSpace(propertyKey);

        var cacheKey = BuildPropertyIndexCacheKey(label, propertyKey, isEdge);
        if (!_propertyIndexes.TryAdd(cacheKey, true))
        {
            return;
        }

        var relation = await ResolveLabelRelationAsync(label, isEdge, cancellationToken).ConfigureAwait(false);
        if (string.IsNullOrEmpty(relation))
        {
            _propertyIndexes.TryRemove(cacheKey, out _);
            return;
        }

        var indexNameSuffix = $"prop_{SanitizeIdentifier(propertyKey)}";
        var indexName = BuildIndexName(relation, indexNameSuffix);
        var columnExpression = $"agtype_access_operator(VARIADIC ARRAY[properties, '\"{propertyKey}\"'::agtype])";
        var command = $"CREATE INDEX IF NOT EXISTS {indexName} ON {relation} USING BTREE ({columnExpression});";

        await ExecuteIndexCommandsAsync(new[] { command }, cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Ensured targeted index {Index} on {Relation} for property {Property}.", indexName, relation, propertyKey);
    }

    public async Task<IReadOnlyList<string>> ExplainAsync(string cypherQuery, IReadOnlyDictionary<string, object?>? parameters = null, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(cypherQuery);

        var explainQuery = $"EXPLAIN\n{cypherQuery}";
        var parameterJson = SerializeParameters(parameters);

        return await ExecuteExplainAsync(explainQuery, parameterJson, cancellationToken).ConfigureAwait(false);
    }

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        return FetchAsync(sourceId, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchAsync(string nodeId, [EnumeratorCancellation] CancellationToken token)
        {
            await using var connection = await OpenConnectionAsync(token).ConfigureAwait(false);
            await using var command = connection.CreateCommand();
            command.CommandText = @"
SELECT 
    source_id::text,
    target_id::text,
    edge_type::text,
    edge_props::text
FROM cypher(@graph_name, $$
    MATCH (source { id: $node_id })-[rel]->(target)
    RETURN source.id AS source_id, target.id AS target_id, type(rel) AS edge_type, properties(rel) AS edge_props
$$, @params) AS (source_id agtype, target_id agtype, edge_type agtype, edge_props agtype);
";
            command.Parameters.AddWithValue(CypherParameterNames.GraphName, _graphName);
            command.Parameters.Add(new NpgsqlParameter(CypherParameterNames.Parameters, NpgsqlDbType.Jsonb)
            {
                Value = JsonSerializer.Serialize(new Dictionary<string, object?>
                {
                    [CypherParameterNames.NodeId] = nodeId
                })
            });

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
        }
    }

    protected virtual async Task ExecuteCypherAsync(string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
    {
        await using var connection = await OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await using var command = connection.CreateCommand();
        command.CommandText = @"
SELECT *
FROM cypher(@graph_name, @query, @params) AS (result agtype);
";
        command.Parameters.AddWithValue(CypherParameterNames.GraphName, _graphName);
        command.Parameters.AddWithValue(CypherParameterNames.Query, query);
        command.Parameters.Add(new NpgsqlParameter(CypherParameterNames.Parameters, NpgsqlDbType.Jsonb)
        {
            Value = SerializeParameters(parameters)
        });
        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    private async Task<NpgsqlConnection> OpenConnectionAsync(CancellationToken cancellationToken)
    {
        var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        await ApplySessionConfigurationAsync(connection, cancellationToken).ConfigureAwait(false);
        return connection;
    }

    private static async Task ApplySessionConfigurationAsync(NpgsqlConnection connection, CancellationToken cancellationToken)
    {
        await ExecuteNonQueryAsync(connection, "LOAD 'age';", cancellationToken).ConfigureAwait(false);
        await ExecuteNonQueryAsync(connection, @"SET search_path = ag_catalog, ""$user"", public;", cancellationToken).ConfigureAwait(false);
    }

    private static async Task ExecuteNonQueryAsync(NpgsqlConnection connection, string sql, CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = sql;
        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
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

    private async Task EnsureLabelIndexesAsync(string label, bool isEdge, CancellationToken cancellationToken)
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

        var relation = await ResolveLabelRelationAsync(label, isEdge, cancellationToken).ConfigureAwait(false);
        if (string.IsNullOrEmpty(relation))
        {
            _indexedLabels.TryRemove(cacheKey, out _);
            return;
        }

        var commands = BuildDefaultIndexCommands(relation, isEdge).ToArray();
        if (commands.Length == 0)
        {
            return;
        }

        await ExecuteIndexCommandsAsync(commands, cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Ensured AGE default indexes on {Relation} ({LabelType}).", relation, isEdge ? "edge" : "vertex");
    }

    protected virtual async Task<string?> ResolveLabelRelationAsync(string label, bool isEdge, CancellationToken cancellationToken)
    {
        await using var connection = await OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        const string sql = @"
SELECT quote_ident(n.nspname) || '.' || quote_ident(c.relname)
FROM ag_catalog.ag_label l
JOIN ag_catalog.ag_graph g ON g.graphid = l.graph
JOIN pg_class c ON c.oid = l.relation
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE g.name = @graph_name AND l.name = @label_name AND l.kind = @label_kind
LIMIT 1;";

        await using var command = connection.CreateCommand();
        command.CommandText = sql;
        command.Parameters.AddWithValue("graph_name", _graphName);
        command.Parameters.AddWithValue("label_name", label);
        command.Parameters.AddWithValue("label_kind", isEdge ? "e" : "v");

        var result = await command.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);
        return result as string;
    }

    protected virtual async Task ExecuteIndexCommandsAsync(IEnumerable<string> commands, CancellationToken cancellationToken)
    {
        await using var connection = await OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        foreach (var commandText in commands)
        {
            await using var command = connection.CreateCommand();
            command.CommandText = commandText;
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    protected virtual async Task<IReadOnlyList<string>> ExecuteExplainAsync(string explainQuery, string parameterJson, CancellationToken cancellationToken)
    {
        await using var connection = await OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await using var command = connection.CreateCommand();
        command.CommandText = @"
SELECT plan
FROM cypher(@graph_name, @query, @params) AS (plan text);";
        command.Parameters.AddWithValue(CypherParameterNames.GraphName, _graphName);
        command.Parameters.AddWithValue(CypherParameterNames.Query, explainQuery);
        command.Parameters.Add(new NpgsqlParameter(CypherParameterNames.Parameters, NpgsqlDbType.Jsonb)
        {
            Value = parameterJson
        });

        var plan = new List<string>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            plan.Add(reader.GetString(0));
        }

        return plan;
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

    public ValueTask DisposeAsync() => ValueTask.CompletedTask;
}
