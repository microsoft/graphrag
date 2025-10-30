using System.Collections.ObjectModel;

namespace GraphRag.Vectors;

/// <summary>
/// Represents a vector store match with associated metadata.
/// </summary>
public sealed class VectorSearchResult(string id, double score, IReadOnlyDictionary<string, object?>? metadata = null)
{
    private static readonly IReadOnlyDictionary<string, object?> EmptyMetadata =
        new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>());

    public string Id { get; } = id ?? throw new ArgumentNullException(nameof(id));

    public double Score { get; } = score;

    public IReadOnlyDictionary<string, object?> Metadata { get; } = metadata ?? EmptyMetadata;

    public override bool Equals(object? obj)
    {
        if (ReferenceEquals(this, obj))
        {
            return true;
        }

        if (obj is not VectorSearchResult other)
        {
            return false;
        }

        return string.Equals(Id, other.Id, StringComparison.Ordinal) &&
               Score.Equals(other.Score) &&
               DictionaryEquals(Metadata, other.Metadata);
    }

    public override int GetHashCode()
    {
        var hash = new HashCode();
        hash.Add(Id, StringComparer.Ordinal);
        hash.Add(Score);
        foreach (var pair in Metadata.OrderBy(static kvp => kvp.Key, StringComparer.Ordinal))
        {
            hash.Add(pair.Key, StringComparer.Ordinal);
            hash.Add(pair.Value);
        }

        return hash.ToHashCode();
    }

    private static bool DictionaryEquals(IReadOnlyDictionary<string, object?> first, IReadOnlyDictionary<string, object?> second)
    {
        if (ReferenceEquals(first, second))
        {
            return true;
        }

        if (first.Count != second.Count)
        {
            return false;
        }

        foreach (var pair in first)
        {
            if (!second.TryGetValue(pair.Key, out var value))
            {
                return false;
            }

            if (!Equals(pair.Value, value))
            {
                return false;
            }
        }

        return true;
    }
}
