namespace GraphRag.Vectors;

public interface IVectorStore
{
    Task UpsertAsync(string collection, ReadOnlyMemory<float> embedding, IReadOnlyDictionary<string, object?> metadata, CancellationToken cancellationToken = default);

    IAsyncEnumerable<VectorSearchResult> SearchAsync(string collection, ReadOnlyMemory<float> embedding, int limit, CancellationToken cancellationToken = default);
}

public sealed record VectorSearchResult(string Id, double Score, IReadOnlyDictionary<string, object?> Metadata);
