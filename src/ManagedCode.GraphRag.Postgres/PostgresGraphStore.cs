using System.Collections.Generic;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using GraphRag.Graphs;
using Microsoft.Extensions.Logging;
using Npgsql;

namespace GraphRag.Storage.Postgres;

public sealed class PostgresGraphStore : IGraphStore
{
    private readonly string _connectionString;
    private readonly string _graphName;
    private readonly ILogger<PostgresGraphStore> _logger;

    public PostgresGraphStore(string connectionString, string graphName, ILogger<PostgresGraphStore> logger)
    {
        _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));
        _graphName = graphName ?? throw new ArgumentNullException(nameof(graphName));
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

        var cypher = BuildNodeUpsertCypher(id, label, properties);
        await ExecuteCypherAsync(cypher, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted node {Id} ({Label}) into graph {GraphName}.", id, label, _graphName);
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);
        ArgumentNullException.ThrowIfNull(properties);

        var cypher = BuildRelationshipUpsertCypher(sourceId, targetId, type, properties);
        await ExecuteCypherAsync(cypher, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted relationship {Source}-[{Type}]->{Target} in graph {GraphName}.", sourceId, type, targetId, _graphName);
    }

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        return FetchAsync(sourceId, cancellationToken);

        async IAsyncEnumerable<GraphRelationship> FetchAsync(string nodeId, [EnumeratorCancellation] CancellationToken token)
        {
            await using var connection = await OpenConnectionAsync(token).ConfigureAwait(false);
            await using var command = connection.CreateCommand();
            command.CommandText = $@"
SELECT 
    source_id::text,
    target_id::text,
    edge_type::text,
    edge_props::text
FROM cypher('{_graphName}', $$
    MATCH (source {{ id: '{EscapeString(nodeId)}' }})-[rel]->(target)
    RETURN source.id AS source_id, target.id AS target_id, type(rel) AS edge_type, properties(rel) AS edge_props
$$) AS (source_id agtype, target_id agtype, edge_type agtype, edge_props agtype);
";

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

    private async Task ExecuteCypherAsync(string statement, CancellationToken cancellationToken)
    {
        await using var connection = await OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await using var command = connection.CreateCommand();
        command.CommandText = statement;
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

    private string BuildNodeUpsertCypher(string id, string label, IReadOnlyDictionary<string, object?> properties)
    {
        var builder = new StringBuilder();
        builder.AppendLine($"SELECT * FROM cypher('{_graphName}', $$");
        builder.Append("    MERGE (n:");
        builder.Append(EscapeLabel(label));
        builder.Append(" { id: '");
        builder.Append(EscapeString(id));
        builder.Append("' })");

        var setClause = BuildSetClause("n", properties, excludeId: true);
        if (!string.IsNullOrEmpty(setClause))
        {
            builder.AppendLine();
            builder.Append("    ");
            builder.Append(setClause);
        }

        builder.AppendLine();
        builder.AppendLine("RETURN n");
        builder.Append("$$) AS (n agtype);");
        return builder.ToString();
    }

    private string BuildRelationshipUpsertCypher(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties)
    {
        var builder = new StringBuilder();
        builder.AppendLine($"SELECT * FROM cypher('{_graphName}', $$");
        builder.AppendLine($"    MATCH (source {{ id: '{EscapeString(sourceId)}' }}), (target {{ id: '{EscapeString(targetId)}' }})");
        builder.Append("    MERGE (source)-[rel:");
        builder.Append(EscapeLabel(type));
        builder.Append("]->(target)");

        var setClause = BuildSetClause("rel", properties, excludeId: false);
        if (!string.IsNullOrEmpty(setClause))
        {
            builder.AppendLine();
            builder.Append("    ");
            builder.Append(setClause);
        }

        builder.AppendLine();
        builder.AppendLine("RETURN rel");
        builder.Append("$$) AS (rel agtype);");
        return builder.ToString();
    }

    private static string BuildSetClause(string alias, IReadOnlyDictionary<string, object?> properties, bool excludeId)
    {
        var assignments = new List<string>();
        foreach (var (key, value) in properties)
        {
            if (value is null)
            {
                continue;
            }

            if (excludeId && string.Equals(key, "id", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            assignments.Add($"{EscapePropertyKey(key)}: {FormatValue(value)}");
        }

        return assignments.Count == 0 ? string.Empty : $"SET {alias} += {{{string.Join(", ", assignments)}}}";
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

    private static string EscapePropertyKey(string key)
    {
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new ArgumentException("Property key cannot be null or whitespace.", nameof(key));
        }

        foreach (var ch in key)
        {
            if (!char.IsLetterOrDigit(ch) && ch != '_')
            {
                throw new ArgumentException($"Invalid character '{ch}' in property key '{key}'.", nameof(key));
            }
        }

        return key;
    }

    private static string EscapeString(string value) => value.Replace("'", "''", StringComparison.Ordinal);

    private static string FormatValue(object value) => value switch
    {
        null => "null",
        string s => $"'{EscapeString(s)}'",
        bool b => b ? "true" : "false",
        int or long or short or byte => Convert.ToString(value, CultureInfo.InvariantCulture)!,
        float f => f.ToString(CultureInfo.InvariantCulture),
        double d => d.ToString(CultureInfo.InvariantCulture),
        decimal dec => dec.ToString(CultureInfo.InvariantCulture),
        Guid guid => $"'{guid:D}'",
        DateTime dt => $"'{dt.ToUniversalTime():O}'",
        DateTimeOffset dto => $"'{dto.ToUniversalTime():O}'",
        _ => $"'{EscapeString(value.ToString() ?? string.Empty)}'"
    };

    private static Dictionary<string, object?> ParseProperties(string json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        }

        using var document = JsonDocument.Parse(json);
        if (document.RootElement.ValueKind != JsonValueKind.Object)
        {
            return new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        }

        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var property in document.RootElement.EnumerateObject())
        {
            result[property.Name] = ConvertJsonElement(property.Value);
        }

        return result;
    }

    private static object? ConvertJsonElement(JsonElement element) => element.ValueKind switch
    {
        JsonValueKind.Null => null,
        JsonValueKind.String => element.GetString(),
        JsonValueKind.Number when element.TryGetInt64(out var longValue) => longValue,
        JsonValueKind.Number => element.GetDouble(),
        JsonValueKind.True => true,
        JsonValueKind.False => false,
        JsonValueKind.Array => element.EnumerateArray().Select(ConvertJsonElement).ToArray(),
        JsonValueKind.Object => element.EnumerateObject().ToDictionary(prop => prop.Name, prop => ConvertJsonElement(prop.Value), StringComparer.OrdinalIgnoreCase),
        _ => null
    };

    private static string NormalizeAgTypeText(string value)
    {
        if (string.IsNullOrEmpty(value))
        {
            return value;
        }

        if (value.Length >= 2 && ((value[0] == '"' && value[^1] == '"') || (value[0] == '\'' && value[^1] == '\'')))
        {
            return value[1..^1];
        }

        return value;
    }
}
