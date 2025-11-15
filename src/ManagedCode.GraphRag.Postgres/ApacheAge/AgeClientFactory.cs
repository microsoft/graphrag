using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Npgsql;

namespace GraphRag.Storage.Postgres.ApacheAge;

public interface IAgeClientFactory
{
    IAgeClient CreateClient();
    ValueTask<IAgeClientScope> CreateScopeAsync(CancellationToken cancellationToken = default);
}

internal sealed class AgeClientFactory([FromKeyedServices] IAgeConnectionManager connectionManager, ILoggerFactory loggerFactory) : IAgeClientFactory
{
    private readonly IAgeConnectionManager _connectionManager = connectionManager ?? throw new ArgumentNullException(nameof(connectionManager));
    private readonly ILoggerFactory _loggerFactory = loggerFactory ?? throw new ArgumentNullException(nameof(loggerFactory));
    private readonly AsyncLocal<AgeClientScopeState?> _currentScope = new();

    public IAgeClient CreateClient()
    {
        if (_currentScope.Value is { } scopeState)
        {
            return scopeState.CreateLease();
        }

        return CreatePhysicalClient();
    }

    public ValueTask<IAgeClientScope> CreateScopeAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (_currentScope.Value is not null)
        {
            throw new InvalidOperationException("An AGE client scope is already active for this asynchronous context.");
        }

        var scopeClient = CreatePhysicalClient();
        var scopeState = new AgeClientScopeState(scopeClient);
        _currentScope.Value = scopeState;

        return new ValueTask<IAgeClientScope>(new ActiveAgeClientScope(this, scopeState));
    }

    private AgeClient CreatePhysicalClient()
    {
        var logger = _loggerFactory.CreateLogger<AgeClient>();
        return new AgeClient(_connectionManager, logger);
    }

    private void ClearScope(AgeClientScopeState state)
    {
        if (!ReferenceEquals(_currentScope.Value, state))
        {
            return;
        }

        _currentScope.Value = null;
    }

    private sealed class ActiveAgeClientScope(AgeClientFactory factory, AgeClientFactory.AgeClientScopeState state) : IAgeClientScope
    {
        private readonly AgeClientFactory _factory = factory;
        private readonly AgeClientScopeState _state = state;
        private bool _disposed;

        public async ValueTask DisposeAsync()
        {
            if (_disposed)
            {
                return;
            }

            if (_state.HasActiveLease)
            {
                throw new InvalidOperationException("Cannot dispose an AGE client scope while an operation is still running.");
            }

            _disposed = true;
            _factory.ClearScope(_state);
            await _state.Client.CloseConnectionAsync().ConfigureAwait(false);
            await _state.Client.DisposeAsync().ConfigureAwait(false);
        }
    }

    private sealed class AgeClientScopeState(AgeClient client)
    {
        private int _leaseActive;

        public AgeClient Client { get; } = client;

        public IAgeClient CreateLease()
        {
            if (Interlocked.CompareExchange(ref _leaseActive, 1, 0) == 1)
            {
                throw new InvalidOperationException("An AGE client scope cannot be used concurrently. Await ongoing operations before issuing new ones within the same scope.");
            }

            return new ScopedAgeClient(this);
        }

        public void ReleaseLease()
        {
            Volatile.Write(ref _leaseActive, 0);
        }

        public bool HasActiveLease => Volatile.Read(ref _leaseActive) == 1;
    }

    private sealed class ScopedAgeClient(AgeClientFactory.AgeClientScopeState state) : IAgeClient
    {
        private readonly AgeClientScopeState _state = state;
        private bool _disposed;

        public bool IsConnected => _state.Client.IsConnected;

        public NpgsqlConnection Connection => _state.Client.Connection;

        public Task OpenConnectionAsync(CancellationToken cancellationToken = default) =>
            _state.Client.OpenConnectionAsync(cancellationToken);

        public Task CreateGraphAsync(string graphName, CancellationToken cancellationToken = default) =>
            _state.Client.CreateGraphAsync(graphName, cancellationToken);

        public Task DropGraphAsync(string graphName, bool cascade = false, CancellationToken cancellationToken = default) =>
            _state.Client.DropGraphAsync(graphName, cascade, cancellationToken);

        public Task ExecuteCypherAsync(string graph, string cypher, CancellationToken cancellationToken = default) =>
            _state.Client.ExecuteCypherAsync(graph, cypher, cancellationToken);

        public Task<AgeDataReader> ExecuteQueryAsync(string query, CancellationToken cancellationToken = default, params object?[] parameters) =>
            _state.Client.ExecuteQueryAsync(query, cancellationToken, parameters);

        public Task CloseConnectionAsync(CancellationToken cancellationToken = default) =>
            Task.CompletedTask;

        public Task<bool> GraphExistsAsync(string graphName, CancellationToken cancellationToken = default) =>
            _state.Client.GraphExistsAsync(graphName, cancellationToken);

        public ValueTask DisposeAsync()
        {
            if (_disposed)
            {
                return ValueTask.CompletedTask;
            }

            _disposed = true;
            _state.ReleaseLease();
            return ValueTask.CompletedTask;
        }
    }
}
