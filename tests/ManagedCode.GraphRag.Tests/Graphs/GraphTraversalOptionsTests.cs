using GraphRag.Graphs;

namespace ManagedCode.GraphRag.Tests.Graphs;

public sealed class GraphTraversalOptionsTests
{
    [Fact]
    public void Validate_AllowsPositiveValues()
    {
        var options = new GraphTraversalOptions { Skip = 5, Take = 10 };
        options.Validate();
    }

    [Fact]
    public void Validate_ThrowsForNegativeSkip()
    {
        var options = new GraphTraversalOptions { Skip = -1 };
        Assert.Throws<ArgumentOutOfRangeException>(() => options.Validate());
    }

    [Fact]
    public void Validate_ThrowsForNegativeTake()
    {
        var options = new GraphTraversalOptions { Take = -5 };
        Assert.Throws<ArgumentOutOfRangeException>(() => options.Validate());
    }
}
