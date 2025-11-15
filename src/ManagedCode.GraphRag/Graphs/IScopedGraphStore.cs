namespace GraphRag.Graphs;

public interface IGraphStoreScope : IAsyncDisposable
{
}

public interface IScopedGraphStore
{
    ValueTask<IGraphStoreScope> CreateScopeAsync(CancellationToken cancellationToken = default);
}
