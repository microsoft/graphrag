using System.Collections;
using System.Collections.Concurrent;
using System.Globalization;
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
    private readonly string _graphNameLiteral;
    private readonly bool _autoCreateIndexes;
    private readonly ILogger<PostgresGraphStore> _logger;
    private readonly ConcurrentDictionary<string, bool> _indexedLabels = new(StringComparer.OrdinalIgnoreCase);
    private readonly ConcurrentDictionary<string, bool> _propertyIndexes = new(StringComparer.OrdinalIgnoreCase);
    private readonly IReadOnlyDictionary<string, string[]> _vertexPropertyIndexConfig;
    private readonly IReadOnlyDictionary<string, string[]> _edgePropertyIndexConfig;

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

        _connectionString = connectionString;
        _graphName = graphName;
        _graphNameLiteral = BuildGraphNameLiteral(_graphName);
        _autoCreateIndexes = options.AutoCreateIndexes;
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        _vertexPropertyIndexConfig = NormalizeIndexMap(options.VertexPropertyIndexes);
        _edgePropertyIndexConfig = NormalizeIndexMap(options.EdgePropertyIndexes);
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await ExecuteNonQueryAsync(connection, "CREATE EXTENSION IF NOT EXISTS age;", cancellationToken);
        await ApplySessionConfigurationAsync(connection, cancellationToken);

        await using (var existsCommand = connection.CreateCommand())
        {
            existsCommand.CommandText = "SELECT 1 FROM ag_catalog.ag_graph WHERE name = @graphName LIMIT 1;";
            existsCommand.Parameters.AddWithValue("graphName", _graphName);
            var exists = await existsCommand.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);

            if (exists is null)
            {
                await using var createGraph = connection.CreateCommand();
                createGraph.CommandText = "SELECT ag_catalog.create_graph(@graphName);";
                createGraph.Parameters.AddWithValue("graphName", _graphName);
                await createGraph.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            }
        }

        _logger.LogInformation("Apache AGE graph {GraphName} initialised.", _graphName);
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentNullException.ThrowIfNull(properties);

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

        var query = queryBuilder.ToString();

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

        var query = queryBuilder.ToString();

        await EnsureLabelIndexesAsync(type, isEdge: true, cancellationToken).ConfigureAwait(false);
        await ExecuteCypherAsync(query, parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted relationship {Source}-[{Type}]->{Target} in graph {GraphName}.", sourceId, type, targetId, _graphName);
    }

    public Task EnsurePropertyKeyIndexAsync(string label, string propertyKey, bool isEdge, CancellationToken cancellationToken = default)
    {
        return EnsurePropertyKeyIndexInternalAsync(label, propertyKey, isEdge, relation: null, cancellationToken);
    }

    public async Task<IReadOnlyList<string>> ExplainAsync(string cypherQuery, IReadOnlyDictionary<string, object?>? parameters = null, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(cypherQuery);

        var explainQuery = $"EXPLAIN\n{cypherQuery}";
        var parameterJson = SerializeParameters(parameters);

        return await ExecuteExplainAsync(explainQuery, parameterJson, cancellationToken).ConfigureAwait(false);
    }

    private async Task EnsurePropertyKeyIndexInternalAsync(string label, string propertyKey, bool isEdge, string? relation, CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentException.ThrowIfNullOrWhiteSpace(propertyKey);

        var cacheKey = BuildPropertyIndexCacheKey(label, propertyKey, isEdge);
        if (!_propertyIndexes.TryAdd(cacheKey, true))
        {
            return;
        }

        relation ??= await ResolveLabelRelationAsync(label, isEdge, cancellationToken).ConfigureAwait(false);
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

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        return FetchAsync(sourceId, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchAsync(string nodeId, [EnumeratorCancellation] CancellationToken token)
        {
            await using var connection = await OpenConnectionAsync(token).ConfigureAwait(false);
            await using var command = connection.CreateCommand();
            command.CommandText = string.Concat(
                "SELECT ",
                "\n    source_id::text,",
                "\n    target_id::text,",
                "\n    edge_type::text,",
                "\n    edge_props::text",
                "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", $$",
                "\n    MATCH (source { id: $node_id })-[rel]->(target)",
                "\n    RETURN source.id AS source_id, target.id AS target_id, type(rel) AS edge_type, properties(rel) AS edge_props",
                "\n$$, @params::ag_catalog.agtype) AS (source_id agtype, target_id agtype, edge_type agtype, edge_props agtype);");
            var payload = JsonSerializer.Serialize(new Dictionary<string, object?>
            {
                [CypherParameterNames.NodeId] = nodeId
            });
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
        }
    }

    protected virtual async Task ExecuteCypherAsync(string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
    {
        await using var connection = await OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await using var command = connection.CreateCommand();
        var queryLiteral = WrapInDollarQuotes(query);
        command.CommandText = string.Concat(
            "SELECT *",
            "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", ", queryLiteral, "::cstring, @params::ag_catalog.agtype) AS (result agtype);");
        command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, SerializeParameters(parameters)));
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
        if (commands.Length > 0)
        {
            await ExecuteIndexCommandsAsync(commands, cancellationToken).ConfigureAwait(false);
            _logger.LogInformation("Ensured AGE default indexes on {Relation} ({LabelType}).", relation, isEdge ? "edge" : "vertex");
        }

        await EnsureConfiguredPropertyIndexesAsync(label, relation, isEdge, cancellationToken).ConfigureAwait(false);
    }

    private async Task EnsureConfiguredPropertyIndexesAsync(string label, string relation, bool isEdge, CancellationToken cancellationToken)
    {
        var propertyMap = isEdge ? _edgePropertyIndexConfig : _vertexPropertyIndexConfig;
        if (!propertyMap.TryGetValue(label, out var properties) || properties.Length == 0)
        {
            return;
        }

        foreach (var property in properties)
        {
            await EnsurePropertyKeyIndexInternalAsync(label, property, isEdge, relation, cancellationToken).ConfigureAwait(false);
        }
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
        var explainLiteral = WrapInDollarQuotes(explainQuery);
        command.CommandText = string.Concat(
            "SELECT plan",
            "\nFROM ag_catalog.cypher(", _graphNameLiteral, ", ", explainLiteral, "::cstring, @params::ag_catalog.agtype) AS (plan text);");
        command.Parameters.Add(CreateAgTypeParameter(CypherParameterNames.Parameters, parameterJson));

        var plan = new List<string>();
        await using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            plan.Add(reader.GetString(0));
        }

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

        return new NpgsqlParameter(name, NpgsqlDbType.Unknown)
        {
            DataTypeName = "ag_catalog.agtype",
            Value = jsonPayload
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
            assignments.Add($"{alias}.{escapedProperty} = ${parameterName}");
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
