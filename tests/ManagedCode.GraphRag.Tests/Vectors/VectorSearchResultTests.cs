using GraphRag.Vectors;

namespace ManagedCode.GraphRag.Tests.Vectors;

public sealed class VectorSearchResultTests
{
    [Fact]
    public void Equals_ComparesMetadata()
    {
        var metadata = new Dictionary<string, object?> { ["chunk"] = 1, ["label"] = "alpha" };
        var first = new VectorSearchResult("id", 0.9, metadata);
        var second = new VectorSearchResult("id", 0.9, new Dictionary<string, object?>(metadata));

        Assert.Equal(first, second);
        Assert.Equal(first.GetHashCode(), second.GetHashCode());
    }

    [Fact]
    public void Equals_ReturnsFalseForDifferentIds()
    {
        var first = new VectorSearchResult("id-a", 0.9);
        var second = new VectorSearchResult("id-b", 0.9);

        Assert.NotEqual(first, second);
        Assert.NotEqual(first.GetHashCode(), second.GetHashCode());
    }
}
