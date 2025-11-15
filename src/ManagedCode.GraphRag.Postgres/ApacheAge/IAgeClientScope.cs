namespace GraphRag.Storage.Postgres.ApacheAge;

/// <summary>
/// Represents a scope that keeps an AGE connection alive for the lifetime of the scope.
/// </summary>
public interface IAgeClientScope : IAsyncDisposable
{
}
