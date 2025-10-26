using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Graphs;
using Microsoft.Extensions.Logging;
using Npgsql;
using NpgsqlTypes;

namespace GraphRag.Storage.Postgres;

public sealed class PostgresGraphStore : IGraphStore
{
    private readonly string _connectionString;
    private readonly ILogger<PostgresGraphStore> _logger;

    public PostgresGraphStore(string connectionString, ILogger<PostgresGraphStore> logger)
    {
        _connectionString = connectionString ?? throw new ArgumentNullException(nameof(connectionString));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using (var command = connection.CreateCommand())
        {
            command.CommandText = @"CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                properties JSONB NOT NULL
            );";
            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        await using (var command = connection.CreateCommand())
        {
            command.CommandText = @"CREATE TABLE IF NOT EXISTS graph_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
                target_id TEXT NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                properties JSONB NOT NULL
            );";
            await command.ExecuteNonQueryAsync(cancellationToken);
        }

        _logger.LogInformation("PostgreSQL graph store initialised");
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);

        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = @"INSERT INTO graph_nodes(id, label, properties) VALUES (@id, @label, @props)
            ON CONFLICT (id) DO UPDATE SET label = EXCLUDED.label, properties = EXCLUDED.properties;";
        command.Parameters.AddWithValue("@id", id);
        command.Parameters.AddWithValue("@label", label);
        command.Parameters.AddWithValue("@props", NpgsqlDbType.Jsonb, JsonSerializer.Serialize(properties));
        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);

        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = @"INSERT INTO graph_edges(id, source_id, target_id, type, properties) VALUES (@id, @source, @target, @type, @props)
            ON CONFLICT (id) DO UPDATE SET type = EXCLUDED.type, properties = EXCLUDED.properties;";
        command.Parameters.AddWithValue("@id", $"{sourceId}:{type}:{targetId}");
        command.Parameters.AddWithValue("@source", sourceId);
        command.Parameters.AddWithValue("@target", targetId);
        command.Parameters.AddWithValue("@type", type);
        command.Parameters.AddWithValue("@props", NpgsqlDbType.Jsonb, JsonSerializer.Serialize(properties));
        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    public IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        return Fetch();

        async IAsyncEnumerable<GraphRelationship> Fetch([EnumeratorCancellation] CancellationToken token = default)
        {
            await using var connection = new NpgsqlConnection(_connectionString);
            await connection.OpenAsync(token);
            await using var command = connection.CreateCommand();
            command.CommandText = "SELECT source_id, target_id, type, properties::text FROM graph_edges WHERE source_id = @source";
            command.Parameters.AddWithValue("@source", sourceId);

            await using var reader = await command.ExecuteReaderAsync(token);
            while (await reader.ReadAsync(token))
            {
                var propertiesJson = reader.GetString(3);
                var properties = JsonSerializer.Deserialize<Dictionary<string, object?>>(propertiesJson) ?? new Dictionary<string, object?>();
                yield return new GraphRelationship(reader.GetString(0), reader.GetString(1), reader.GetString(2), properties);
            }
        }
    }
}
