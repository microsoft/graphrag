using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using GraphRag.Graphs;
using Microsoft.Extensions.Logging;
using Npgsql;
using NpgsqlTypes;

namespace GraphRag.Storage.Postgres;

public class PostgresGraphStore : IGraphStore, IAsyncDisposable
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

        var query = $"MERGE (n:{EscapeLabel(label)} {{ id: $node_id }}) SET n += $props RETURN n";
        var parameters = new Dictionary<string, object?>
        {
            ["node_id"] = id,
            ["props"] = ConvertProperties(properties)
        };

        await ExecuteCypherAsync(query, parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogDebug("Upserted node {Id} ({Label}) into graph {GraphName}.", id, label, _graphName);
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);
        ArgumentNullException.ThrowIfNull(properties);

        var query = $"MATCH (source {{ id: $source_id }}), (target {{ id: $target_id }}) MERGE (source)-[rel:{EscapeLabel(type)}]->(target) SET rel += $props RETURN rel";
        var parameters = new Dictionary<string, object?>
        {
            ["source_id"] = sourceId,
            ["target_id"] = targetId,
            ["props"] = ConvertProperties(properties)
        };

        await ExecuteCypherAsync(query, parameters, cancellationToken).ConfigureAwait(false);
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
            command.Parameters.AddWithValue("graph_name", _graphName);
            command.Parameters.Add(new NpgsqlParameter("params", NpgsqlDbType.Jsonb)
            {
                Value = JsonSerializer.Serialize(new Dictionary<string, object?>
                {
                    ["node_id"] = nodeId
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
        command.Parameters.AddWithValue("graph_name", _graphName);
        command.Parameters.AddWithValue("query", query);
        command.Parameters.Add(new NpgsqlParameter("params", NpgsqlDbType.Jsonb)
        {
            Value = JsonSerializer.Serialize(parameters)
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
            if (value is null || string.Equals(key, "id", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            result[key] = value switch
            {
                string s => s,
                int or long or short or byte => Convert.ToInt64(value, CultureInfo.InvariantCulture),
                float or double or decimal => Convert.ToDouble(value, CultureInfo.InvariantCulture),
                bool b => b,
                DateTime dt => dt.ToUniversalTime(),
                IEnumerable<string> list => list.ToArray(),
                _ => value.ToString()
            };
        }

        return result;
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
