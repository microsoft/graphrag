using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Npgsql;

namespace GraphRag.Storage.Postgres.ApacheAge;

public interface IAgeConnectionManager : IAsyncDisposable, IDisposable
{
    string ConnectionString { get; }
    Task<NpgsqlConnection> OpenConnectionAsync(CancellationToken cancellationToken);
    Task ReturnConnectionAsync(NpgsqlConnection connection, CancellationToken cancellationToken = default);
}

public sealed class AgeConnectionManager : IAgeConnectionManager
{
    private readonly NpgsqlDataSource _dataSource;
    private readonly ILogger<AgeConnectionManager> _logger;
    private readonly SemaphoreSlim _extensionLock = new(1, 1);
    private readonly SemaphoreSlim _poolSemaphore;
    private bool _extensionEnsured;
    private bool _disposed;

    public AgeConnectionManager(string connectionString, ILogger<AgeConnectionManager>? logger = null, int maxPoolSize = 100)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(connectionString);
        if (maxPoolSize <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(maxPoolSize), "Max pool size must be greater than zero.");
        }

        var connectionBuilder = new NpgsqlConnectionStringBuilder(connectionString)
        {
            MaxPoolSize = maxPoolSize,
            MinPoolSize = Math.Min(10, maxPoolSize)
        };

        ConnectionString = connectionBuilder.ConnectionString;
        _poolSemaphore = new SemaphoreSlim(maxPoolSize, maxPoolSize);
        _dataSource = NpgsqlDataSource.Create(connectionBuilder.ConnectionString);
        _logger = logger ?? NullLogger<AgeConnectionManager>.Instance;
    }

    public string ConnectionString { get; }

    public async Task<NpgsqlConnection> OpenConnectionAsync(CancellationToken cancellationToken)
    {
        ThrowIfDisposed();

        await _poolSemaphore.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            await EnsureExtensionCreatedAsync(cancellationToken).ConfigureAwait(false);
            var connection = await _dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
            await LoadAgeAsync(connection, cancellationToken).ConfigureAwait(false);
            await SetSearchPathAsync(connection, cancellationToken).ConfigureAwait(false);
            return connection;
        }
        catch
        {
            _poolSemaphore.Release();
            throw;
        }
    }

    public async Task ReturnConnectionAsync(NpgsqlConnection connection, CancellationToken cancellationToken = default)
    {
        if (connection is null)
        {
            _poolSemaphore.Release();
            return;
        }

        try
        {
            if (connection.FullState.HasFlag(System.Data.ConnectionState.Open))
            {
                await connection.CloseAsync().ConfigureAwait(false);
            }

            await connection.DisposeAsync().ConfigureAwait(false);
        }
        finally
        {
            _poolSemaphore.Release();
        }
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }

        _dataSource.Dispose();
        _poolSemaphore.Dispose();
        _disposed = true;
        GC.SuppressFinalize(this);
    }

    public async ValueTask DisposeAsync()
    {
        if (_disposed)
        {
            return;
        }

        await _dataSource.DisposeAsync().ConfigureAwait(false);
        _poolSemaphore.Dispose();
        _disposed = true;
        GC.SuppressFinalize(this);
    }

    private async Task EnsureExtensionCreatedAsync(CancellationToken cancellationToken)
    {
        if (_extensionEnsured)
        {
            return;
        }

        await _extensionLock.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_extensionEnsured)
            {
                return;
            }

            await using var connection = new NpgsqlConnection(ConnectionString);
            await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
            await using var command = connection.CreateCommand();
            command.CommandText = "CREATE EXTENSION IF NOT EXISTS age;";
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            _extensionEnsured = true;
            LogMessages.ExtensionCreated(_logger, ConnectionString);
        }
        finally
        {
            _extensionLock.Release();
        }
    }

    private async Task LoadAgeAsync(NpgsqlConnection connection, CancellationToken cancellationToken)
    {
        try
        {
            await using var load = connection.CreateCommand();
            load.CommandText = "LOAD 'age';";
            load.CommandTimeout = 0;
            await load.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            LogMessages.ExtensionLoaded(_logger, ConnectionString);
        }
        catch (PostgresException ex)
        {
            LogMessages.ExtensionNotLoadedError(_logger, ConnectionString, ex.MessageText);
            throw new AgeException("Could not load AGE shared library. Ensure the extension is installed and available.", ex);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            LogMessages.ExtensionNotLoadedError(_logger, ConnectionString, ex.Message);
            throw new AgeException("Could not load AGE shared library. Ensure the extension is installed and available.", ex);
        }
    }

    private async Task SetSearchPathAsync(NpgsqlConnection connection, CancellationToken cancellationToken)
    {
        try
        {
            await using var searchPath = connection.CreateCommand();
            searchPath.CommandText = @"SET search_path = ag_catalog, ""$user"", public;";
            searchPath.CommandTimeout = 0;
            await searchPath.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
            LogMessages.AgCatalogAddedToSearchPath(_logger);
        }
        catch (PostgresException ex)
        {
            LogMessages.AgCatalogNotAddedToSearchPathError(_logger, ex.MessageText);
            throw new AgeException("Could not set the search_path for AGE.", ex);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            LogMessages.AgCatalogNotAddedToSearchPathError(_logger, ex.Message);
            throw new AgeException("Could not set the search_path for AGE.", ex);
        }
    }

    private void ThrowIfDisposed() =>
        ObjectDisposedException.ThrowIf(_disposed, nameof(AgeConnectionManager));
}
