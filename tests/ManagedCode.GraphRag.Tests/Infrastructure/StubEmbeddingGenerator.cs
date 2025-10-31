using Microsoft.Extensions.AI;

namespace ManagedCode.GraphRag.Tests.Infrastructure;

internal sealed class StubEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly Dictionary<string, float[]> _vectors;
    private readonly float[] _fallback;

    public StubEmbeddingGenerator(IDictionary<string, float[]>? vectors = null)
    {
        _vectors = vectors is null
            ? new Dictionary<string, float[]>(StringComparer.OrdinalIgnoreCase)
            : new Dictionary<string, float[]>(vectors, StringComparer.OrdinalIgnoreCase);

        _fallback = _vectors.Values.FirstOrDefault() ?? new[] { 0.5f, 0.5f, 0.5f };
    }

    public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(
        IEnumerable<string> values,
        EmbeddingGenerationOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(values);

        var embeddings = new List<Embedding<float>>();

        foreach (var value in values)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var vector = ResolveVector(value);
            embeddings.Add(new Embedding<float>(new ReadOnlyMemory<float>(vector)));
        }

        return Task.FromResult(new GeneratedEmbeddings<Embedding<float>>(embeddings));
    }

    public object? GetService(Type serviceType, object? serviceKey = null) => null;

    public void Dispose()
    {
    }

    private float[] ResolveVector(string? value)
    {
        if (!string.IsNullOrWhiteSpace(value) && _vectors.TryGetValue(value, out var vector))
        {
            return vector;
        }

        return _fallback;
    }
}
