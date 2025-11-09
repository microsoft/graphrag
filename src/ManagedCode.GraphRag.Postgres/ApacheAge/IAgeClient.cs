using Npgsql;

namespace GraphRag.Storage.Postgres.ApacheAge;

/// <summary>
/// Defines clients for use with the Apache AGE extension for PostgreSQL.
/// </summary>
public interface IAgeClient : IAsyncDisposable
{
    /// <summary>
    /// Indicates if there's an open connection to the database.
    /// </summary>
    bool IsConnected { get; }

    /// <summary>
    /// The currently open connection. Throws if a connection has not been opened.
    /// </summary>
    NpgsqlConnection Connection { get; }

    /// <summary>
    /// Opens connection to the database and performs the necessary actions to create
    /// and load the AGE extension in the database.
    /// </summary>
    /// <param name="cancellationToken">
    /// Token for propagating a notification  stop the running operation.
    /// </param>
    /// <returns>
    /// A <see cref="Task"/> for monitoring the progress of the operation.
    /// </returns>
    Task OpenConnectionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a graph if it doesn't exist.
    /// </summary>
    /// <param name="graphName">
    /// Graph name.
    /// </param>
    /// <param name="cancellationToken">
    /// Token for propagating a notification to stop the running operation.
    /// </param>
    /// <returns></returns>
    Task CreateGraphAsync(
        string graphName,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Drop the given graph.
    /// </summary>
    /// <param name="graphName">
    /// Graph name.
    /// </param>
    /// <param name="cascade">
    /// Indicates that labels and data that depend on the graph should
    /// be deleted. Default is <see langword="false"/>.
    /// </param>
    /// <param name="cancellationToken">
    /// Token for propagating a notification to stop the running operation.
    /// </param>
    /// <returns></returns>
    Task DropGraphAsync(
        string graphName,
        bool cascade = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Execute the given cypher command in the database.
    /// </summary>
    /// <remarks>
    /// For queries which return values, use
    /// <see cref="ExecuteQueryAsync(string, CancellationToken)"/>.
    /// </remarks>
    /// <param name="graph">
    /// Graph name.
    /// </param>
    /// <param name="cypher">
    /// Cypher command.
    /// </param>
    /// <param name="cancellationToken">
    /// Token for propagating a notification to stop the running operation.
    /// </param>
    /// <returns>
    /// A <see cref="Task"/> for monitoring the progress of the operation.
    /// </returns>
    Task ExecuteCypherAsync(
        string graph,
        string cypher,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Execute the given query, which returns records, in the database.
    /// </summary>
    /// <remarks>
    /// For queries which don't return any value, use
    /// <see cref="ExecuteCypherAsync(string, string, CancellationToken)"/>.
    /// </remarks>
    /// <param name="query">
    /// Query.
    /// </param>
    /// <param name="cancellationToken">
    /// Token for propagating a notification to stop the running operation.
    /// </param>
    /// <param name="parameters">
    /// Query parameters, if using a parameterised query.
    /// </param>
    /// <returns>
    /// The result as <see cref="AgType"/>.
    /// </returns>
    Task<AgeDataReader> ExecuteQueryAsync(
        string query,
        CancellationToken cancellationToken = default,
        params object?[] parameters);

    /// <summary>
    /// Close connection to the database.
    /// </summary>
    /// <param name="cancellationToken">
    /// Token for propagating a notification  stop the running operation.
    /// </param>
    /// <returns>
    /// A <see cref="Task"/> for monitoring the progress of the operation.
    /// </returns>
    Task CloseConnectionAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Checks if graph exists in the database.
    /// </summary>
    /// <param name="graphName">Graph name.</param>
    /// <param name="cancellationToken">
    /// Token for propagating a notification  stop the running operation.
    /// </param>
    /// <returns><see langword="true"/> if it exists, otherwise <see langword="false"/>.</returns>
    Task<bool> GraphExistsAsync(string graphName, CancellationToken cancellationToken = default);
}
