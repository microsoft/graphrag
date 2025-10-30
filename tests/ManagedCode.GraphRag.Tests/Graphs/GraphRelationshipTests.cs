using GraphRag.Graphs;

namespace ManagedCode.GraphRag.Tests.Graphs;

public sealed class GraphRelationshipTests
{
    [Fact]
    public void GraphRelationship_StoresProperties()
    {
        var properties = new Dictionary<string, object?> { ["weight"] = 0.9 };
        var relationship = new GraphRelationship("source", "target", "RELATES", properties);

        Assert.Equal("source", relationship.SourceId);
        Assert.Equal("target", relationship.TargetId);
        Assert.Equal("RELATES", relationship.Type);
        Assert.Equal(0.9, relationship.Properties["weight"]);
    }
}
