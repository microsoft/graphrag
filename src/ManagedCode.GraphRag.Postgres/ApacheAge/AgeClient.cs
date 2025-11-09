using System.Data;
using Microsoft.Extensions.Logging;
using Npgsql;

namespace GraphRag.Storage.Postgres.ApacheAge;

/// <summary>
/// Client for interacting with the Apache AGE extension for PostgreSQL.
/// </summary>
public sealed class AgeClient(IAgeConnectionManager connectionManager, ILogger<AgeClient> logger) : IAgeClient, IAsyncDisposable, IDisposable
{
    private readonly IAgeConnectionManager _connectionManager = connectionManager ?? throw new ArgumentNullException(nameof(connectionManager));
    private readonly ILogger<AgeClient> _logger = logger ?? throw new ArgumentNullException(nameof(logger));

    private NpgsqlConnection? _connection;
    private bool _disposed;

    public string ConnectionString => Volatile.Read(ref _connection)?.ConnectionString ?? _connectionManager.ConnectionString;

    public bool IsConnected
    {
        get
        {
            var connection = Volatile.Read(ref _connection);
            return connection is { } existing && existing.FullState.HasFlag(ConnectionState.Open);
        }
    }

    public NpgsqlConnection Connection =>
        Volatile.Read(ref _connection) ?? throw new InvalidOperationException("AGE connection is not open.");

    public async Task OpenConnectionAsync(CancellationToken cancellationToken = default)
    {
        ThrowIfDisposed();

        var existing = Volatile.Read(ref _connection);
        if (existing is { FullState: var state } && state.HasFlag(ConnectionState.Open))
        {
            return;
        }

        try
        {
            var connection = await _connectionManager.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
            existing = Interlocked.Exchange(ref _connection, connection);

            if (existing is not null)
            {
                await existing.DisposeAsync().ConfigureAwait(false);
            }

            LogMessages.ConnectionOpened(_logger, ConnectionString);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            LogMessages.OpenConnectionError(_logger, ex.Message, ex);
            throw new AgeException("Could not connect to the database.", ex);
        }
    }

    public async Task CloseConnectionAsync(CancellationToken cancellationToken = default)
    {
        var connection = Interlocked.Exchange(ref _connection, null);
        if (connection is null)
        {
            return;
        }

        try
        {
            await _connectionManager.ReturnConnectionAsync(connection, cancellationToken).ConfigureAwait(false);
            LogMessages.ConnectionClosed(_logger, ConnectionString);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            LogMessages.CloseConnectionError(_logger, ex.Message, ex);
            throw new AgeException("Could not close the existing connection to the database.", ex);
        }
    }

    public async Task CreateGraphAsync(string graphName, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(graphName);
        CheckForExistingConnection();

        if (await GraphExistsAsync(graphName, cancellationToken).ConfigureAwait(false))
        {
            return;
        }

        await using var command = new NpgsqlCommand("SELECT * FROM ag_catalog.create_graph($1);", _connection)
        {
            Parameters =
            {
                new NpgsqlParameter { Value = graphName }
            }
        };

        try
        {
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            LogMessages.GraphCreated(_logger, graphName);
        }
        catch (PostgresException ex)
        {
            LogMessages.GraphNotCreatedError(_logger, graphName, ex.MessageText, ex);
            throw new AgeException($"Could not create graph '{graphName}'.", ex);
        }
        catch (Exception ex)
        {
            LogMessages.GraphNotCreatedError(_logger, graphName, ex.Message, ex);
            throw new AgeException($"Could not create graph '{graphName}'.", ex);
        }
    }

    public async Task DropGraphAsync(string graphName, bool cascade = false, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(graphName);
        CheckForExistingConnection();

        await using var command = new NpgsqlCommand("SELECT * FROM ag_catalog.drop_graph($1, $2);", _connection)
        {
            Parameters =
            {
                new NpgsqlParameter { Value = graphName },
                new NpgsqlParameter { Value = cascade }
            }
        };

        try
        {
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            LogMessages.GraphDropped(_logger, graphName, cascade);
        }
        catch (PostgresException ex)
        {
            LogMessages.GraphNotDroppedError(_logger, graphName, ex.MessageText, ex);
            throw new AgeException($"Could not drop graph '{graphName}'.", ex);
        }
        catch (Exception ex)
        {
            LogMessages.GraphNotDroppedError(_logger, graphName, ex.Message, ex);
            throw new AgeException($"Could not drop graph '{graphName}'.", ex);
        }
    }

    public async Task ExecuteCypherAsync(string graph, string cypher, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(graph);
        ArgumentException.ThrowIfNullOrWhiteSpace(cypher);
        CheckForExistingConnection();

        await using var command = new NpgsqlCommand(
            $"SELECT * FROM ag_catalog.cypher('{graph}', $$ {cypher} $$) as (result ag_catalog.agtype);",
            _connection);

        try
        {
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            LogMessages.CypherExecuted(_logger, graph, cypher);
        }
        catch (PostgresException ex)
        {
            LogMessages.CypherExecutionError(
                _logger,
                $"Graph: {graph}. {ex.MessageText}",
                cypher,
                ex);
            throw new AgeException($"Could not execute Cypher command. Graph: {graph}. Cypher: {cypher}", ex);
        }
        catch (Exception ex)
        {
            LogMessages.CypherExecutionError(
                _logger,
                $"Graph: {graph}. {ex.Message}",
                cypher,
                ex);
            throw new AgeException($"Could not execute Cypher command. Graph: {graph}. Cypher: {cypher}", ex);
        }
    }

    public async Task<AgeDataReader> ExecuteQueryAsync(string query, CancellationToken cancellationToken = default, params object?[] parameters)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(query);
        CheckForExistingConnection();

        await using var command = new NpgsqlCommand(query, _connection)
        {
            AllResultTypesAreUnknown = true
        };

        foreach (var parameter in BuildParameters(parameters))
        {
            command.Parameters.Add(parameter);
        }

        try
        {
            var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            LogMessages.QueryExecuted(_logger, query);
            return new AgeDataReader(reader);
        }
        catch (PostgresException ex)
        {
            LogMessages.QueryExecutionError(_logger, query, ex.MessageText, ex);
            throw new AgeException("Could not execute query.", ex);
        }
        catch (Exception ex)
        {
            LogMessages.QueryExecutionError(_logger, query, ex.Message, ex);
            throw new AgeException("Could not execute query.", ex);
        }
    }

    public async Task<bool> GraphExistsAsync(string graphName, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(graphName);
        CheckForExistingConnection();

        const string graphExistsQuery = "SELECT name FROM ag_catalog.ag_graph WHERE name = $1;";

        await using var command = new NpgsqlCommand(
            graphExistsQuery,
            _connection)
        {
            Parameters =
            {
                new NpgsqlParameter { Value = graphName }
            }
        };

        try
        {
            var graph = await command.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);
            var exists = graph != null;

            if (exists)
            {
                LogMessages.GraphExists(_logger, graphName);
            }
            else
            {
                LogMessages.GraphDoesNotExist(_logger, graphName);
            }

            return exists;
        }
        catch (PostgresException ex)
        {
            LogMessages.QueryExecutionError(_logger, graphExistsQuery, ex.MessageText, ex);
            throw new AgeException($"Could not verify graph '{graphName}'.", ex);
        }
        catch (Exception ex)
        {
            LogMessages.QueryExecutionError(_logger, graphExistsQuery, ex.Message, ex);
            throw new AgeException($"Could not verify graph '{graphName}'.", ex);
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (_disposed)
        {
            return;
        }

        _disposed = true;
        var connection = Interlocked.Exchange(ref _connection, null);
        if (connection is not null)
        {
            await _connectionManager.ReturnConnectionAsync(connection).ConfigureAwait(false);
        }

        GC.SuppressFinalize(this);
    }

    public void Dispose()
    {
        DisposeAsync().AsTask().GetAwaiter().GetResult();
    }

    private static IEnumerable<NpgsqlParameter> BuildParameters(object?[] parameters)
    {
        if (parameters == null || parameters.Length == 0)
        {
            yield break;
        }

        foreach (var parameter in parameters)
        {
            yield return new NpgsqlParameter { Value = parameter };
        }
    }

    private void CheckForExistingConnection()
    {
        ThrowIfDisposed();

        if (Volatile.Read(ref _connection) is not null)
        {
            return;
        }

        LogMessages.NoExistingConnectionWarning(
            _logger,
            "An attempt to perform certain action was made when there is no existing connection to the database");

        throw new AgeException("There is no existing connection to the database. Call OpenConnectionAsync() to open a connection.");
    }

    private void ThrowIfDisposed() =>
        ObjectDisposedException.ThrowIf(_disposed, nameof(AgeClient));
}
