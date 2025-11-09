namespace GraphRag.Storage.Postgres.ApacheAge;

internal static class AgeClientEventId
{
    #region Connection
    public const int CONNECTION_OPENED = 1000;
    public const int CONNECTION_CLOSED = 1001;

    public const int NULL_CONNECTION_WARNING = 1800;

    public const int OPEN_CONNECTION_ERROR = 1900;
    public const int CLOSE_CONNECTION_ERROR = 1901;
    #endregion

    #region Internals
    public const int EXTENSION_CREATED = 2101;
    public const int EXTENSION_LOADED = 2103;
    public const int RETRIEVED_CURRENT_SEARCH_PATH = 2104;
    public const int AG_CATALOG_ADDED_TO_SEARCH_PATH = 2105;

    public const int EXTENSION_NOT_CREATED_ERROR = 2900;
    public const int EXTENSION_NOT_LOADED_ERROR = 2901;
    public const int AG_CATALOG_NOT_ADDED_TO_SEARCH_PATH_ERROR = 2902;
    #endregion

    #region Commands
    public const int GRAPH_CREATED = 3001;
    public const int GRAPH_DROPPED = 3002;
    public const int GRAPH_EXISTS = 3003;
    public const int GRAPH_DOES_NOT_EXIST = 3004;

    public const int CYPHER_EXECUTED = 3101;
    public const int QUERY_EXECUTED = 3102;

    public const int GRAPH_NOT_CREATED_ERROR = 3900;
    public const int GRAPH_NOT_DROPPED_ERROR = 3901;
    public const int CYPHER_EXECUTION_ERROR = 3902;
    public const int QUERY_EXECUTION_ERROR = 3903;
    #endregion

    public const int UNKNOWN_ERROR = 9900;
}
