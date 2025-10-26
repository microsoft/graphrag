using System.Collections.Generic;
using GraphRag.Vectors;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Vectors;

public sealed class VectorSearchResultTests
{
    [Fact]
    public void VectorSearchResult_EqualityUsesValues()
    {
        var metadata = new Dictionary<string, object?> { ["source"] = "document" };
        var first = new VectorSearchResult("id", 0.9, metadata);
        var second = new VectorSearchResult("id", 0.9, metadata);

        Assert.Equal(first, second);
        Assert.Equal("document", first.Metadata["source"]);
    }
}
