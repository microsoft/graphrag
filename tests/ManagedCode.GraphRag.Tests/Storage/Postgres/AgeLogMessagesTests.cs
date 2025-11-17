using GraphRag.Storage.Postgres.ApacheAge;
using Microsoft.Extensions.Logging.Abstractions;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

public sealed class AgeLogMessagesTests
{
    [Fact]
    public void LogMessages_ConnectionScenarios_DoNotThrow()
    {
        var logger = NullLogger.Instance;
        LogMessages.ConnectionOpened(logger, "conn");
        LogMessages.ConnectionClosed(logger, "conn");
        LogMessages.ConnectionRetrying(logger, "conn", 1, TimeSpan.FromMilliseconds(50), "retry");
        LogMessages.NoExistingConnectionWarning(logger, "warning");
        LogMessages.OpenConnectionError(logger, "open", new InvalidOperationException());
        LogMessages.CloseConnectionError(logger, "close", new InvalidOperationException());
    }

    [Fact]
    public void LogMessages_InternalOperations_DoNotThrow()
    {
        var logger = NullLogger.Instance;
        LogMessages.ExtensionCreated(logger, "conn");
        LogMessages.ExtensionLoaded(logger, "conn");
        LogMessages.RetrievedCurrentSearchPath(logger, "ag_catalog");
        LogMessages.AgCatalogAddedToSearchPath(logger);
        LogMessages.ExtensionNotCreatedError(logger, "conn", "reason");
        LogMessages.ExtensionNotLoadedError(logger, "conn", "reason");
        LogMessages.AgCatalogNotAddedToSearchPathError(logger, "reason");
    }

    [Fact]
    public void LogMessages_CommandOperations_DoNotThrow()
    {
        var logger = NullLogger.Instance;
        LogMessages.GraphCreated(logger, "graph");
        LogMessages.GraphNotCreatedError(logger, "graph", "reason", new InvalidOperationException());
        LogMessages.GraphDropped(logger, "graph", true);
        LogMessages.CypherExecuted(logger, "graph", "cypher");
        LogMessages.QueryExecuted(logger, "query");
        LogMessages.GraphExists(logger, "graph");
        LogMessages.GraphDoesNotExist(logger, "graph");
        LogMessages.GraphNotDroppedError(logger, "graph", "reason", new InvalidOperationException());
        LogMessages.CypherExecutionError(logger, "graph", "cypher", new InvalidOperationException());
        LogMessages.QueryExecutionError(logger, "reason", "query", new InvalidOperationException());
    }
}
