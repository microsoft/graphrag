using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Postgres.ApacheAge;

internal static partial class LogMessages
{
    #region Connection

    [LoggerMessage(
    EventId = AgeClientEventId.CONNECTION_OPENED,
    Level = LogLevel.Debug,
    Message = "Connection opened to {connectionString}")]
    public static partial void ConnectionOpened(
        ILogger logger,
        string connectionString);

    [LoggerMessage(
    EventId = AgeClientEventId.CONNECTION_CLOSED,
    Level = LogLevel.Debug,
    Message = "Connection to {connectionString} closed")]
    public static partial void ConnectionClosed(
        ILogger logger,
        string connectionString);

    [LoggerMessage(
    EventId = AgeClientEventId.NULL_CONNECTION_WARNING,
    Level = LogLevel.Warning,
    Message = "{message}")]
    public static partial void NoExistingConnectionWarning(
        ILogger logger,
        string message);

    [LoggerMessage(
    EventId = AgeClientEventId.OPEN_CONNECTION_ERROR,
    Level = LogLevel.Error,
    Message = "{message}",
    SkipEnabledCheck = true)]
    public static partial void OpenConnectionError(
        ILogger logger,
        string message,
        Exception exception);

    [LoggerMessage(
    EventId = AgeClientEventId.CLOSE_CONNECTION_ERROR,
    Level = LogLevel.Error,
    Message = "{message}",
    SkipEnabledCheck = true)]
    public static partial void CloseConnectionError(
        ILogger logger,
        string message,
        Exception exception);

    #endregion

    #region Internals

    [LoggerMessage(
        EventId = AgeClientEventId.EXTENSION_CREATED,
        Level = LogLevel.Debug,
        Message = "Created 'age' extension in {connectionString}")]
    public static partial void ExtensionCreated(
        ILogger logger,
        string connectionString);

    [LoggerMessage(
        EventId = AgeClientEventId.EXTENSION_LOADED,
        Level = LogLevel.Debug,
        Message = "Loaded 'age' in {connectionString}")]
    public static partial void ExtensionLoaded(
        ILogger logger,
        string connectionString);

    [LoggerMessage(
        EventId = AgeClientEventId.RETRIEVED_CURRENT_SEARCH_PATH,
        Level = LogLevel.Debug,
        Message = "Retrieved current search_path. search_path = {searchPath}")]
    public static partial void RetrievedCurrentSearchPath(
        ILogger logger,
        string? searchPath);

    [LoggerMessage(
        EventId = AgeClientEventId.AG_CATALOG_ADDED_TO_SEARCH_PATH,
        Level = LogLevel.Debug,
        Message = "'ag_catalog' added to search_path")]
    public static partial void AgCatalogAddedToSearchPath(
        ILogger logger);

    #region Error Logs

    [LoggerMessage(
    EventId = AgeClientEventId.EXTENSION_NOT_CREATED_ERROR,
    Level = LogLevel.Warning,
    Message = "AGE extension not created in {connectionString}. Reason: {reason}",
    SkipEnabledCheck = true)]
    public static partial void ExtensionNotCreatedError(
    ILogger logger,
    string connectionString,
    string reason);

    [LoggerMessage(
        EventId = AgeClientEventId.EXTENSION_NOT_LOADED_ERROR,
        Level = LogLevel.Warning,
        Message = "AGE extension not loaded in {connectionString}. Reason: {reason}",
        SkipEnabledCheck = true)]
    public static partial void ExtensionNotLoadedError(
        ILogger logger,
        string connectionString,
        string reason);

    [LoggerMessage(
        EventId = AgeClientEventId.AG_CATALOG_NOT_ADDED_TO_SEARCH_PATH_ERROR,
        Level = LogLevel.Warning,
        Message = "'ag_catalog' could not be added to search_path. Reason: {reason}. Will use the full qualified name instead")]
    public static partial void AgCatalogNotAddedToSearchPathError(
        ILogger logger,
        string reason);

    #endregion
    #endregion

    #region Commands

    [LoggerMessage(
        EventId = AgeClientEventId.GRAPH_CREATED,
        Level = LogLevel.Information,
        Message = "Created graph '{graphName}'")]
    public static partial void GraphCreated(
        ILogger logger,
        string graphName);

    [LoggerMessage(
        EventId = AgeClientEventId.GRAPH_NOT_CREATED_ERROR,
        Level = LogLevel.Error,
        Message = "Could not droppe graph '{graphName}'. Reason: {reason}")]
    public static partial void GraphNotCreatedError(
        ILogger logger,
        string graphName,
        string reason,
        Exception exception);

    [LoggerMessage(
        EventId = AgeClientEventId.GRAPH_DROPPED,
        Level = LogLevel.Information,
        Message = "Dropped graph '{graphName}'. Cascade: {cascade}")]
    public static partial void GraphDropped(
        ILogger logger,
        string graphName,
        bool cascade);

    [LoggerMessage(
        EventId = AgeClientEventId.CYPHER_EXECUTED,
        Level = LogLevel.Information,
        Message = "Executed Cypher\nGraph: {graph}\nCypher: {cypher}")]
    public static partial void CypherExecuted(
        ILogger logger,
        string graph,
        string cypher);

    [LoggerMessage(
        EventId = AgeClientEventId.QUERY_EXECUTED,
        Level = LogLevel.Information,
        Message = "Executed query\nQuery: {query}")]
    public static partial void QueryExecuted(
        ILogger logger,
        string query);

    [LoggerMessage(
        EventId = AgeClientEventId.GRAPH_EXISTS,
        Level = LogLevel.Information,
        Message = "Graph '{graph}' exists")]
    public static partial void GraphExists(
        ILogger logger,
        string graph);

    [LoggerMessage(
        EventId = AgeClientEventId.GRAPH_DOES_NOT_EXIST,
        Level = LogLevel.Information,
        Message = "Graph '{graph}' does not exist")]
    public static partial void GraphDoesNotExist(
        ILogger logger,
        string graph);

    #region Error logs

    [LoggerMessage(
    EventId = AgeClientEventId.GRAPH_NOT_DROPPED_ERROR,
    Level = LogLevel.Error,
    Message = "Could not drop graph '{graphName}'. Reason: {reason}")]
    public static partial void GraphNotDroppedError(
    ILogger logger,
    string graphName,
    string reason,
    Exception exception);

    [LoggerMessage(
        EventId = AgeClientEventId.CYPHER_EXECUTION_ERROR,
        Level = LogLevel.Error,
        Message = "Cypher did not execute properly. Reason: {reason}\nQuery: {cypherQuery}")]
    public static partial void CypherExecutionError(
        ILogger logger,
        string reason,
        string cypherQuery,
        Exception exception);

    [LoggerMessage(
        EventId = AgeClientEventId.QUERY_EXECUTION_ERROR,
        Level = LogLevel.Error,
        Message = "Query did not execute properly. Reason: {reason}\nQuery: {query}")]
    public static partial void QueryExecutionError(
        ILogger logger,
        string query,
        string reason,
        Exception exception);

    #endregion
    #endregion

    [LoggerMessage(
        EventId = AgeClientEventId.UNKNOWN_ERROR,
        Level = LogLevel.Error,
        Message = "Uknown error occurred")]
    public static partial void UnknownError(
        ILogger logger,
        Exception exception);
}
